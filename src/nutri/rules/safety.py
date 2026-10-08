"""Clinical Safety Gate protecting vulnerable populations and extreme physiological states."""

from typing import Any, Dict, List

DISCLAIMER_TEXT = (
    "EDUCATIONAL AND SCREENING USE ONLY. This system does not diagnose medical "
    "conditions, prescribe treatments, or replace professional medical advice. Always "
    "consult a licensed physician or registered dietitian before making significant dietary changes."
)


def evaluate_safety_gate(
    age: int,
    bmi: float,
    weight_kg: float,
    height_cm: float,
    is_pregnant: bool = False,
    is_breastfeeding: bool = False,
    eating_disorder_history: bool = False,
    goal: str = "maintain",
) -> Dict[str, Any]:
    """Evaluate patient health safety gate to protect vulnerable populations.

    Safety Conditions Monitored:
    1. Minors (age < 18): Restrictive diets withheld to protect growth.
    2. Elderly (age > 75): Geriatric oversight recommended.
    3. Pregnancy / Lactation: Elevated micronutrient needs; deficits withheld.
    4. Eating Disorder History: Weight tracking and caloric restriction blocked.
    5. Extreme BMI (< 16.0 or > 45.0): High clinical risk requiring physician oversight.
    6. Extreme Physiological Values: Height/weight input plausibility checks.

    Returns:
        Dict with status, warnings, plan permission flags, and medical disclaimer.
    """
    blockers: List[str] = []
    advisories: List[str] = []
    withhold_aggressive_plan = False
    block_automated_plan = False

    # 1. Minors check
    if age < 18:
        msg = "Minors (< 18 years) require specialized pediatric nutritional guidance. Automated caloric restriction is withheld."
        blockers.append(msg)
        withhold_aggressive_plan = True
        block_automated_plan = True

    # 2. Elderly check
    elif age > 75:
        advisories.append(
            "Senior / Elderly: Individuals over 75 years of age should consult a geriatric healthcare professional before modifying caloric intake."
        )
        withhold_aggressive_plan = True

    # 3. Pregnancy / Lactation
    if is_pregnant:
        msg = "Caloric deficits and unmonitored diet changes during pregnancy can impair fetal development. Automated meal plans are withheld."
        blockers.append(msg)
        withhold_aggressive_plan = True
        block_automated_plan = True
    elif is_breastfeeding:
        advisories.append(
            "Lactation increases caloric and hydration demands. Calorie deficits should only be implemented under clinical supervision."
        )
        withhold_aggressive_plan = True

    # 4. Eating Disorder History
    if eating_disorder_history:
        msg = "Caloric restriction and rigid macro tracking are strongly contraindicated for individuals with a history of eating disorders. Please consult a specialized healthcare provider."
        blockers.append(msg)
        withhold_aggressive_plan = True
        block_automated_plan = True

    # 5. Extreme BMI checks
    if bmi < 16.0:
        msg = f"Severe underweight detected (BMI {bmi:.1f} < 16.0). Immediate medical evaluation for malnutrition or underlying illness is advised."
        blockers.append(msg)
        withhold_aggressive_plan = True
        block_automated_plan = True
    elif bmi > 45.0:
        advisories.append(
            f"Severe obesity detected (BMI {bmi:.1f} > 45.0). Medically supervised multidisciplinary management is recommended."
        )
        withhold_aggressive_plan = True

    # 6. Biologically implausible values
    if weight_kg < 30.0 or weight_kg > 250.0 or height_cm < 120.0 or height_cm > 240.0:
        msg = "Entered body measurements fall outside standard adult physiological ranges. Please verify your entries."
        blockers.append(msg)
        block_automated_plan = True

    # In case of active blockers with weight loss goal, suppress deficit
    safe_for_automated_plan = not block_automated_plan
    allowed_goal = "maintain" if withhold_aggressive_plan else goal.lower()

    return {
        "safe_for_automated_plan": safe_for_automated_plan,
        "withhold_aggressive_targets": withhold_aggressive_plan,
        "allowed_goal": allowed_goal,
        "blockers": blockers,
        "advisories": advisories,
        "has_warnings": bool(blockers or advisories),
        "disclaimer": DISCLAIMER_TEXT,
    }
