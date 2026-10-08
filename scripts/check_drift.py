"""Data and Prediction Drift Monitoring Pipeline.

Calculates Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests
between baseline training feature distributions and operational inference requests.
Generates structured JSON and Markdown telemetry reports.
"""

from __future__ import annotations

import json
from typing import Any, Dict

import numpy as np
import pandas as pd
from scipy import stats

from nutri.config import RAW_OBESITY_CSV, REPORTS_DIR, SEED
from nutri.features.obesity_features import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from nutri.logging import setup_logger
from nutri.models.predict import get_risk_pipeline

logger = setup_logger(__name__)


def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_buckets: int = 10) -> float:
    """Calculate Population Stability Index (PSI) for continuous numeric feature distributions.

    Standard Interpretation:
    - PSI < 0.10: No significant distribution change (Stable).
    - 0.10 <= PSI < 0.25: Moderate distribution shift (Warning).
    - PSI >= 0.25: Significant distribution shift (Action required / Retraining alert).
    """
    # Guard against empty or constant arrays
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine quantile bin edges based on expected baseline
    quantiles = np.linspace(0, 100, num_buckets + 1)
    bin_edges = np.percentile(expected, quantiles)
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf
    # Ensure strictly increasing bins by adding tiny jitter if ties exist
    for i in range(1, len(bin_edges)):
        if bin_edges[i] <= bin_edges[i - 1]:
            bin_edges[i] = bin_edges[i - 1] + 1e-5

    # Compute frequency counts
    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    # Convert to fractions with Laplace smoothing (avoid divide-by-zero)
    eps = 1e-4
    expected_pct = (expected_counts + eps) / (len(expected) + eps * num_buckets)
    actual_pct = (actual_counts + eps) / (len(actual) + eps * num_buckets)

    # Calculate PSI sum
    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(round(psi_val, 4))


def calculate_categorical_psi(expected_series: pd.Series, actual_series: pd.Series) -> float:
    """Calculate PSI across discrete categories."""
    categories = list(set(expected_series.unique()).union(set(actual_series.unique())))
    eps = 1e-4
    num_cats = len(categories)

    exp_counts = expected_series.value_counts()
    act_counts = actual_series.value_counts()

    exp_total = len(expected_series)
    act_total = len(actual_series)

    psi_total = 0.0
    for cat in categories:
        exp_pct = (exp_counts.get(cat, 0) + eps) / (exp_total + eps * num_cats)
        act_pct = (act_counts.get(cat, 0) + eps) / (act_total + eps * num_cats)
        psi_total += (act_pct - exp_pct) * np.log(act_pct / exp_pct)

    return float(round(psi_total, 4))


def run_drift_check(baseline_df: pd.DataFrame, production_df: pd.DataFrame) -> Dict[str, Any]:
    """Execute complete drift audit across features and predictions."""
    report = {
        "baseline_sample_size": len(baseline_df),
        "production_sample_size": len(production_df),
        "feature_drift": {},
        "prediction_drift": {},
        "summary": {
            "total_features_evaluated": len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES),
            "features_with_moderate_drift": 0,
            "features_with_severe_drift": 0,
            "overall_system_status": "STABLE",
        },
    }

    # 1. Numeric Feature Drift (PSI + KS-Test)
    for col in NUMERIC_FEATURES:
        b_vals = baseline_df[col].dropna().to_numpy()
        p_vals = production_df[col].dropna().to_numpy()

        psi_val = calculate_psi(b_vals, p_vals)
        ks_res = stats.ks_2samp(b_vals, p_vals)

        status_str = "STABLE"
        if psi_val >= 0.25:
            status_str = "SEVERE_DRIFT"
            report["summary"]["features_with_severe_drift"] += 1
        elif psi_val >= 0.10:
            status_str = "MODERATE_DRIFT"
            report["summary"]["features_with_moderate_drift"] += 1

        report["feature_drift"][col] = {
            "type": "numeric",
            "psi": psi_val,
            "ks_statistic": round(float(ks_res.statistic), 4),
            "ks_pvalue": round(float(ks_res.pvalue), 4),
            "status": status_str,
        }

    # 2. Categorical Feature Drift (PSI)
    for col in CATEGORICAL_FEATURES:
        b_ser = baseline_df[col].dropna().astype(str)
        p_ser = production_df[col].dropna().astype(str)

        psi_val = calculate_categorical_psi(b_ser, p_ser)
        status_str = "STABLE"
        if psi_val >= 0.25:
            status_str = "SEVERE_DRIFT"
            report["summary"]["features_with_severe_drift"] += 1
        elif psi_val >= 0.10:
            status_str = "MODERATE_DRIFT"
            report["summary"]["features_with_moderate_drift"] += 1

        report["feature_drift"][col] = {
            "type": "categorical",
            "psi": psi_val,
            "status": status_str,
        }

    # 3. Prediction Distribution Drift
    pipeline = get_risk_pipeline()
    b_preds = pd.Series(pipeline.predict(baseline_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]))
    p_preds = pd.Series(pipeline.predict(production_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]))

    pred_psi = calculate_categorical_psi(b_preds, p_preds)
    b_dist = b_preds.value_counts(normalize=True).round(3).to_dict()
    p_dist = p_preds.value_counts(normalize=True).round(3).to_dict()

    report["prediction_drift"] = {
        "prediction_psi": pred_psi,
        "baseline_class_distribution": b_dist,
        "production_class_distribution": p_dist,
        "status": "STABLE"
        if pred_psi < 0.10
        else ("MODERATE_DRIFT" if pred_psi < 0.25 else "SEVERE_DRIFT"),
    }

    # Overall Status
    if report["summary"]["features_with_severe_drift"] > 0 or pred_psi >= 0.25:
        report["summary"]["overall_system_status"] = "ACTION_REQUIRED"
    elif report["summary"]["features_with_moderate_drift"] > 0 or pred_psi >= 0.10:
        report["summary"]["overall_system_status"] = "WARNING_MONITOR"

    return report


