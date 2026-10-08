"""Unit tests for deterministic health assessment engine with hand-computed test cases."""

import pytest

from nutri.assess.bmi import calculate_bmi, calculate_ideal_weight_range, get_bmi_category
from nutri.assess.energy import calculate_bmr_mifflin_st_jeor, calculate_tdee
from nutri.assess.targets import calculate_nutrient_targets
from nutri.rules.safety import evaluate_safety_gate


def test_calculate_bmi_hand_computed():
    """Verify BMI against hand-computed values."""
    # 70 kg, 175 cm -> 70 / (1.75^2) = 22.857 -> 22.86
    bmi1 = calculate_bmi(70.0, 175.0)
    assert bmi1 == 22.86

    # 90 kg, 170 cm -> 90 / (1.70^2) = 31.141 -> 31.14
    bmi2 = calculate_bmi(90.0, 170.0)
    assert bmi2 == 31.14

    with pytest.raises(ValueError):
        calculate_bmi(-70.0, 175.0)


def test_get_bmi_category_who_vs_asian():
    """Verify WHO cut-offs and Asian-specific cut-offs."""
    # BMI 24.0: Normal in WHO (<24.9), Overweight in Asian (>22.9)
    who_res = get_bmi_category(24.0, use_asian_cutoffs=False)
    assert who_res["category"] == "Normal weight"

    asian_res = get_bmi_category(24.0, use_asian_cutoffs=True)
    assert asian_res["category"] == "Overweight"

    # Underweight check
    under_res = get_bmi_category(17.5)
    assert under_res["category"] == "Underweight"

    # Severe Obesity check
    obese_res = get_bmi_category(42.0)
    assert obese_res["category"] == "Obesity Class III"


def test_calculate_ideal_weight_range():
    """Verify healthy weight range bounds for height."""
    # Height 175 cm (1.75 m):
    # min: 18.5 * (1.75^2) = 56.656 -> 56.7 kg
    # max: 24.9 * (1.75^2) = 76.256 -> 76.3 kg
    min_w, max_w = calculate_ideal_weight_range(175.0, use_asian_cutoffs=False)
    assert min_w == 56.7
    assert max_w == 76.3


def test_calculate_bmr_mifflin_st_jeor_hand_computed():
    """Verify BMR against hand-computed formula values."""
    # Male: 75 kg, 180 cm, 30 yo
    # 10*75 + 6.25*180 - 5*30 + 5 = 750 + 1125 - 150 + 5 = 1730.0 kcal
    bmr_m = calculate_bmr_mifflin_st_jeor(75.0, 180.0, 30, "male")
    assert bmr_m == 1730.0

    # Female: 60 kg, 165 cm, 25 yo
    # 10*60 + 6.25*165 - 5*25 - 161 = 600 + 1031.25 - 125 - 161 = 1345.25 -> 1345.2 or 1345.3
    bmr_f = calculate_bmr_mifflin_st_jeor(60.0, 165.0, 25, "female")
    assert abs(bmr_f - 1345.25) < 0.1


def test_calculate_tdee_multipliers():
    """Verify TDEE activity multipliers."""
    bmr = 1730.0
    # Sedentary (1.2) -> 2076.0
    assert calculate_tdee(bmr, "sedentary") == 2076.0
    # Moderate (1.55) -> 2681.5
    assert calculate_tdee(bmr, "moderate") == 2681.5
    # Active (1.725) -> 2984.2 or 2984.3
    assert abs(calculate_tdee(bmr, "active") - 2984.25) < 0.1


def test_calorie_floor_protection_female():
    """Verify safety floor clamps aggressive deficits for women to 1,200 kcal."""
    # Sedentary low-weight woman with TDEE 1400 kcal wanting to lose 0.5 kg/week (-550 kcal)
    # Raw target would be 850 kcal (dangerously low!)
    targets = calculate_nutrient_targets(
        tdee=1400.0,
        weight_kg=50.0,
        sex="female",
        goal="lose",
        rate_kg_per_week=0.5,
    )
    assert targets["calorie_floor_applied"] is True
    assert targets["target_kcal"] == 1200
    assert targets["raw_calculated_kcal"] == 850


