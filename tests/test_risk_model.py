"""Unit and regression tests for obesity risk ML model, pipeline, and explainability."""

import json

import pytest

from nutri.config import MODEL_METRICS_PATH, MODEL_PATH
from nutri.features.obesity_features import FOUR_TIER_NAMES, validate_risk_features
from nutri.models.predict import get_risk_pipeline, predict_obesity_risk


@pytest.fixture
def valid_habits():
    """Sample valid habits survey payload."""
    return {
        "Gender": "Male",
        "Age": 26.0,
        "family_history_with_overweight": "yes",
        "FAVC": "yes",
        "FCVC": 2.0,
        "NCP": 3.0,
        "CAEC": "Sometimes",
        "SMOKE": "no",
        "CH2O": 2.0,
        "SCC": "no",
        "FAF": 1.0,
        "TUE": 1.0,
        "CALC": "Sometimes",
        "MTRANS": "Public_Transportation",
    }


def test_model_artifact_exists_and_loads():
    """Verify that persisted pipeline exists and loads correctly."""
    assert MODEL_PATH.exists(), "obesity_risk_pipeline.joblib must exist."
    pipeline = get_risk_pipeline()
    assert hasattr(pipeline, "predict")
    assert hasattr(pipeline, "predict_proba")


def test_predict_obesity_risk_structure_and_probabilities(valid_habits):
    """Verify prediction format, classes, and probability sum constraint."""
    res = predict_obesity_risk(valid_habits)
    assert res["risk_tier"] in FOUR_TIER_NAMES
    probs = res["probabilities"]
    assert len(probs) == len(FOUR_TIER_NAMES)

    # Probabilities must sum strictly to 1.0
    total_prob = sum(probs.values())
    assert abs(total_prob - 1.0) < 0.001

    # Explanations generated
    assert len(res["top_risk_drivers"]) >= 1
    assert len(res["top_protective_factors"]) >= 1
    assert "EDUCATIONAL" in res["disclaimer"]


def test_input_validation_rejections():
    """Verify schema validator catches invalid or missing fields."""
    # Age out of bounds
    with pytest.raises(ValueError, match="Age out of plausible range"):
        validate_risk_features(
            {"Age": 150.0, "FCVC": 2.0, "NCP": 3.0, "CH2O": 2.0, "FAF": 1.0, "TUE": 1.0}
        )

    # Missing required field
    with pytest.raises(ValueError, match="Missing required numeric feature"):
        validate_risk_features({"Age": 25.0})


def test_model_metric_floors():
    """Verify empirical metric floors from training artifacts."""
    assert MODEL_METRICS_PATH.exists(), "model_metrics.json must exist."
    with open(MODEL_METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # 5-fold CV Macro-F1 floor (> 0.70)
    cv_f1 = metrics["candidate_cv_benchmarks"]["LightGBM"]["cv_macro_f1_mean"]
    assert cv_f1 >= 0.75, f"LightGBM CV Macro-F1 was {cv_f1}, expected >= 0.75"

    # Synthetic test accuracy floor (> 0.85)
    synth_acc = metrics["synthetic_test_evaluation"]["accuracy"]
    assert synth_acc >= 0.85, f"Synthetic test accuracy was {synth_acc}, expected >= 0.85"

    # Real holdout accuracy floor (> 0.50)
    real_acc = metrics["likely_original_holdout_evaluation"]["accuracy"]
    assert real_acc >= 0.50, f"Real holdout accuracy was {real_acc}, expected >= 0.50"
