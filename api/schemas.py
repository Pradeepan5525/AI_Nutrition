"""Pydantic v2 schemas for the AI Nutrition Intelligence REST API.

All request and response contracts are strictly validated with explicit boundaries,
enums, and documentation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Assessment Schemas
# ---------------------------------------------------------------------------
class AssessRequest(BaseModel):
    """Payload for metabolic, BMI, and clinical safety assessment."""

    age: int = Field(..., ge=1, le=120, description="Age in years")
    sex: Literal["male", "female"] = Field(..., description="Biological sex ('male' or 'female')")
    height_cm: float = Field(..., ge=50.0, le=250.0, description="Height in centimeters")
    weight_kg: float = Field(..., ge=20.0, le=350.0, description="Weight in kilograms")
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = Field(
        ..., description="Physical activity frequency level"
    )
    goal: Literal["weight_loss", "maintenance", "muscle_gain"] = Field(
        default="maintenance", description="Nutritional caloric objective"
    )
    dietary_restrictions: List[str] = Field(
        default_factory=list, description="Dietary tags e.g. ['vegan', 'vegetarian']"
    )
    allergies: List[str] = Field(
        default_factory=list, description="Allergens to strictly exclude e.g. ['peanuts', 'gluten']"
    )
    condition_flags: List[str] = Field(
        default_factory=list, description="Clinical flags e.g. ['hypertension', 'diabetes']"
    )
    is_asian: bool = Field(
        default=False, description="Use Asian-specific BMI thresholds (WHO recommendation)"
    )
    is_pregnant: bool = Field(default=False, description="Pregnancy status")
    is_lactating: bool = Field(default=False, description="Lactation / nursing status")
    has_ed_history: bool = Field(default=False, description="History of eating disorders")


class AssessResponse(BaseModel):
    """Response containing BMI, TDEE, macronutrient distribution, and safety audit."""

    bmi: float
    bmi_category: str
    ideal_weight_min_kg: float
    ideal_weight_max_kg: float
    bmr_kcal: float
    tdee_kcal: float
    target_kcal: float
    deficit_or_surplus_kcal: float
    macros: Dict[str, float]
    water_ml: float
    safety_gate: Dict[str, Any]
    clinical_constraints: Dict[str, Any]
    disclaimer: str


# ---------------------------------------------------------------------------
# Lifestyle Risk Model Schemas
# ---------------------------------------------------------------------------
class RiskRequest(BaseModel):
    """Lifestyle questionnaire features for obesity lifestyle risk screening."""

    age: float = Field(..., ge=10.0, le=100.0, description="Age in years")
    gender: Literal["Female", "Male", "female", "male"] = Field(..., description="Gender")
    family_history_with_overweight: Literal["yes", "no", "Yes", "No"] = Field(
        ..., description="Family history of overweight ('yes' or 'no')"
    )
    favc: Literal["yes", "no", "Yes", "No"] = Field(
        ..., description="Frequent consumption of high-caloric food ('yes' or 'no')"
    )
    fcvc: float = Field(
        ..., ge=1.0, le=3.0, description="Frequency of vegetable consumption (1 to 3)"
    )
    ncp: float = Field(..., ge=1.0, le=4.0, description="Number of main meals per day (1 to 4)")
    caec: Literal[
        "no", "Sometimes", "Frequently", "Always", "sometimes", "frequently", "always"
    ] = Field(..., description="Consumption of food between meals")
    smoke: Literal["yes", "no", "Yes", "No"] = Field(
        ..., description="Smoking status ('yes' or 'no')"
    )
    ch2o: float = Field(..., ge=1.0, le=3.0, description="Daily water intake scale (1 to 3)")
    scc: Literal["yes", "no", "Yes", "No"] = Field(
        ..., description="Calorie consumption monitoring ('yes' or 'no')"
    )
    faf: float = Field(
        ..., ge=0.0, le=3.0, description="Physical activity frequency scale (0 to 3)"
    )
    tue: float = Field(..., ge=0.0, le=2.0, description="Time using technology devices (0 to 2)")
    calc: Literal[
        "no", "Sometimes", "Frequently", "Always", "sometimes", "frequently", "always"
    ] = Field(..., description="Alcohol consumption frequency")
    mtrans: Literal[
        "Automobile",
        "Motorbike",
        "Bike",
        "Public_Transportation",
        "Walking",
        "automobile",
        "motorbike",
        "bike",
        "public_transportation",
        "walking",
    ] = Field(..., description="Primary mode of transportation")


class RiskResponse(BaseModel):
    """Calibrated predictions and SHAP lifestyle factor breakdown."""

    predicted_category: str
    probabilities: Dict[str, float]
    risk_tier: str
    top_risk_factors: List[str]
    top_protective_factors: List[str]
    model_version: str
    disclaimer: str


# ---------------------------------------------------------------------------
# Meal Plan Optimization Schemas
# ---------------------------------------------------------------------------
class PlanRequest(BaseModel):
    """Optimization parameters for daily or weekly meal plan synthesis."""

    target_kcal: float = Field(..., ge=1200.0, le=4500.0, description="Target daily energy in kcal")
    protein_target_g: float = Field(..., ge=30.0, le=300.0, description="Target protein in grams")
    max_sodium_mg: float = Field(
        default=2300.0, ge=500.0, le=4000.0, description="Upper bound sodium (mg)"
    )
    max_sat_fat_g: float = Field(
        default=22.0, ge=3.0, le=60.0, description="Upper bound saturated fat (g)"
    )
    max_sugar_g: float = Field(
        default=50.0, ge=5.0, le=120.0, description="Upper bound added sugar (g)"
    )
    user_allergies: List[str] = Field(default_factory=list, description="Allergens to exclude")
    dietary_restrictions: List[str] = Field(
        default_factory=list, description="Dietary tags e.g. ['vegan']"
    )
    strict_allergens: bool = Field(default=True, description="Strict tri-state allergen exclusion")
    days: int = Field(default=1, ge=1, le=7, description="Number of days (1 to 7)")


class PlanResponse(BaseModel):
    """Generated meal plan and consolidated grocery list."""

    days_requested: int
    daily_plans: List[Dict[str, Any]]
    grocery_list: Dict[str, Any]
    solver_status: str
    solver_time_sec: float
    disclaimer: str


# ---------------------------------------------------------------------------
# Food Search & Swaps Schemas
# ---------------------------------------------------------------------------
class FoodItem(BaseModel):
    """Harmonized food item details."""

    food_id: str
    name: str
    category: str
    food_type: str
    health_score_v2: float
    nutri_score: str
    kcal_100g: float
    protein_100g: float
    carbs_100g: float
    fat_100g: float
    fiber_100g: float
    sugar_100g: float
    sodium_mg_100g: float
    sat_fat_100g: float
    cholesterol_mg_100g: float
    allergens: Dict[str, str]
    dietary_restrictions: List[str]


class FoodSearchResponse(BaseModel):
    """Paginated food search results."""

    total_matches: int
    page: int
    page_size: int
    results: List[FoodItem]


class FoodSwapItem(BaseModel):
    """Suggested healthier replacement food item with differential metrics."""

    food_id: str
    name: str
    category: str
    health_score_v2: float
    score_improvement: float
    kcal_diff: float
    sodium_diff_mg: float
    sugar_diff_g: float
    sat_fat_diff_g: float
    reasons: List[str]


class FoodSwapResponse(BaseModel):
    """Healthier swap alternatives."""

    original_food: Dict[str, Any]
    count: int
    swaps: List[FoodSwapItem]


# ---------------------------------------------------------------------------
# Report & System Health Schemas
# ---------------------------------------------------------------------------
class ReportRequest(BaseModel):
    """Full data payload for compiling clinical summary PDF report."""

    client_info: Dict[str, Any]
    target_nutrition: Dict[str, Any]
    safety_gate: Optional[Dict[str, Any]] = None
    clinical_rules: Optional[Dict[str, Any]] = None
    risk_screening: Optional[Dict[str, Any]] = None
    meal_plan: Optional[Dict[str, Any]] = None
    grocery_list: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """System operational health and telemetry."""

    status: str
    timestamp: str
    model_loaded: bool
    total_foods_indexed: int
    database_connected: bool


class VersionResponse(BaseModel):
    """Version metadata."""

    system: str
    version: str
    model_architecture: str
    optimizer_engine: str


# ---------------------------------------------------------------------------
# Authentication & User Schemas
# ---------------------------------------------------------------------------
class UserRegisterRequest(BaseModel):
    """Payload to register a new user account."""

    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=128, description="Account password")
    full_name: Optional[str] = Field(default=None, description="User full name")
    role: Literal["patient", "clinician"] = Field(
        default="patient", description="User role in the system"
    )
    initial_profile: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional initial metabolic/dietary profile"
    )


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""

    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Plaintext account password")


class UserResponse(BaseModel):
    """Public user record details."""

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    saved_profile: Optional[Dict[str, Any]] = None
    created_at: str
    last_login: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT Bearer access token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserProfileUpdateRequest(BaseModel):
    """Payload for updating saved anthropometric & dietary profile."""

    profile: Dict[str, Any] = Field(..., description="Key-value mapping of saved user parameters")


class RegisterRequest(BaseModel):
    """Payload to register a new user account with educational disclaimer."""

    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Account password (min 8 chars, letters+digits)")
    full_name: Optional[str] = Field(default=None, description="User full name")
    username: Optional[str] = Field(default=None, description="Optional username (defaults to email)")
    accept_disclaimer: bool = Field(default=False, description="Must acknowledge educational disclaimer")


class LoginRequest(BaseModel):
    """Payload for user authentication with remember-me support."""

    username_or_email: Optional[str] = Field(default=None, description="Username or email address")
    email: Optional[str] = Field(default=None, description="Email address")
    password: str = Field(..., description="Plaintext account password")
    remember_me: bool = Field(default=False, description="Extend session lifetime to 30 days")


class ProfileDetail(BaseModel):
    """Structured user clinical & anthropometric profile."""

    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    is_asian: bool = False
    conditions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    preferred_cuisine: str = "Any"
    onboarding_completed: bool = False
    updated_at: Optional[str] = None


class UserFullResponse(BaseModel):
    """Complete user representation including structured profile."""

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    profile: Optional[ProfileDetail] = None
    saved_profile: Optional[Dict[str, Any]] = None
    created_at: str
    last_login: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    """Payload for changing account password."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class WeightLogItem(BaseModel):
    """Body weight tracking entry."""

    id: Optional[int] = None
    weight_kg: float
    bmi: Optional[float] = None
    note: Optional[str] = None
    logged_at: Optional[str] = None


