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
