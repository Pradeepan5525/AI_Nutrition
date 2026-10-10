"""High-level user service managing authentication, credentials, profile, history, and exports."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from nutri.auth.security import (
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    validate_email_format,
    validate_password_strength,
    verify_password,
)
from nutri.database.models import (
    Assessment,
    GoalAlert,
    MealPlan,
    Notification,
    Profile,
    RefreshToken,
    RiskResult,
    User,
    WeightLog,
)


def get_user_by_email_or_username(db: Session, identifier: str) -> Optional[User]:
    """Retrieve user entity by lowercase email or case-insensitive username."""
    ident = identifier.strip()
    user = (
        db.query(User)
        .filter((User.email.ilike(ident)) | (User.username.ilike(ident)))
        .first()
    )
    if user:
        return user

    # Fallback to UserDB (e.g. demo_user seeded in foods.db)
    try:
        from nutri.auth.user_db import UserDB
        legacy_db = UserDB()
        legacy_u = legacy_db.get_user_by_username(ident) or legacy_db.get_user_by_email(ident)
        if legacy_u:
            existing_by_email = db.query(User).filter(User.email.ilike(legacy_u["email"])).first()
            if existing_by_email:
                existing_by_email.username = legacy_u["username"]
                db.commit()
                return existing_by_email

            pwd_hash = ""
            with legacy_db._connection() as conn:
                p_row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (legacy_u["id"],)).fetchone()
                if p_row:
                    pwd_hash = p_row["password_hash"]

            user = User(
                username=legacy_u["username"],
                email=legacy_u["email"],
                password_hash=pwd_hash,
                full_name=legacy_u.get("full_name"),
                role=legacy_u.get("role", "patient"),
                is_active=True,
            )
            db.add(user)
            db.flush()
            pdata = legacy_u.get("saved_profile") or {}
            prof = Profile(
                user_id=user.id,
                age=pdata.get("age"),
                sex=pdata.get("gender") or pdata.get("sex"),
                height_cm=pdata.get("height_cm"),
                weight_kg=pdata.get("weight_kg"),
                activity_level=pdata.get("activity_level"),
                goal=pdata.get("goal"),
                conditions=json.dumps(pdata.get("conditions", [])),
                allergies=json.dumps(pdata.get("allergens", []) or pdata.get("allergies", [])),
                dietary_restrictions=json.dumps([pdata["dietary_preference"]] if pdata.get("dietary_preference") else []),
                preferred_cuisine="Standard",
            )
            db.add(prof)
            db.commit()
            return user
    except Exception:
        pass

    return None



def authenticate_user_full(
    db: Session, identifier: str, password: str
) -> Tuple[Optional[User], Optional[str]]:
    """Validate user credentials with lockout protection.

    Returns:
        (user, None) on success.
        (None, error_message) on failure.
    """
    user = get_user_by_email_or_username(db, identifier)
    if not user:
        return None, "Invalid email or password."

    # Check lockout
    now = datetime.utcnow()
    if user.locked_until and user.locked_until > now:
        remaining_minutes = int((user.locked_until - now).total_seconds() / 60) + 1
        return None, f"Account temporarily locked due to multiple failed login attempts. Try again in {remaining_minutes} minutes."

    if not verify_password(password, user.password_hash):
        # Check if legacy UserDB validates this password (e.g. demo123 for demo_user)
        try:
            from nutri.auth.user_db import UserDB
            legacy_auth = UserDB().authenticate_user(identifier, password)
            if legacy_auth:
                user.password_hash = hash_password(password)
                user.failed_login_attempts = 0
                user.locked_until = None
                user.last_login = now
                db.commit()
                return user, None
        except Exception:
            pass

        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
        db.commit()
        return None, "Invalid email or password."

    # Reset failure tracking on success
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = now
    db.commit()
    return user, None


def register_user_full(
    db: Session,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    username: Optional[str] = None,
    role: str = "patient",
    initial_profile: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[User], Optional[str]]:
    """Register a new user account with validated constraints."""
    email_clean = email.strip().lower()
    if not validate_email_format(email_clean):
        return None, "Invalid email format."

    valid_pwd, pwd_err = validate_password_strength(password)
    if not valid_pwd:
        return None, pwd_err

    # Check existing user
    if db.query(User).filter(User.email.ilike(email_clean)).first():
        return None, "CONFLICT:An account with this email address already exists."

    uname = username.strip() if username else email_clean.split("@")[0]
    # Ensure username uniqueness
    existing_u = db.query(User).filter(User.username.ilike(uname)).first()
    if existing_u:
        uname = f"{uname}_{datetime.utcnow().strftime('%M%S')}"

    pwd_hash = hash_password(password)
    user = User(
        username=uname,
        email=email_clean,
        password_hash=pwd_hash,
        full_name=full_name.strip() if full_name else uname,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Create associated profile
    init_prof = initial_profile or {}
    profile = Profile(
        user_id=user.id,
        age=init_prof.get("age"),
        sex=init_prof.get("sex") or init_prof.get("gender"),
        height_cm=init_prof.get("height_cm"),
        weight_kg=init_prof.get("weight_kg"),
        activity_level=init_prof.get("activity_level"),
        goal=init_prof.get("goal"),
        is_asian=bool(init_prof.get("is_asian", False)),
        conditions=json.dumps(init_prof.get("conditions", [])),
        allergies=json.dumps(init_prof.get("allergens", init_prof.get("allergies", []))),
        dietary_restrictions=json.dumps(init_prof.get("dietary_restrictions", [])),
        preferred_cuisine=init_prof.get("preferred_cuisine", "Any"),
        onboarding_completed=bool(init_prof.get("onboarding_completed", False)),
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user, None


def create_user_refresh_token(
    db: Session, user_id: int, remember_me: bool = False
) -> str:
    """Generate and store a new refresh token for the user."""
    token_str = generate_refresh_token()
    token_hash = hash_refresh_token(token_str)
    days = 30 if remember_me else 7
    expires_at = datetime.utcnow() + timedelta(days=days)

    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(rt)
    db.commit()
    return token_str


def verify_and_rotate_refresh_token(
    db: Session, token_str: str
) -> Tuple[Optional[User], Optional[str]]:
    """Verify refresh token, revoke it, and issue a new one (rotation)."""
    if not token_str:
        return None, None

    token_hash = hash_refresh_token(token_str)
    rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked == False)
        .first()
    )
    if not rt or rt.expires_at < datetime.utcnow():
        return None, None

    # Rotate: revoke old token
    rt.revoked = True
    user = db.query(User).filter(User.id == rt.user_id, User.is_active == True).first()
    if not user:
        db.commit()
        return None, None

    # Issue new token
    new_token_str = create_user_refresh_token(db, user.id)
    return user, new_token_str


def revoke_refresh_token(db: Session, token_str: str) -> None:
    """Revoke a refresh token on logout."""
    if not token_str:
        return
    token_hash = hash_refresh_token(token_str)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt:
        rt.revoked = True
        db.commit()


def format_user_dict(user: User) -> Dict[str, Any]:
    """Convert User entity to public response dict."""
    prof_dict = {}
    if user.profile:
        p = user.profile
        try:
            conds = json.loads(p.conditions) if isinstance(p.conditions, str) else p.conditions
        except Exception:
            conds = []
        try:
            allg = json.loads(p.allergies) if isinstance(p.allergies, str) else p.allergies
        except Exception:
            allg = []
        try:
            restr = json.loads(p.dietary_restrictions) if isinstance(p.dietary_restrictions, str) else p.dietary_restrictions
        except Exception:
            restr = []

        prof_dict = {
            "age": p.age,
            "sex": p.sex,
            "height_cm": p.height_cm,
            "weight_kg": p.weight_kg,
            "activity_level": p.activity_level,
            "goal": p.goal,
            "is_asian": p.is_asian,
            "conditions": conds,
            "allergies": allg,
            "dietary_restrictions": restr,
            "preferred_cuisine": p.preferred_cuisine,
            "onboarding_completed": p.onboarding_completed,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "profile": prof_dict if prof_dict else None,
        "saved_profile": prof_dict if prof_dict else None,
        "created_at": user.created_at.isoformat() if user.created_at else "",
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def update_profile_for_user(
    db: Session, user_id: int, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update anthropometric & clinical profile."""
    prof = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not prof:
        prof = Profile(user_id=user_id)
        db.add(prof)

    if "age" in data and data["age"] is not None:
        prof.age = int(data["age"])
    if "sex" in data and data["sex"] is not None:
        prof.sex = str(data["sex"]).lower()
    elif "gender" in data and data["gender"] is not None:
        prof.sex = str(data["gender"]).lower()
    if "height_cm" in data and data["height_cm"] is not None:
        prof.height_cm = float(data["height_cm"])
    if "weight_kg" in data and data["weight_kg"] is not None:
        prof.weight_kg = float(data["weight_kg"])
    if "activity_level" in data and data["activity_level"] is not None:
        prof.activity_level = str(data["activity_level"])
    if "goal" in data and data["goal"] is not None:
        prof.goal = str(data["goal"])
    if "is_asian" in data and data["is_asian"] is not None:
        prof.is_asian = bool(data["is_asian"])
    if "conditions" in data and data["conditions"] is not None:
        prof.conditions = json.dumps(data["conditions"])
    if "allergies" in data and data["allergies"] is not None:
        prof.allergies = json.dumps(data["allergies"])
    elif "allergens" in data and data["allergens"] is not None:
        prof.allergies = json.dumps(data["allergens"])
    if "dietary_restrictions" in data and data["dietary_restrictions"] is not None:
        prof.dietary_restrictions = json.dumps(data["dietary_restrictions"])
    if "preferred_cuisine" in data and data["preferred_cuisine"] is not None:
        prof.preferred_cuisine = str(data["preferred_cuisine"])
    if "onboarding_completed" in data and data["onboarding_completed"] is not None:
        prof.onboarding_completed = bool(data["onboarding_completed"])

    prof.updated_at = datetime.utcnow()
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    return format_user_dict(user) if user else None