class GoalAlertItem(BaseModel):
    """Personalized goal and alert parameters."""

    id: Optional[int] = None
    target_weight_kg: Optional[float] = None
    daily_calorie_cap: Optional[float] = None
    sodium_cap_mg: Optional[float] = None
    hydration_target_ml: Optional[float] = None
    alert_type: Optional[str] = None
    status: str = "active"
    message: Optional[str] = None
    last_evaluated: Optional[str] = None


class NotificationItem(BaseModel):
    """In-app alert notification."""

    id: Optional[int] = None
    title: str
    message: str
    is_read: bool = False
    notification_type: str = "info"
    created_at: Optional[str] = None


class AssessmentRecord(BaseModel):
    """Persisted user assessment record."""

    id: Optional[int] = None
    created_at: Optional[str] = None
    input_data: Dict[str, Any]
    bmi: float
    bmi_category: str
    bmr_kcal: float
    tdee_kcal: float
    target_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sodium_mg: float
    water_ml: float
    safety_cleared: bool = True
    safety_flags: List[str] = Field(default_factory=list)
    clinical_constraints: Dict[str, Any] = Field(default_factory=dict)


class RiskRecord(BaseModel):
    """Persisted obesity lifestyle risk screening record."""

    id: Optional[int] = None
    created_at: Optional[str] = None
    input_habits: Dict[str, Any]
    predicted_tier: str
    confidence: float
    probabilities: Dict[str, float]
    top_risk_drivers: List[Dict[str, Any]]
    top_protective_factors: List[Dict[str, Any]]
    disclaimer: Optional[str] = None


class MealPlanRecord(BaseModel):
    """Persisted meal plan optimization record."""

    id: Optional[int] = None
    created_at: Optional[str] = None
    title: str
    days: int
    target_kcal: float
    daily_plans: List[Dict[str, Any]]
    grocery_list: List[Dict[str, Any]]


class DataExportResponse(BaseModel):
    """Complete GDPR/HIPAA-compliant personal data export."""

    user: Dict[str, Any]
    profile: Optional[Dict[str, Any]] = None
    assessments: List[Dict[str, Any]] = Field(default_factory=list)
    risk_results: List[Dict[str, Any]] = Field(default_factory=list)
    meal_plans: List[Dict[str, Any]] = Field(default_factory=list)
    weight_logs: List[Dict[str, Any]] = Field(default_factory=list)
    goals_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    notifications: List[Dict[str, Any]] = Field(default_factory=list)
    export_timestamp: str

