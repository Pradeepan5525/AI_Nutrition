"""Training, hyperparameter tuning, calibration, and benchmarking for obesity risk model."""

import json
from typing import Any, Dict, List, Tuple

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize

from nutri.config import (
    MODEL_DIR,
    MODEL_METRICS_PATH,
    MODEL_PATH,
    RAW_OBESITY_CSV,
    SEED,
)
from nutri.features.obesity_features import (
    ALL_FEATURE_COLUMNS,
    FOUR_TIER_MAPPING,
    FOUR_TIER_NAMES,
    build_preprocessor,
    extract_likely_original_mask,
)
from nutri.logging import setup_logger

logger = setup_logger(__name__)


def compute_multiclass_brier_score(
    y_true_indices: np.ndarray, y_proba: np.ndarray, n_classes: int
) -> float:
    """Compute multiclass Brier score (mean squared error of predicted probabilities)."""
    y_one_hot = label_binarize(y_true_indices, classes=list(range(n_classes)))
    if y_one_hot.shape[1] == 1 and n_classes == 2:
        y_one_hot = np.hstack([1 - y_one_hot, y_one_hot])
    mse = np.mean(np.sum((y_proba - y_one_hot) ** 2, axis=1))
    return float(round(mse, 4))


def prepare_datasets() -> Tuple[
    pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series
]:
    """Load, deduplicate, and partition obesity data into train, synthetic test, and real holdout.

    Design rationale (docs/DECISIONS.md):
    All 'Healthy' (Normal_Weight) rows in the dataset are original survey responses (0 synthetic
    rows were generated for Normal_Weight). To enable 4-class training while preserving a strictly
    unseen held-out realism benchmark, we split likely_original into a train split (50%) and a held-out
    test split (50%). The held-out realism split is NEVER trained on.
    """
    raw_df = pd.read_csv(RAW_OBESITY_CSV)
    deduped_df = raw_df.drop_duplicates().copy()
    logger.info(
        "Loaded raw obesity data: %d rows. After deduplication: %d rows",
        len(raw_df),
        len(deduped_df),
    )

    # Construct 4-tier target
    deduped_df["target_4tier"] = deduped_df["NObeyesdad"].map(FOUR_TIER_MAPPING)

    # Identify likely original (real human) responses
    likely_orig_mask = extract_likely_original_mask(deduped_df)
    real_df = deduped_df[likely_orig_mask].copy()
    synth_df = deduped_df[~likely_orig_mask].copy()

    # Split real rows into train and strictly held-out test
    real_train, real_test = train_test_split(
        real_df, test_size=0.50, random_state=SEED, stratify=real_df["target_4tier"]
    )
    # Split synthetic rows into train and test
    synth_train, synth_test = train_test_split(
        synth_df, test_size=0.20, random_state=SEED, stratify=synth_df["target_4tier"]
    )

    # Combined training set
    train_df = pd.concat([real_train, synth_train], ignore_index=True)

    X_train = train_df[ALL_FEATURE_COLUMNS]
    y_train = train_df["target_4tier"]

    X_test_synth = synth_test[ALL_FEATURE_COLUMNS]
    y_test_synth = synth_test["target_4tier"]

    X_real_holdout = real_test[ALL_FEATURE_COLUMNS]
    y_real_holdout = real_test["target_4tier"]

    logger.info(
        "Splits created: Train = %d, Synthetic Test = %d, Real Holdout = %d",
        len(X_train),
        len(X_test_synth),
        len(X_real_holdout),
    )

    return X_train, y_train, X_test_synth, y_test_synth, X_real_holdout, y_real_holdout


