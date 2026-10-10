"""Lifestyle risk model inference router with SHAP explanations and medical disclaimers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from api.schemas import RiskRequest, RiskResponse
from nutri.models.predict import predict_obesity_risk

router = APIRouter(prefix="/risk", tags=["Risk Screening"])


@router.post("", response_model=RiskResponse)
def screen_lifestyle_risk(
    payload: RiskRequest,
    current_user: dict = Depends(get_current_user),
) -> RiskResponse:
    """Predict lifestyle obesity risk tier, calibrated probabilities, and SHAP drivers.

    Note: Anthropometric measurements (Height, Weight, BMI) are strictly excluded
    to screen lifestyle behavioral risk rather than regurgitate current body size.
    """
    try:
        user_habits = payload.model_dump()
        result = predict_obesity_risk(user_habits, include_explanations=True)

        return RiskResponse(
            predicted_category=result["risk_tier"],
            probabilities=result["probabilities"],
            risk_tier=result["risk_tier"],
            top_risk_factors=result["top_risk_drivers"],
            top_protective_factors=result["top_protective_factors"],
            model_version="1.0.0-calibrated-lgbm",
            disclaimer=result["disclaimer"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Risk model screening error: {str(e)}") from e
