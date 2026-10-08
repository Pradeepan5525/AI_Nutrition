"""Inference wrapper for obesity risk assessment with schema validation and explainability."""

from typing import Any, Dict

import joblib
import numpy as np

from nutri.config import MODEL_PATH
from nutri.features.obesity_features import FOUR_TIER_NAMES, validate_risk_features
from nutri.models.explain import RiskExplainer
from nutri.rules.safety import DISCLAIMER_TEXT

# Cached global instances
_PIPELINE = None
_EXPLAINER = None


def get_risk_pipeline():
    """Retrieve or lazily load the production calibrated risk pipeline."""
    global _PIPELINE
    if _PIPELINE is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {MODEL_PATH}. Run 'python scripts/train.py' first."
            )
        _PIPELINE = joblib.load(MODEL_PATH)
    return _PIPELINE


def get_explainer() -> RiskExplainer:
    """Retrieve or lazily load the SHAP risk explainer."""
    global _EXPLAINER
    if _EXPLAINER is None:
        _EXPLAINER = RiskExplainer()
    return _EXPLAINER


def predict_obesity_risk(
    user_habits: Dict[str, Any], include_explanations: bool = True
) -> Dict[str, Any]:
    """Validate habits input, predict risk tier and probabilities, and generate SHAP factors.

    Args:
        user_habits: Dict containing demographic and lifestyle habit features.
        include_explanations: Whether to generate SHAP top risk factors.

    Returns:
        Structured prediction result with tier, calibrated probabilities, and drivers.
    """
    # 1. Schema and range validation
    input_df = validate_risk_features(user_habits)

    # 2. Predict calibrated probabilities
    pipeline = get_risk_pipeline()
    proba_raw = pipeline.predict_proba(input_df)[0]

    # Normalize to ensure sum is strictly 1.0
    proba_sum = float(np.sum(proba_raw))
    proba_norm = (proba_raw / proba_sum) if proba_sum > 0 else proba_raw

    # Map to class labels
    classes = list(pipeline.classes_)
    prob_dict = {
        cls: round(float(proba_norm[classes.index(cls)]), 4)
        for cls in FOUR_TIER_NAMES
        if cls in classes
    }

    predicted_tier = str(pipeline.predict(input_df)[0])

    # 3. Explanations
    top_risk_drivers = []
    top_protective = []
    if include_explanations:
        try:
            explainer = get_explainer()
            exp_res = explainer.explain_instance(input_df, predicted_tier)
            top_risk_drivers = exp_res["top_risk_drivers"]
            top_protective = exp_res["top_protective_factors"]
        except Exception:
            top_risk_drivers = ["Explanation unavailable for this input profile."]

    return {
        "risk_tier": predicted_tier,
        "probabilities": prob_dict,
        "top_risk_drivers": top_risk_drivers,
        "top_protective_factors": top_protective,
        "disclaimer": DISCLAIMER_TEXT,
    }
