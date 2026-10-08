"""SHAP explainability engine providing global and individual patient risk factor breakdowns."""

from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import pandas as pd
import shap

from nutri.config import MODEL_DIR
from nutri.features.obesity_features import ALL_FEATURE_COLUMNS, FOUR_TIER_NAMES
from nutri.logging import setup_logger

logger = setup_logger(__name__)

# Feature human-readable translations
FEATURE_TRANSLATIONS: Dict[str, str] = {
    "Age": "Age",
    "FCVC": "Vegetable Consumption",
    "NCP": "Number of Daily Meals",
    "CH2O": "Daily Water Hydration",
    "FAF": "Physical Activity Frequency",
    "TUE": "Screen / Technology Time",
    "Gender": "Gender",
    "family_history_with_overweight": "Family History of Overweight",
    "FAVC": "High-Calorie Food Intake",
    "CAEC": "Snacking Between Meals",
    "SMOKE": "Smoking Habit",
    "SCC": "Calorie Monitoring",
    "CALC": "Alcohol Consumption",
    "MTRANS": "Primary Transportation Mode",
}


class RiskExplainer:
    """SHAP explainer for obesity lifestyle risk predictions."""

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or MODEL_DIR
        self.uncalibrated_path = self.model_dir / "obesity_risk_uncalibrated.joblib"
        self._explainer = None
        self._pipeline = None
        self._feature_names = None

    def _lazy_init(self) -> None:
        if self._explainer is None:
            if not self.uncalibrated_path.exists():
                raise FileNotFoundError(
                    f"Model artifact not found at {self.uncalibrated_path}. Run training first."
                )
            self._pipeline = joblib.load(self.uncalibrated_path)
            preprocessor = self._pipeline.named_steps["prep"]
            clf = self._pipeline.named_steps["clf"]

            # Extract transformed feature names
            cat_encoder = preprocessor.named_transformers_["cat"]
            cat_cols = list(cat_encoder.get_feature_names_out(preprocessor.transformers[1][2]))
            num_cols = list(preprocessor.transformers[0][2])
            self._feature_names = num_cols + cat_cols

            self._explainer = shap.TreeExplainer(clf)

    def explain_instance(
        self,
        input_df: pd.DataFrame,
        predicted_tier: str,
    ) -> Dict[str, Any]:
        """Generate top 3 risk drivers and top 3 protective factors in plain language."""
        self._lazy_init()
        preprocessor = self._pipeline.named_steps["prep"]
        X_trans = preprocessor.transform(input_df)

        # Compute SHAP values for sample
        shap_values = self._explainer.shap_values(X_trans)

        # Handle multiclass shap values format
        class_idx = (
            FOUR_TIER_NAMES.index(predicted_tier) if predicted_tier in FOUR_TIER_NAMES else 1
        )
        if isinstance(shap_values, list):
            vals = shap_values[class_idx][0]
        elif len(shap_values.shape) == 3:
            vals = shap_values[0, :, class_idx]
        else:
            vals = shap_values[0]

        # Aggregate one-hot encoded features back to original feature groups
        feature_impacts: Dict[str, float] = dict.fromkeys(ALL_FEATURE_COLUMNS, 0.0)
        for idx, trans_name in enumerate(self._feature_names):
            val = float(vals[idx])
            for orig_col in ALL_FEATURE_COLUMNS:
                if trans_name.startswith(f"{orig_col}_") or trans_name == orig_col:
                    feature_impacts[orig_col] += val
                    break

        # Separate risk-raising (>0) and risk-lowering (<0)
        sorted_factors = sorted(feature_impacts.items(), key=lambda item: item[1], reverse=True)

        top_risk_drivers = []
        for feat, impact in sorted_factors:
            if impact > 0.01:
                explanation = self._format_factor_text(feat, input_df.iloc[0][feat], is_risk=True)
                top_risk_drivers.append(explanation)
            if len(top_risk_drivers) >= 3:
                break

        top_protective = []
        for feat, impact in reversed(sorted_factors):
            if impact < -0.01:
                explanation = self._format_factor_text(feat, input_df.iloc[0][feat], is_risk=False)
                top_protective.append(explanation)
            if len(top_protective) >= 3:
                break

        # Fallbacks if lifestyle features are completely neutral
        if not top_risk_drivers:
            top_risk_drivers.append(
                "Balanced baseline habits without severe elevated risk markers."
            )
        if not top_protective:
            top_protective.append("Consistent daily routine supporting baseline health.")

        return {
            "top_risk_drivers": top_risk_drivers,
            "top_protective_factors": top_protective,
            "raw_feature_impacts": {k: round(v, 3) for k, v in feature_impacts.items()},
        }

    def _format_factor_text(self, feat: str, val: Any, is_risk: bool) -> str:
        """Render clinically explainable user-friendly descriptions."""
        if feat == "family_history_with_overweight":
            return (
                "Family history of overweight elevates metabolic risk predisposition."
                if is_risk
                else "No reported familial overweight history provides a genetic baseline."
            )
        if feat == "FAVC":
            return (
                "Frequent consumption of high-calorie foods is a primary driver."
                if is_risk
                else "Low consumption of energy-dense fried/fast foods helps protect against excess weight."
            )
        if feat == "FAF":
            return (
                f"Low physical exercise frequency ({val:.1f} days/wk) contributes to sedentary exposure."
                if is_risk
                else f"Regular physical activity ({val:.1f} days/wk) is a strong protective habit."
            )
        if feat == "FCVC":
            return (
                "Low vegetable consumption (< 2 daily servings) reduces dietary fiber satiety."
                if is_risk
                else "Frequent vegetable consumption (3 servings/day) promotes satiety and metabolic regulation."
            )
        if feat == "CAEC":
            return (
                f"Frequent snacking between meals ('{val}') increases daily surplus risk."
                if is_risk
                else "Controlled snacking between meals prevents caloric accumulation."
            )
        if feat == "CH2O":
            return (
                "Low daily water consumption (< 1-2 L) can affect metabolic regulation."
                if is_risk
                else "Healthy daily water hydration supports satiety and metabolic health."
            )
        if feat == "SCC":
            return (
                "Lack of calorie awareness or nutritional monitoring."
                if is_risk
                else "Active monitoring of calories and portions serves as a strong regulating habit."
            )
        if feat == "TUE":
            return (
                f"High screen time ({val:.1f} hrs/day) correlates with prolonged sedentary behavior."
                if is_risk
                else "Moderate screen time limits sedentary exposure."
            )
        if feat == "MTRANS":
            return (
                f"Reliance on motorized transit ('{val}') reduces non-exercise activity."
                if is_risk
                else f"Active transit mode ('{val}') increases daily non-exercise physical activity."
            )

        return f"{FEATURE_TRANSLATIONS.get(feat, feat)}: recorded value '{val}'."