def evaluate_model(
    pipeline: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    class_names: List[str] = FOUR_TIER_NAMES,
) -> Dict[str, Any]:
    """Compute comprehensive performance metrics for a model pipeline."""
    y_pred = pipeline.predict(X_test)
    y_proba_raw = pipeline.predict_proba(X_test)

    # Align probabilities to class_names order
    model_classes = list(pipeline.classes_)
    aligned_proba = np.zeros((len(X_test), len(class_names)))
    for col_idx, cls in enumerate(class_names):
        if cls in model_classes:
            aligned_proba[:, col_idx] = y_proba_raw[:, model_classes.index(cls)]

    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    # Map classes to indices for Brier score
    class_to_idx = {c: i for i, c in enumerate(class_names)}
    y_true_idx = np.array([class_to_idx[y] for y in y_test])
    brier = compute_multiclass_brier_score(y_true_idx, aligned_proba, len(class_names))

    # Per-class recall
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    per_class_recall = {
        cls: round(report.get(cls, {}).get("recall", 0.0), 3) for cls in class_names
    }

    cm = confusion_matrix(y_test, y_pred, labels=class_names).tolist()

    return {
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "brier_score": brier,
        "per_class_recall": per_class_recall,
        "confusion_matrix": cm,
    }


def run_cross_validation_benchmark(
    X_train: pd.DataFrame, y_train: pd.Series
) -> Dict[str, Dict[str, float]]:
    """Run stratified 5-fold cross validation across candidate models."""
    logger.info("Executing 5-fold cross-validation comparison...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=SEED),
        "RandomForest": RandomForestClassifier(n_estimators=150, max_depth=10, random_state=SEED),
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=150, learning_rate=0.05, num_leaves=31, random_state=SEED, verbose=-1
        ),
    }

    cv_results = {}

    for name, clf in models.items():
        preprocessor = build_preprocessor()
        pipe = Pipeline([("prep", preprocessor), ("clf", clf)])

        acc_scores = []
        f1_scores = []

        for train_idx, val_idx in skf.split(X_train, y_train):
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

            pipe.fit(X_tr, y_tr)
            preds = pipe.predict(X_val)
            acc_scores.append(accuracy_score(y_val, preds))
            f1_scores.append(f1_score(y_val, preds, average="macro"))

        cv_results[name] = {
            "cv_accuracy_mean": round(float(np.mean(acc_scores)), 4),
            "cv_accuracy_std": round(float(np.std(acc_scores)), 4),
            "cv_macro_f1_mean": round(float(np.mean(f1_scores)), 4),
            "cv_macro_f1_std": round(float(np.std(f1_scores)), 4),
        }
        logger.info(
            "%s -> CV Macro-F1: %.4f (+/- %.4f)",
            name,
            cv_results[name]["cv_macro_f1_mean"],
            cv_results[name]["cv_macro_f1_std"],
        )

    return cv_results


def run_fairness_audit(pipeline: Any, X_eval: pd.DataFrame, y_eval: pd.Series) -> Dict[str, Any]:
    """Audit model predictions across demographic subgroups (Gender and Age bands)."""
    df_eval = X_eval.copy()
    df_eval["y_true"] = y_eval.values
    df_eval["y_pred"] = pipeline.predict(X_eval)

    # 1. Gender breakdown
    gender_metrics = {}
    for g in df_eval["Gender"].unique():
        sub = df_eval[df_eval["Gender"] == g]
        acc = accuracy_score(sub["y_true"], sub["y_pred"])
        f1 = f1_score(sub["y_true"], sub["y_pred"], average="macro", zero_division=0)
        gender_metrics[str(g)] = {
            "count": len(sub),
            "accuracy": round(float(acc), 4),
            "macro_f1": round(float(f1), 4),
        }

    # 2. Age group breakdown
    def age_band(age):
        if age < 25:
            return "< 25"
        if age <= 40:
            return "25 - 40"
        return "> 40"

    df_eval["age_band"] = df_eval["Age"].apply(age_band)
    age_metrics = {}
    for ab in ["< 25", "25 - 40", "> 40"]:
        sub = df_eval[df_eval["age_band"] == ab]
        if len(sub) > 0:
            acc = accuracy_score(sub["y_true"], sub["y_pred"])
            f1 = f1_score(sub["y_true"], sub["y_pred"], average="macro", zero_division=0)
            age_metrics[ab] = {
                "count": len(sub),
                "accuracy": round(float(acc), 4),
                "macro_f1": round(float(f1), 4),
            }

    return {
        "by_gender": gender_metrics,
        "by_age_band": age_metrics,
    }


