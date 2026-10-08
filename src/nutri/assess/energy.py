"""BMR (Mifflin-St Jeor) and TDEE calculation."""

from typing import Dict

# Standard physical activity multipliers (FAO/WHO/UNU)
ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "sedentary": 1.2,  # Little or no exercise, desk job
    "light": 1.375,  # Light exercise/sports 1-3 days/week
    "moderate": 1.55,  # Moderate exercise/sports 3-5 days/week
    "active": 1.725,  # Hard exercise/sports 6-7 days/week
    "very_active": 1.9,  # Very hard exercise, physical job or 2x/day training
}


def calculate_bmr_mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Formulas:
    - Men:   (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    - Women: (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        sex: 'male', 'female', 'm', or 'f'.

    Returns:
        BMR in kcal/day rounded to 1 decimal place.
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("Weight, height, and age must be strictly positive.")

    base = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age)
    sex_clean = str(sex).lower().strip()

    if sex_clean in ["male", "m"]:
        bmr = base + 5.0
    elif sex_clean in ["female", "f"]:
        bmr = base - 161.0
    else:
        # If unstated, use midpoint between male (+5) and female (-161)
        bmr = base - 78.0

    return round(bmr, 1)


calculate_bmr = calculate_bmr_mifflin_st_jeor


def calculate_tdee(bmr: float, activity_level: str = "moderate") -> float:
    """Calculate Total Daily Energy Expenditure (TDEE).

    Formula: BMR * activity_multiplier

    Args:
        bmr: Basal metabolic rate (kcal/day).
        activity_level: One of 'sedentary', 'light', 'moderate', 'active', 'very_active'.

    Returns:
        TDEE in kcal/day rounded to 1 decimal place.
    """
    key = str(activity_level).lower().strip().replace(" ", "_")
    multiplier = ACTIVITY_MULTIPLIERS.get(key, 1.375)
    tdee = bmr * multiplier
    return round(tdee, 1)
