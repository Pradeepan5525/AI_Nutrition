"""Unit tests for condition-aware clinical rules engine and conflict resolution."""

import pytest

from nutri.rules.conditions import (
    register_custom_condition_rule,
    resolve_clinical_rules,
)


@pytest.fixture
def base_targets_2000():
    """Standard baseline targets fixture for 2000 kcal diet."""
    return {
        "target_kcal": 2000.0,
        "macros": {
            "protein_g": 70.0,
            "protein_kcal": 280,
            "fat_g": 62.2,
            "fat_kcal": 560,
            "carbs_g": 290.0,
            "carbs_kcal": 1160,
        },
        "micros_and_guidance": {
            "fiber_g": 28.0,
            "max_added_sugar_g": 50.0,
            "max_sodium_mg": 2300.0,
            "daily_water_ml": 2500,
            "daily_water_liters": 2.5,
        },
    }


def test_positive_hypertension_rule(base_targets_2000):
    """Verify Hypertension applies AHA DASH sodium cap (1,500 mg)."""
    res = resolve_clinical_rules(
        active_conditions=["Hypertension"],
        active_restrictions=[],
        base_targets=base_targets_2000,
        weight_kg=70.0,
    )
    targets = res["adjusted_targets"]
    audit = res["audit_trail"]

    assert targets["micros_and_guidance"]["max_sodium_mg"] == 1500.0
    assert audit["max_sodium_mg"]["final_value"] == 1500.0
    assert "Hypertension" in audit["max_sodium_mg"]["ruling_condition"]
    assert "AHA" in audit["max_sodium_mg"]["citation"]
    assert len(res["clinical_guidance"]) >= 1


def test_positive_diabetes_rule(base_targets_2000):
    """Verify Diabetes applies ADA sugar limit (5% kcal) and high-fiber target."""
    res = resolve_clinical_rules(
        active_conditions=["Diabetes"],
        active_restrictions=[],
        base_targets=base_targets_2000,
        weight_kg=70.0,
    )
    targets = res["adjusted_targets"]
    audit = res["audit_trail"]

    # 2000 kcal * 5% = 100 kcal = 25 g sugar
    assert targets["micros_and_guidance"]["max_added_sugar_g"] == 25.0
    # 2000 kcal * 18g/1000kcal = 36 g fiber
    assert targets["micros_and_guidance"]["fiber_g"] == 36.0
    assert "Diabetes" in audit["max_added_sugar_g"]["ruling_condition"]
    assert "Diabetes" in audit["fiber_g"]["ruling_condition"]


def test_positive_high_cholesterol_rule(base_targets_2000):
    """Verify Hypercholesterolemia caps saturated fat to 7% and cholesterol to 200 mg."""
    res = resolve_clinical_rules(
        active_conditions=["high_cholesterol"],
        active_restrictions=[],
        base_targets=base_targets_2000,
        weight_kg=70.0,
    )
    targets = res["adjusted_targets"]
    audit = res["audit_trail"]

    # 2000 kcal * 7% = 140 kcal = 15.6 g sat fat
    assert targets["micros_and_guidance"]["max_sat_fat_g"] == 15.6
    assert targets["micros_and_guidance"]["max_cholesterol_mg"] == 200.0
    assert "cholesterol" in audit["max_sat_fat_g"]["ruling_condition"].lower()


def test_positive_obesity_rule(base_targets_2000):
    """Verify Obesity rule elevates protein to 1.4 g/kg for satiety and lean mass."""
    res = resolve_clinical_rules(
        active_conditions=["obesity"],
        active_restrictions=[],
        base_targets=base_targets_2000,
        weight_kg=80.0,
    )
    targets = res["adjusted_targets"]
    audit = res["audit_trail"]

    # 80 kg * 1.4 = 112.0 g protein
    assert targets["macros"]["protein_g"] == 112.0
    assert "Obesity" in audit["protein_g"]["ruling_condition"]


def test_negative_cases_no_active_conditions(base_targets_2000):
    """Verify baseline limits remain untouched when no condition is active."""
    res = resolve_clinical_rules(
        active_conditions=[],
        active_restrictions=[],
        base_targets=base_targets_2000,
        weight_kg=70.0,
    )
    targets = res["adjusted_targets"]
    audit = res["audit_trail"]

    assert targets["micros_and_guidance"]["max_sodium_mg"] == 2300.0
    assert targets["micros_and_guidance"]["fiber_g"] == 28.0
    assert targets["micros_and_guidance"]["max_added_sugar_g"] == 50.0
    assert "General" in audit["max_sodium_mg"]["ruling_condition"]
    assert len(res["clinical_guidance"]) == 0


def test_conflict_resolution_hypertension_and_diabetes(base_targets_2000):
    """Verify multi-condition co-morbidity resolves to strictest bounds with exact attribution."""
    res = resolve_clinical_rules(
        active_conditions=["Hypertension", "Diabetes"],
        active_restrictions=[],
        base_targets=base_targets_2000,
        weight_kg=70.0,
    )
    targets = res["adjusted_targets"]
    audit = res["audit_trail"]

    # Sodium capped at 1500 mg (ruled by Hypertension)
    assert targets["micros_and_guidance"]["max_sodium_mg"] == 1500.0
    assert "Hypertension" in audit["max_sodium_mg"]["ruling_condition"]

    # Sugar capped at 25 g (ruled by Diabetes)
    assert targets["micros_and_guidance"]["max_added_sugar_g"] == 25.0
    assert "Diabetes" in audit["max_added_sugar_g"]["ruling_condition"]

    # Fiber target raised to 36 g (ruled by Diabetes)
    assert targets["micros_and_guidance"]["fiber_g"] == 36.0
    assert "Diabetes" in audit["fiber_g"]["ruling_condition"]


def test_extension_point_custom_rule(base_targets_2000):
    """Verify dynamic extension point allows adding new clinical conditions."""
    custom_rule = {
        "name": "Chronic Kidney Disease Stage 3",
        "citation": "KDOQI Clinical Practice Guideline (2020)",
        "constraints": {
            "max_sodium_mg": {"value": 1800.0, "reason": "Fluid balance."},
        },
        "guidance": ["Monitor protein and potassium intake."],
    }
    register_custom_condition_rule("ckd_stage_3", custom_rule)

    res = resolve_clinical_rules(
        active_conditions=["ckd_stage_3"],
        active_restrictions=[],
        base_targets=base_targets_2000,
        weight_kg=70.0,
    )
    assert res["adjusted_targets"]["micros_and_guidance"]["max_sodium_mg"] == 1800.0
    assert (
        "CKD" in res["audit_trail"]["max_sodium_mg"]["ruling_condition"]
        or "Chronic Kidney" in res["audit_trail"]["max_sodium_mg"]["ruling_condition"]
    )