def test_calorie_floor_protection_male():
    """Verify safety floor clamps aggressive deficits for men to 1,500 kcal."""
    targets = calculate_nutrient_targets(
        tdee=1800.0,
        weight_kg=65.0,
        sex="male",
        goal="lose",
        rate_kg_per_week=0.5,
    )
    assert targets["calorie_floor_applied"] is True
    assert targets["target_kcal"] == 1500
    assert targets["raw_calculated_kcal"] == 1250


def test_macronutrient_distribution_and_guidelines():
    """Verify macro targets, fiber (14g/1000kcal), sugar (<10%), and water."""
    targets = calculate_nutrient_targets(
        tdee=2600.0,
        weight_kg=80.0,
        sex="male",
        goal="maintain",
    )
    assert targets["target_kcal"] == 2600
    # Protein: 1.0 g/kg for maintain -> 80.0 g (320 kcal)
    assert targets["macros"]["protein_g"] == 80.0
    # Fiber: (2600 / 1000) * 14 = 36.4 g
    assert targets["micros_and_guidance"]["fiber_g"] == 36.4
    # Max sugar: 2600 * 0.10 / 4 = 65.0 g
    assert targets["micros_and_guidance"]["max_added_sugar_g"] == 65.0
    # Water: 80 * 35 = 2800 ml = 2.8 L
    assert targets["micros_and_guidance"]["daily_water_ml"] == 2800
    assert targets["micros_and_guidance"]["daily_water_liters"] == 2.8


def test_safety_gate_minors_and_seniors():
    """Verify safety gate flags age boundaries."""
    # Minor: age 16
    minor_eval = evaluate_safety_gate(age=16, bmi=21.0, weight_kg=55.0, height_cm=165.0)
    assert minor_eval["safe_for_automated_plan"] is False
    assert minor_eval["withhold_aggressive_targets"] is True
    assert any("Minors" in b for b in minor_eval["blockers"])

    # Senior: age 78
    senior_eval = evaluate_safety_gate(age=78, bmi=24.0, weight_kg=68.0, height_cm=168.0)
    assert senior_eval["withhold_aggressive_targets"] is True
    assert any("75 years" in a for a in senior_eval["advisories"])


def test_safety_gate_pregnancy_and_eating_disorder():
    """Verify safety gate blocks restrictive targets for pregnancy and eating disorder history."""
    preg_eval = evaluate_safety_gate(
        age=28, bmi=23.0, weight_kg=62.0, height_cm=164.0, is_pregnant=True
    )
    assert preg_eval["safe_for_automated_plan"] is False
    assert any("pregnancy" in b.lower() for b in preg_eval["blockers"])

    ed_eval = evaluate_safety_gate(
        age=24, bmi=20.0, weight_kg=58.0, height_cm=170.0, eating_disorder_history=True
    )
    assert ed_eval["safe_for_automated_plan"] is False
    assert any("eating disorders" in b.lower() for b in ed_eval["blockers"])


def test_safety_gate_extreme_bmi():
    """Verify safety gate catches severe underweight (<16) and severe obesity (>45)."""
    # BMI 15.0
    under_eval = evaluate_safety_gate(age=25, bmi=15.0, weight_kg=40.0, height_cm=163.0)
    assert under_eval["safe_for_automated_plan"] is False
    assert any("underweight" in b.lower() for b in under_eval["blockers"])

    # BMI 48.0
    obese_eval = evaluate_safety_gate(age=40, bmi=48.0, weight_kg=140.0, height_cm=170.0)
    assert obese_eval["withhold_aggressive_targets"] is True
    assert any("obesity" in a.lower() for a in obese_eval["advisories"])