def generate_drift_markdown(report: Dict[str, Any]) -> str:
    """Format drift findings into a clear markdown telemetry document."""
    lines = [
        "# Operational Telemetry: Data & Prediction Drift Report",
        "",
        f"- **Baseline Population Sample:** {report['baseline_sample_size']:,}",
        f"- **Inference Request Batch:** {report['production_sample_size']:,}",
        f"- **System Drift Status:** **`{report['summary']['overall_system_status']}`**",
        f"- **Features with Severe Drift (PSI ≥ 0.25):** {report['summary']['features_with_severe_drift']}",
        f"- **Features with Moderate Drift (0.10 ≤ PSI < 0.25):** {report['summary']['features_with_moderate_drift']}",
        "",
        "## Feature Distribution Stability (PSI & KS-Test)",
        "",
        "| Feature | Type | PSI | KS-Stat / P-Value | Drift Classification |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for feat, data in report["feature_drift"].items():
        ks_info = (
            f"{data['ks_statistic']} (p={data['ks_pvalue']})"
            if data["type"] == "numeric"
            else "N/A (discrete)"
        )
        status_badge = (
            "✅ Stable"
            if data["status"] == "STABLE"
            else ("⚠️ Warning" if data["status"] == "MODERATE_DRIFT" else "🚨 Severe")
        )
        lines.append(
            f"| `{feat}` | {data['type']} | {data['psi']:.4f} | {ks_info} | {status_badge} |"
        )

    lines.extend(
        [
            "",
            "## Output Prediction Distribution Shift",
            "",
            f"- **Prediction Drift PSI:** `{report['prediction_drift']['prediction_psi']:.4f}` ({report['prediction_drift']['status']})",
            "",
            "| Risk Tier | Baseline Share (%) | Operational Batch Share (%) | Shift (%) |",
            "| :--- | :--- | :--- | :--- |",
        ]
    )

    b_dist = report["prediction_drift"]["baseline_class_distribution"]
    p_dist = report["prediction_drift"]["production_class_distribution"]
    all_classes = sorted(set(b_dist.keys()).union(set(p_dist.keys())))

    for cls in all_classes:
        b_pct = b_dist.get(cls, 0.0) * 100
        p_pct = p_dist.get(cls, 0.0) * 100
        diff = p_pct - b_pct
        lines.append(f"| **{cls}** | {b_pct:.1f}% | {p_pct:.1f}% | {diff:+.1f}% |")

    lines.append("")
    lines.append(
        "> Standard threshold reference: PSI < 0.10 indicates stable distribution; PSI ≥ 0.25 triggers automated pipeline retraining alert."
    )
    return "\n".join(lines)


def main() -> None:
    """Run drift check script."""
    logger.info("Initiating data & prediction drift audit...")

    if not RAW_OBESITY_CSV.exists():
        raise FileNotFoundError(f"Obesity baseline raw dataset not found at {RAW_OBESITY_CSV}")

    baseline_df = pd.read_csv(RAW_OBESITY_CSV)

    # Simulate operational inference batch (sample with slight realistic demographic variance)
    np.random.seed(SEED)
    sample_indices = np.random.choice(
        len(baseline_df), size=min(400, len(baseline_df)), replace=False
    )
    prod_df = baseline_df.iloc[sample_indices].copy()

    # Introduce minor simulated age drift (+1.5 years on average) to test detector sensitivity
    prod_df["Age"] = np.clip(
        prod_df["Age"] + np.random.normal(1.2, 0.5, size=len(prod_df)), 12.0, 95.0
    )

    # Compute drift
    drift_report = run_drift_check(baseline_df, prod_df)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "drift_report.json"
    md_path = REPORTS_DIR / "drift_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(drift_report, f, indent=2)

    md_content = generate_drift_markdown(drift_report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info("Drift audit completed. Saved report to %s and %s", json_path, md_path)
    print(
        f"Drift Audit Complete. Overall Status: {drift_report['summary']['overall_system_status']}"
    )
    print(f"Prediction PSI: {drift_report['prediction_drift']['prediction_psi']:.4f}")


if __name__ == "__main__":
    main()
