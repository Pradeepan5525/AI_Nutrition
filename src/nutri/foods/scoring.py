"""Transparent nutritional scoring engine (Health Score v2)."""

from typing import Any, Dict, Optional

NUTRISCORE_MAP = {
    "a": 95.0,
    "b": 80.0,
    "c": 60.0,
    "d": 40.0,
    "e": 20.0,
}


def calculate_health_score_v2(
    kcal_100g: float,
    protein_100g: float,
    fat_100g: float,
    sat_fat_100g: float,
    carbs_100g: float,
    sugar_100g: float,
    fiber_100g: float,
    sodium_mg_100g: float,
    calcium_mg_100g: Optional[float] = 0.0,
    iron_mg_100g: Optional[float] = 0.0,
    vitamin_c_mg_100g: Optional[float] = 0.0,
    nutriscore_grade: Optional[str] = None,
) -> float:
    """Calculate transparent evidence-based Health Score v2 (0 - 100).

    Formula Rationale:
    1. Base starts at 50 (neutral).
    2. Positive Nutrient Density Points (+40 max):
       - Fiber: +2.5 pts per 1g/100g up to 8g (+20 max)
       - Protein: +0.6 pts per 1g/100g up to 25g (+15 max)
       - Calcium, Iron, Vitamin C: up to +5 max combined
    3. Negative Risk Points (-50 max):
       - Free/Total Sugar: -0.8 pts per 1g/100g up to 25g (-20 max)
       - Saturated Fat: -1.5 pts per 1g/100g up to 10g (-15 max)
       - Sodium: -1.0 pt per 100mg/100g up to 1500mg (-15 max)
    4. Calorie Density Factor:
       - If energy > 400 kcal/100g and fiber < 3g, penalty up to -10 pts.
    5. Nutri-Score Blending:
       - If authoritative Nutri-Score grade is present, blend 60% calculated + 40% Nutri-Score.

    Returns:
        Float score clamped to [0.0, 100.0].
    """
    kcal = max(0.0, float(kcal_100g or 0.0))
    protein = max(0.0, float(protein_100g or 0.0))
    sat_fat = max(0.0, float(sat_fat_100g or 0.0))
    sugar = max(0.0, float(sugar_100g or 0.0))
    fiber = max(0.0, float(fiber_100g or 0.0))
    sodium = max(0.0, float(sodium_mg_100g or 0.0))
    calcium = max(0.0, float(calcium_mg_100g or 0.0))
    iron = max(0.0, float(iron_mg_100g or 0.0))
    vit_c = max(0.0, float(vitamin_c_mg_100g or 0.0))

    # Positive Points
    fiber_pts = min(20.0, fiber * 2.5)
    protein_pts = min(15.0, protein * 0.6)

    # Micronutrient bonus (up to 5 points)
    ca_pts = min(2.0, (calcium / 300.0) * 2.0)
    fe_pts = min(1.5, (iron / 6.0) * 1.5)
    vit_c_pts = min(1.5, (vit_c / 45.0) * 1.5)
    micro_pts = ca_pts + fe_pts + vit_c_pts

    # Negative Penalties
    sugar_pts = min(20.0, sugar * 0.8)
    sat_fat_pts = min(15.0, sat_fat * 1.5)
    sodium_pts = min(15.0, (sodium / 100.0) * 1.0)

    # Caloric Density Adjustments
    density_penalty = 0.0
    density_bonus = 0.0
    if kcal > 400.0 and fiber < 3.0:
        density_penalty = min(10.0, (kcal - 400.0) / 40.0)
    elif kcal < 60.0 and sugar < 5.0 and (fiber >= 1.5 or vit_c >= 10.0):
        # Whole leafy greens / fresh vegetables reward
        density_bonus = min(10.0, (60.0 - kcal) / 4.0)

    # Compute raw score
    raw_score = (
        50.0
        + (fiber_pts + protein_pts + micro_pts + density_bonus)
        - (sugar_pts + sat_fat_pts + sodium_pts + density_penalty)
    )
    raw_score = max(0.0, min(100.0, raw_score))

    # Blend with Nutri-Score if present
    if nutriscore_grade and str(nutriscore_grade).lower().strip() in NUTRISCORE_MAP:
        grade_val = NUTRISCORE_MAP[str(nutriscore_grade).lower().strip()]
        final_score = (0.6 * raw_score) + (0.4 * grade_val)
    else:
        final_score = raw_score

    return round(float(final_score), 1)


def explain_health_score(
    kcal_100g: float,
    protein_100g: float,
    sat_fat_100g: float,
    sugar_100g: float,
    fiber_100g: float,
    sodium_mg_100g: float,
) -> Dict[str, Any]:
    """Breakdown factors driving a food's health score for UI explanation."""
    positives = []
    negatives = []

    if fiber_100g >= 3.0:
        positives.append(f"High in dietary fiber ({fiber_100g:.1f}g/100g)")
    if protein_100g >= 10.0:
        positives.append(f"Good source of protein ({protein_100g:.1f}g/100g)")
    if sugar_100g <= 5.0 and kcal_100g < 250:
        positives.append("Low in sugar")

    if sugar_100g > 15.0:
        negatives.append(f"High in sugar ({sugar_100g:.1f}g/100g)")
    if sat_fat_100g > 5.0:
        negatives.append(f"High in saturated fat ({sat_fat_100g:.1f}g/100g)")
    if sodium_mg_100g > 600.0:
        negatives.append(f"High sodium ({sodium_mg_100g:.0f}mg/100g)")

    return {
        "positives": positives,
        "negatives": negatives,
    }
