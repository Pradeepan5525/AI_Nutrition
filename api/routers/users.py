"""User management router: profile, history, weight logs, goals/alerts, export, and deletion."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.schemas import (
    AssessmentRecord,
    DataExportResponse,
    GoalAlertItem,
    MealPlanRecord,
    NotificationItem,
    PasswordChangeRequest,
    RiskRecord,
    UserFullResponse,
    WeightLogItem,
)
from nutri.auth.security import hash_password, validate_password_strength, verify_password
from nutri.auth.user_service import (
    delete_user_account,
    export_user_data,
    format_user_dict,
    update_profile_for_user,
)
from nutri.database.engine import get_db
from nutri.database.models import (
    Assessment,
    GoalAlert,
    MealPlan,
    Notification,
    RiskResult,
    User,
    WeightLog,
)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/me", response_model=UserFullResponse)
def get_my_details(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserFullResponse:
    """Retrieve full user profile and account details."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserFullResponse(**format_user_dict(user))


@router.put("/me/profile", response_model=UserFullResponse)
def update_my_profile(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserFullResponse:
    """Update anthropometric, clinical, and dietary preferences for current user."""
    # Handle if profile is nested under "profile" key
    profile_data = payload.get("profile", payload)
    updated = update_profile_for_user(db, current_user["id"], profile_data)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update profile.")
    return UserFullResponse(**updated)


@router.put("/me/password")
def change_my_password(
    payload: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Change account password with verification of current password."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed.",
        )

    valid, err = validate_password_strength(payload.new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully."}


@router.get("/me/export", response_model=DataExportResponse)
def export_my_data(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataExportResponse:
    """Export all personal data, assessments, logs, and preferences."""
    export = export_user_data(db, current_user["id"])
    return DataExportResponse(**export)


@router.delete("/me")
def delete_my_account(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Permanently delete user account and all personal records."""
    success = delete_user_account(db, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="User account not found.")
    return {"message": "User account and all personal data permanently deleted."}


# ---------------------------------------------------------------------------
# Assessment History Endpoints
# ---------------------------------------------------------------------------
@router.get("/me/assessments", response_model=List[AssessmentRecord])
def list_my_assessments(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AssessmentRecord]:
    """List saved metabolic assessments for current user."""
    records = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user["id"])
        .order_by(Assessment.created_at.desc())
        .all()
    )
    result = []
    for r in records:
        result.append(
            AssessmentRecord(
                id=r.id,
                created_at=r.created_at.isoformat(),
                input_data=json.loads(r.input_data) if r.input_data else {},
                bmi=r.bmi,
                bmi_category=r.bmi_category,
                bmr_kcal=r.bmr_kcal,
                tdee_kcal=r.tdee_kcal,
                target_kcal=r.target_kcal,
                protein_g=r.protein_g,
                carbs_g=r.carbs_g,
                fat_g=r.fat_g,
                sodium_mg=r.sodium_mg,
                water_ml=r.water_ml,
                safety_cleared=r.safety_cleared,
                safety_flags=json.loads(r.safety_flags) if r.safety_flags else [],
                clinical_constraints=json.loads(r.clinical_constraints) if r.clinical_constraints else {},
            )
        )
    return result


@router.post("/me/assessments", response_model=AssessmentRecord)
def save_my_assessment(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentRecord:
    """Save an assessment to history."""
    item = Assessment(
        user_id=current_user["id"],
        created_at=datetime.utcnow(),
        input_data=json.dumps(payload.get("input_data", {})),
        bmi=float(payload.get("bmi", 0.0)),
        bmi_category=str(payload.get("bmi_category", "Normal")),
        bmr_kcal=float(payload.get("bmr_kcal", 0.0)),
        tdee_kcal=float(payload.get("tdee_kcal", 0.0)),
        target_kcal=float(payload.get("target_kcal", 0.0)),
        protein_g=float(payload.get("protein_g", 0.0)),
        carbs_g=float(payload.get("carbs_g", 0.0)),
        fat_g=float(payload.get("fat_g", 0.0)),
        sodium_mg=float(payload.get("sodium_mg", 0.0)),
        water_ml=float(payload.get("water_ml", 0.0)),
        safety_cleared=bool(payload.get("safety_cleared", True)),
        safety_flags=json.dumps(payload.get("safety_flags", [])),
        clinical_constraints=json.dumps(payload.get("clinical_constraints", {})),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return AssessmentRecord(
        id=item.id,
        created_at=item.created_at.isoformat(),
        input_data=json.loads(item.input_data),
        bmi=item.bmi,
        bmi_category=item.bmi_category,
        bmr_kcal=item.bmr_kcal,
        tdee_kcal=item.tdee_kcal,
        target_kcal=item.target_kcal,
        protein_g=item.protein_g,
        carbs_g=item.carbs_g,
        fat_g=item.fat_g,
        sodium_mg=item.sodium_mg,
        water_ml=item.water_ml,
        safety_cleared=item.safety_cleared,
        safety_flags=json.loads(item.safety_flags),
        clinical_constraints=json.loads(item.clinical_constraints),
    )


@router.delete("/me/assessments/{record_id}")
def delete_my_assessment(
    record_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a saved assessment record."""
    item = (
        db.query(Assessment)
        .filter(Assessment.id == record_id, Assessment.user_id == current_user["id"])
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Assessment record not found.")
    db.delete(item)
    db.commit()
    return {"message": "Assessment record deleted."}


# ---------------------------------------------------------------------------
# Risk Results Endpoints
# ---------------------------------------------------------------------------
@router.get("/me/risk-results", response_model=List[RiskRecord])
def list_my_risk_results(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RiskRecord]:
    """List lifestyle risk screening history."""
    records = (
        db.query(RiskResult)
        .filter(RiskResult.user_id == current_user["id"])
        .order_by(RiskResult.created_at.desc())
        .all()
    )
    return [
        RiskRecord(
            id=r.id,
            created_at=r.created_at.isoformat(),
            input_habits=json.loads(r.input_habits) if r.input_habits else {},
            predicted_tier=r.predicted_tier,
            confidence=r.confidence,
            probabilities=json.loads(r.probabilities) if r.probabilities else {},
            top_risk_drivers=json.loads(r.top_risk_drivers) if r.top_risk_drivers else [],
            top_protective_factors=json.loads(r.top_protective_factors) if r.top_protective_factors else [],
            disclaimer=r.disclaimer,
        )
        for r in records
    ]


@router.post("/me/risk-results", response_model=RiskRecord)
def save_my_risk_result(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RiskRecord:
    """Save a lifestyle risk screening result."""
    probs = payload.get("probabilities", {})
    predicted_tier = payload.get("predicted_tier", payload.get("predicted_category", "Healthy"))
    confidence = float(payload.get("confidence", probs.get(predicted_tier, 0.5)))

    item = RiskResult(
        user_id=current_user["id"],
        created_at=datetime.utcnow(),
        input_habits=json.dumps(payload.get("input_habits", {})),
        predicted_tier=predicted_tier,
        confidence=confidence,
        probabilities=json.dumps(probs),
        top_risk_drivers=json.dumps(payload.get("top_risk_factors", payload.get("top_risk_drivers", []))),
        top_protective_factors=json.dumps(payload.get("top_protective_factors", [])),
        disclaimer=payload.get("disclaimer"),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return RiskRecord(
        id=item.id,
        created_at=item.created_at.isoformat(),
        input_habits=json.loads(item.input_habits),
        predicted_tier=item.predicted_tier,
        confidence=item.confidence,
        probabilities=json.loads(item.probabilities),
        top_risk_drivers=json.loads(item.top_risk_drivers),
        top_protective_factors=json.loads(item.top_protective_factors),
        disclaimer=item.disclaimer,
    )


@router.delete("/me/risk-results/{record_id}")
def delete_my_risk_result(
    record_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a saved risk result."""
    item = (
        db.query(RiskResult)
        .filter(RiskResult.id == record_id, RiskResult.user_id == current_user["id"])
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Risk screening record not found.")
    db.delete(item)
    db.commit()
    return {"message": "Risk screening record deleted."}


# ---------------------------------------------------------------------------
# Meal Plans Endpoints
# ---------------------------------------------------------------------------
@router.get("/me/meal-plans", response_model=List[MealPlanRecord])
def list_my_meal_plans(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[MealPlanRecord]:
    """List saved meal plans for current user."""
    records = (
        db.query(MealPlan)
        .filter(MealPlan.user_id == current_user["id"])
        .order_by(MealPlan.created_at.desc())
        .all()
    )
    return [
        MealPlanRecord(
            id=r.id,
            created_at=r.created_at.isoformat(),
            title=r.title,
            days=r.days,
            target_kcal=r.target_kcal,
            daily_plans=json.loads(r.daily_plans) if r.daily_plans else [],
            grocery_list=json.loads(r.grocery_list) if r.grocery_list else [],
        )
        for r in records
    ]


@router.post("/me/meal-plans", response_model=MealPlanRecord)
def save_my_meal_plan(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MealPlanRecord:
    """Save an optimized meal plan."""
    item = MealPlan(
        user_id=current_user["id"],
        created_at=datetime.utcnow(),
        title=str(payload.get("title", f"{payload.get('days_requested', payload.get('days', 1))}-Day Optimized Meal Plan")),
        days=int(payload.get("days_requested", payload.get("days", 1))),
        target_kcal=float(payload.get("target_kcal", 2000.0)),
        daily_plans=json.dumps(payload.get("daily_plans", [])),
        grocery_list=json.dumps(payload.get("grocery_list", [])),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return MealPlanRecord(
        id=item.id,
        created_at=item.created_at.isoformat(),
        title=item.title,
        days=item.days,
        target_kcal=item.target_kcal,
        daily_plans=json.loads(item.daily_plans),
        grocery_list=json.loads(item.grocery_list),
    )


@router.delete("/me/meal-plans/{record_id}")
def delete_my_meal_plan(
    record_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a saved meal plan."""
    item = (
        db.query(MealPlan)
        .filter(MealPlan.id == record_id, MealPlan.user_id == current_user["id"])
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Meal plan record not found.")
    db.delete(item)
    db.commit()
    return {"message": "Meal plan deleted."}


# ---------------------------------------------------------------------------
# Weight Tracking Logs Endpoints
# ---------------------------------------------------------------------------
@router.get("/me/weight-logs", response_model=List[WeightLogItem])
def list_my_weight_logs(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[WeightLogItem]:
    """List weight logs ordered chronologically."""
    records = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == current_user["id"])
        .order_by(WeightLog.logged_at.asc())
        .all()
    )
    return [
        WeightLogItem(
            id=r.id,
            weight_kg=r.weight_kg,
            bmi=r.bmi,
            note=r.note,
            logged_at=r.logged_at.isoformat(),
        )
        for r in records
    ]


@router.post("/me/weight-logs", response_model=WeightLogItem)
def log_my_weight(
    payload: WeightLogItem,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WeightLogItem:
    """Log a new body weight measurement."""
    # Compute BMI if height is known in profile
    user = db.query(User).filter(User.id == current_user["id"]).first()
    computed_bmi = payload.bmi
    if computed_bmi is None and user and user.profile and user.profile.height_cm:
        height_m = user.profile.height_cm / 100.0
        computed_bmi = round(payload.weight_kg / (height_m * height_m), 1)

    log_entry = WeightLog(
        user_id=current_user["id"],
        logged_at=datetime.utcnow(),
        weight_kg=payload.weight_kg,
        bmi=computed_bmi,
        note=payload.note,
    )
    db.add(log_entry)

    # Also update profile weight_kg
    if user and user.profile:
        user.profile.weight_kg = payload.weight_kg

    db.commit()
    db.refresh(log_entry)
    return WeightLogItem(
        id=log_entry.id,
        weight_kg=log_entry.weight_kg,
        bmi=log_entry.bmi,
        note=log_entry.note,
        logged_at=log_entry.logged_at.isoformat(),
    )


@router.delete("/me/weight-logs/{log_id}")
def delete_my_weight_log(
    log_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a weight log entry."""
    item = (
        db.query(WeightLog)
        .filter(WeightLog.id == log_id, WeightLog.user_id == current_user["id"])
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Weight log entry not found.")
    db.delete(item)
    db.commit()
    return {"message": "Weight log entry deleted."}


# ---------------------------------------------------------------------------
# Goals & Alerts Endpoints
# ---------------------------------------------------------------------------
@router.get("/me/goals-alerts", response_model=List[GoalAlertItem])
def list_my_goals_alerts(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[GoalAlertItem]:
    """List current goals and alert status."""
    records = db.query(GoalAlert).filter(GoalAlert.user_id == current_user["id"]).all()
    if not records:
        # Create a default goal alert entry if none exists
        default_alert = GoalAlert(
            user_id=current_user["id"],
            target_weight_kg=70.0,
            daily_calorie_cap=2100.0,
            sodium_cap_mg=2300.0,
            hydration_target_ml=2500.0,
            alert_type="daily_monitoring",
            status="active",
            message="All nutritional metrics within established clinical bounds.",
            last_evaluated=datetime.utcnow(),
        )
        db.add(default_alert)
        db.commit()
        db.refresh(default_alert)
        records = [default_alert]

    return [
        GoalAlertItem(
            id=r.id,
            target_weight_kg=r.target_weight_kg,
            daily_calorie_cap=r.daily_calorie_cap,
            sodium_cap_mg=r.sodium_cap_mg,
            hydration_target_ml=r.hydration_target_ml,
            alert_type=r.alert_type,
            status=r.status,
            message=r.message,
            last_evaluated=r.last_evaluated.isoformat() if r.last_evaluated else None,
        )
        for r in records
    ]


@router.post("/me/goals-alerts", response_model=GoalAlertItem)
def update_or_create_goal_alert(
    payload: GoalAlertItem,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalAlertItem:
    """Set or update targets and evaluate alert trigger."""
    item = db.query(GoalAlert).filter(GoalAlert.user_id == current_user["id"]).first()
    if not item:
        item = GoalAlert(user_id=current_user["id"])
        db.add(item)

    if payload.target_weight_kg is not None:
        item.target_weight_kg = payload.target_weight_kg
    if payload.daily_calorie_cap is not None:
        item.daily_calorie_cap = payload.daily_calorie_cap
    if payload.sodium_cap_mg is not None:
        item.sodium_cap_mg = payload.sodium_cap_mg
    if payload.hydration_target_ml is not None:
        item.hydration_target_ml = payload.hydration_target_ml

    # Proactive alert evaluation rule
    status_val = "active"
    msg = "All nutritional metrics within established clinical bounds."
    if item.sodium_cap_mg and item.sodium_cap_mg < 1500.0:
        status_val = "triggered"
        msg = "Strict AHA DASH sodium cap reached (<1,500mg). Monitor daily intake."
    elif item.daily_calorie_cap and item.daily_calorie_cap < 1200.0:
        status_val = "triggered"
        msg = "Calorie target falls below metabolic safety floor (1,200 kcal/day)."

    item.status = status_val
    item.message = msg
    item.last_evaluated = datetime.utcnow()
    db.commit()
    db.refresh(item)

    return GoalAlertItem(
        id=item.id,
        target_weight_kg=item.target_weight_kg,
        daily_calorie_cap=item.daily_calorie_cap,
        sodium_cap_mg=item.sodium_cap_mg,
        hydration_target_ml=item.hydration_target_ml,
        alert_type=item.alert_type,
        status=item.status,
        message=item.message,
        last_evaluated=item.last_evaluated.isoformat() if item.last_evaluated else None,
    )


# ---------------------------------------------------------------------------
# Notifications Endpoints
# ---------------------------------------------------------------------------
@router.get("/me/notifications", response_model=List[NotificationItem])
def list_my_notifications(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[NotificationItem]:
    """Retrieve user notifications and system alerts."""
    records = (
        db.query(Notification)
        .filter(Notification.user_id == current_user["id"])
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    if not records:
        # Seed an initial welcome notification
        welcome_n = Notification(
            user_id=current_user["id"],
            created_at=datetime.utcnow(),
            title="Welcome to AI Nutrition Intelligence",
            message="Complete your clinical profile or run a Health Check to generate personalized nutrient targets.",
            is_read=False,
            notification_type="info",
        )
        db.add(welcome_n)
        db.commit()
        db.refresh(welcome_n)
        records = [welcome_n]

    return [
        NotificationItem(
            id=n.id,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            notification_type=n.notification_type,
            created_at=n.created_at.isoformat(),
        )
        for n in records
    ]


@router.put("/me/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Mark notification as read."""
    n = (
        db.query(Notification)
        .filter(Notification.id == notif_id, Notification.user_id == current_user["id"])
        .first()
    )
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")
    n.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}
