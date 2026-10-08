"""Nutrient targets engine calculating caloric, macro, and micro guidance."""

from typing import Any, Dict

from nutri.config import FIBER_PER_1000_KCAL, MAX_SODIUM_MG, MIN_KCAL_MEN, MIN_KCAL_WOMEN


def calculate_nutrient_targets(
    tdee: float,
    weight_kg: float,
    sex: str,
    goal: str = "maintain",
    rate_kg_per_week: float = 0.5,
    custom_protein_g_per_kg: float = 0.0,
) -> Dict[str, Any]:
    """Calculate personalized daily calorie, macronutrient, and micronutrient targets.

    Args:
        tdee: Total Daily Energy Expenditure in kcal.
        weight_kg: Current body weight in kg.
        sex: 'male', 'female', 'm', or 'f'.
        goal: 'maintain', 'lose', or 'gain'.
        rate_kg_per_week: Target rate of weight change (0.25 to 1.0 kg/week).
        custom_protein_g_per_kg: Optional override for protein g/kg ratio.

    Returns:
        Dictionary of complete nutritional targets, floors, and guidance.
    """
    goal_clean = str(goal).lower().strip()
    sex_clean = str(sex).lower().strip()
    is_male = sex_clean in ["male", "m"]

    # 1. Determine caloric adjustment
    # 1 kg body fat ≈ 7,700 kcal -> 0.5 kg/week ≈ 3,850 kcal/week ≈ 550 kcal/day
    daily_delta = round((rate_kg_per_week * 7700.0) / 7.0)

    if goal_clean == "lose":
        raw_kcal = tdee - daily_delta
    elif goal_clean == "gain":
        raw_kcal = tdee + daily_delta
    else:  # maintain
        raw_kcal = tdee

    # 2. Enforce minimum caloric floors for safety
    floor_kcal = MIN_KCAL_MEN if is_male else MIN_KCAL_WOMEN
    floor_applied = False

    if raw_kcal < floor_kcal:
        target_kcal = floor_kcal
        floor_applied = True
    else:
        target_kcal = raw_kcal

    target_kcal = round(target_kcal)

    # 3. Protein target (g/kg)
    # Evidence: 1.2 - 1.6 g/kg during caloric deficit to preserve lean mass; 0.8 - 1.2 g/kg otherwise
    if custom_protein_g_per_kg > 0:
        protein_ratio = custom_protein_g_per_kg
    elif goal_clean == "lose":
        protein_ratio = 1.4
    elif goal_clean == "gain":
        protein_ratio = 1.6
    else:
        protein_ratio = 1.0

    protein_g = round(weight_kg * protein_ratio, 1)
    protein_kcal = protein_g * 4.0

    # Ensure protein calories do not exceed 40% of total calories
    if protein_kcal > (0.40 * target_kcal):
        protein_kcal = 0.40 * target_kcal
        protein_g = round(protein_kcal / 4.0, 1)

    # 4. Fat target (25% to 30% of total kcal)
    fat_pct = 0.28
    fat_kcal = target_kcal * fat_pct
    fat_g = round(fat_kcal / 9.0, 1)

    # 5. Carbohydrate target (remaining kcal)
    remaining_kcal = max(0.0, target_kcal - (protein_kcal + fat_kcal))
    carbs_g = round(remaining_kcal / 4.0, 1)

    # 6. Fiber (14 g per 1,000 kcal)
    fiber_g = round((target_kcal / 1000.0) * FIBER_PER_1000_KCAL, 1)

    # 7. Sugar cap (< 10% of total kcal)
    max_sugar_g = round((target_kcal * 0.10) / 4.0, 1)

    # 8. Sodium cap
    max_sodium_mg = MAX_SODIUM_MG

    # 9. Daily Water Guidance (approx 35 ml per kg)
    water_ml = round(weight_kg * 35.0)

    return {
        "target_kcal": target_kcal,
        "raw_calculated_kcal": round(raw_kcal),
        "calorie_floor_applied": floor_applied,
        "floor_kcal": floor_kcal,
        "goal": goal_clean,
        "macros": {
            "protein_g": protein_g,
            "protein_kcal": round(protein_kcal),
            "protein_pct": round((protein_kcal / target_kcal) * 100, 1),
            "fat_g": fat_g,
            "fat_kcal": round(fat_kcal),
            "fat_pct": round((fat_kcal / target_kcal) * 100, 1),
            "carbs_g": carbs_g,
            "carbs_kcal": round(remaining_kcal),
            "carbs_pct": round((remaining_kcal / target_kcal) * 100, 1),
        },
        "micros_and_guidance": {
            "fiber_g": fiber_g,
            "max_added_sugar_g": max_sugar_g,
            "max_sodium_mg": max_sodium_mg,
            "daily_water_ml": water_ml,
            "daily_water_liters": round(water_ml / 1000.0, 1),
        },
    }
