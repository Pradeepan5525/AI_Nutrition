"""SQLAlchemy database models for AI Nutrition Intelligence System."""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from nutri.database.engine import Base


class User(Base):
    """User account entity with security metadata and relationship cascade."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="patient", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    risk_results = relationship("RiskResult", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")
    weight_logs = relationship("WeightLog", back_populates="user", cascade="all, delete-orphan")
    goals_alerts = relationship("GoalAlert", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    """Clinical, anthropometric, and dietary profile associated with a user."""

    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    sex = Column(String(20), nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    activity_level = Column(String(50), nullable=True)
    goal = Column(String(50), nullable=True)
    is_asian = Column(Boolean, default=False, nullable=False)
    conditions = Column(Text, default="[]", nullable=False)  # JSON serialized list
    allergies = Column(Text, default="[]", nullable=False)   # JSON serialized list
    dietary_restrictions = Column(Text, default="[]", nullable=False)  # JSON serialized list
    preferred_cuisine = Column(String(100), default="Any", nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="profile")


class Assessment(Base):
    """Historical metabolic, caloric, and clinical guideline assessments."""

    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    input_data = Column(Text, default="{}", nullable=False)  # JSON serialized input
    bmi = Column(Float, nullable=False)
    bmi_category = Column(String(50), nullable=False)
    bmr_kcal = Column(Float, nullable=False)
    tdee_kcal = Column(Float, nullable=False)
    target_kcal = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    sodium_mg = Column(Float, nullable=False)
    water_ml = Column(Float, nullable=False)
    safety_cleared = Column(Boolean, default=True, nullable=False)
    safety_flags = Column(Text, default="[]", nullable=False)
    clinical_constraints = Column(Text, default="{}", nullable=False)

    user = relationship("User", back_populates="assessments")


class RiskResult(Base):
    """Obesity lifestyle risk screening inference record with SHAP explanations."""

    __tablename__ = "risk_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    input_habits = Column(Text, default="{}", nullable=False)
    predicted_tier = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities = Column(Text, default="{}", nullable=False)
    top_risk_drivers = Column(Text, default="[]", nullable=False)
    top_protective_factors = Column(Text, default="[]", nullable=False)
    disclaimer = Column(Text, nullable=True)

    user = relationship("User", back_populates="risk_results")


class MealPlan(Base):
    """LP-optimized single or 7-day meal plan schedule."""

    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    title = Column(String(255), default="Optimized Meal Plan", nullable=False)
    days = Column(Integer, default=1, nullable=False)
    target_kcal = Column(Float, nullable=False)
    daily_plans = Column(Text, default="[]", nullable=False)
    grocery_list = Column(Text, default="[]", nullable=False)

    user = relationship("User", back_populates="meal_plans")


class WeightLog(Base):
    """User body weight tracking log."""

    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    weight_kg = Column(Float, nullable=False)
    bmi = Column(Float, nullable=True)
    note = Column(String(500), nullable=True)

    user = relationship("User", back_populates="weight_logs")


class GoalAlert(Base):
    """Personalized health goals and rule-triggered proactive alerts."""

    __tablename__ = "goals_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_weight_kg = Column(Float, nullable=True)
    daily_calorie_cap = Column(Float, nullable=True)
    sodium_cap_mg = Column(Float, nullable=True)
    hydration_target_ml = Column(Float, nullable=True)
    alert_type = Column(String(100), nullable=True)
    status = Column(String(20), default="active", nullable=False)  # "active", "triggered"
    message = Column(String(500), nullable=True)
    last_evaluated = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="goals_alerts")


class Notification(Base):
    """Proactive user notification messages."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    notification_type = Column(String(50), default="info", nullable=False)

    user = relationship("User", back_populates="notifications")


class RefreshToken(Base):
    """Persisted refresh tokens with cryptographic hash and revocation flag."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