def train_and_persist_risk_model() -> Dict[str, Any]:
    """Execute complete risk model training, calibration, fairness audit, and artifact export."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    X_train, y_train, X_test_synth, y_test_synth, X_real_holdout, y_real_holdout = (
        prepare_datasets()
    )

    # 1. Cross Validation Benchmarking
    cv_benchmark = run_cross_validation_benchmark(X_train, y_train)

    # 2. Fit base LightGBM with preprocessing
    preprocessor = build_preprocessor()
    base_lgbm = lgb.LGBMClassifier(
        n_estimators=180,
        learning_rate=0.04,
        num_leaves=31,
        min_child_samples=20,
        random_state=SEED,
        verbose=-1,
    )
    raw_pipeline = Pipeline([("prep", preprocessor), ("clf", base_lgbm)])
    raw_pipeline.fit(X_train, y_train)

    # 3. Fit Calibrated Model (Sigmoid / Platt scaling via 5-fold internal CV)
    logger.info("Fitting calibrated LightGBM pipeline...")
    # Pre-transform training data for calibrated classifier
    X_train_trans = preprocessor.fit_transform(X_train)
    calibrated_clf = CalibratedClassifierCV(estimator=base_lgbm, method="sigmoid", cv=5)
    calibrated_clf.fit(X_train_trans, y_train)

    final_pipeline = Pipeline(
        [
            ("prep", preprocessor),
            ("clf", calibrated_clf),
        ]
    )

    # 4. Comprehensive Evaluation on both Synthetic Test Split and Real Holdout
    synth_metrics = evaluate_model(final_pipeline, X_test_synth, y_test_synth)
    real_metrics = evaluate_model(final_pipeline, X_real_holdout, y_real_holdout)

    logger.info("=== EVALUATION RESULTS ===")
    logger.info(
        "Synthetic Test Split -> Accuracy: %.4f | Macro-F1: %.4f | Brier: %.4f",
        synth_metrics["accuracy"],
        synth_metrics["macro_f1"],
        synth_metrics["brier_score"],
    )
    logger.info(
        "Likely Original Holdout -> Accuracy: %.4f | Macro-F1: %.4f | Brier: %.4f",
        real_metrics["accuracy"],
        real_metrics["macro_f1"],
        real_metrics["brier_score"],
    )

    # 5. Demographic Fairness Audit
    fairness_results = run_fairness_audit(final_pipeline, X_real_holdout, y_real_holdout)

    # 6. Save Pipeline Artifacts
    joblib.dump(final_pipeline, MODEL_PATH)
    logger.info("Persisted production pipeline to %s", MODEL_PATH)

    # Save raw uncalibrated pipeline too (for TreeExplainer)
    uncalibrated_path = MODEL_DIR / "obesity_risk_uncalibrated.joblib"
    joblib.dump(raw_pipeline, uncalibrated_path)

    # Compile comprehensive metrics payload
    metrics_payload = {
        "candidate_cv_benchmarks": cv_benchmark,
        "synthetic_test_evaluation": synth_metrics,
        "likely_original_holdout_evaluation": real_metrics,
        "fairness_audit_on_real_holdout": fairness_results,
        "training_metadata": {
            "n_train_samples": len(X_train),
            "n_synthetic_test_samples": len(X_test_synth),
            "n_real_holdout_samples": len(X_real_holdout),
            "seed": SEED,
            "classes": FOUR_TIER_NAMES,
        },
    }

    with open(MODEL_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    logger.info("Saved model metrics to %s", MODEL_METRICS_PATH)

    return metrics_payload


if __name__ == "__main__":
    train_and_persist_risk_model()