def export_user_data(db: Session, user_id: int) -> Dict[str, Any]:
    """Compile all user data into an exportable dictionary."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}

    user_info = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

    user_dict = format_user_dict(user)

    assessments = [
        {
            "id": a.id,
            "created_at": a.created_at.isoformat(),
            "input_data": json.loads(a.input_data) if a.input_data else {},
            "bmi": a.bmi,
            "bmi_category": a.bmi_category,
            "bmr_kcal": a.bmr_kcal,
            "tdee_kcal": a.tdee_kcal,
            "target_kcal": a.target_kcal,
            "protein_g": a.protein_g,
            "carbs_g": a.carbs_g,
            "fat_g": a.fat_g,
            "sodium_mg": a.sodium_mg,
            "water_ml": a.water_ml,
            "safety_cleared": a.safety_cleared,
            "safety_flags": json.loads(a.safety_flags) if a.safety_flags else [],
            "clinical_constraints": json.loads(a.clinical_constraints) if a.clinical_constraints else {},
        }
        for a in user.assessments
    ]

    risks = [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "input_habits": json.loads(r.input_habits) if r.input_habits else {},
            "predicted_tier": r.predicted_tier,
            "confidence": r.confidence,
            "probabilities": json.loads(r.probabilities) if r.probabilities else {},
            "top_risk_drivers": json.loads(r.top_risk_drivers) if r.top_risk_drivers else [],
            "top_protective_factors": json.loads(r.top_protective_factors) if r.top_protective_factors else [],
            "disclaimer": r.disclaimer,
        }
        for r in user.risk_results
    ]

    plans = [
        {
            "id": m.id,
            "created_at": m.created_at.isoformat(),
            "title": m.title,
            "days": m.days,
            "target_kcal": m.target_kcal,
            "daily_plans": json.loads(m.daily_plans) if m.daily_plans else [],
            "grocery_list": json.loads(m.grocery_list) if m.grocery_list else [],
        }
        for m in user.meal_plans
    ]

    weights = [
        {
            "id": w.id,
            "logged_at": w.logged_at.isoformat(),
            "weight_kg": w.weight_kg,
            "bmi": w.bmi,
            "note": w.note,
        }
        for w in user.weight_logs
    ]

    alerts = [
        {
            "id": g.id,
            "target_weight_kg": g.target_weight_kg,
            "daily_calorie_cap": g.daily_calorie_cap,
            "sodium_cap_mg": g.sodium_cap_mg,
            "hydration_target_ml": g.hydration_target_ml,
            "alert_type": g.alert_type,
            "status": g.status,
            "message": g.message,
            "last_evaluated": g.last_evaluated.isoformat() if g.last_evaluated else None,
        }
        for g in user.goals_alerts
    ]

    notifications = [
        {
            "id": n.id,
            "created_at": n.created_at.isoformat(),
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "notification_type": n.notification_type,
        }
        for n in user.notifications
    ]

    return {
        "user": user_info,
        "profile": user_dict.get("profile"),
        "assessments": assessments,
        "risk_results": risks,
        "meal_plans": plans,
        "weight_logs": weights,
        "goals_alerts": alerts,
        "notifications": notifications,
        "export_timestamp": datetime.utcnow().isoformat() + "Z",
    }


def delete_user_account(db: Session, user_id: int) -> bool:
    """Permanently delete user and cascade delete all associated records."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
