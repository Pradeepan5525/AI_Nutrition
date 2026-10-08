"""Tests targeting remaining branches to push code coverage above 80%."""

import tempfile
from pathlib import Path

from nutri.assess.bmi import get_bmi_category
from nutri.data.loaders import (
    load_raw_allergens,
    load_raw_diet_recommendations,
    load_raw_dietary_restrictions,
    load_raw_obesity,
)
from nutri.features.obesity_features import extract_likely_original_mask
from nutri.foods.food_db import get_food_db
from nutri.reports.pdf import generate_nutrition_pdf, save_nutrition_pdf
from nutri.rules.safety import evaluate_safety_gate


def test_bmi_asian_and_obesity_tiers():
    """Verify all branch conditions in get_bmi_category."""
    # Asian branches
    assert get_bmi_category(17.0, use_asian_cutoffs=True)["category"] == "Underweight"
    assert get_bmi_category(20.0, use_asian_cutoffs=True)["category"] == "Normal weight"
    assert get_bmi_category(24.0, use_asian_cutoffs=True)["category"] == "Overweight"
    assert get_bmi_category(29.0, use_asian_cutoffs=True)["category"] == "Obese"

    # Standard WHO branches
    assert get_bmi_category(17.0, use_asian_cutoffs=False)["category"] == "Underweight"
    assert get_bmi_category(22.0, use_asian_cutoffs=False)["category"] == "Normal weight"
    assert get_bmi_category(27.0, use_asian_cutoffs=False)["category"] == "Overweight"
    assert get_bmi_category(32.0, use_asian_cutoffs=False)["category"] == "Obesity Class I"
    assert get_bmi_category(37.0, use_asian_cutoffs=False)["category"] == "Obesity Class II"
    assert get_bmi_category(42.0, use_asian_cutoffs=False)["category"] == "Obesity Class III"


def test_safety_gate_breastfeeding_and_extremes():
    """Verify breastfeeding and implausible body dimensions."""
    res_bf = evaluate_safety_gate(
        age=30, bmi=22.0, weight_kg=60.0, height_cm=165.0, is_breastfeeding=True
    )
    assert res_bf["withhold_aggressive_targets"] is True

    res_extreme_wt = evaluate_safety_gate(age=30, bmi=22.0, weight_kg=290.0, height_cm=165.0)
    assert res_extreme_wt["safe_for_automated_plan"] is False


def test_pdf_save_and_multi_day_rendering():
    """Verify PDF save helper and full report generation with risk and meal plan."""
    sample_plan = {
        "daily_plans": [
            {
                "day_number": 1,
                "daily_totals": {
                    "kcal": 2000,
                    "protein_g": 120,
                    "carbs_g": 220,
                    "fat_g": 60,
                    "sodium_mg": 1800,
                },
                "meals": {
                    "breakfast": [
                        {
                            "name": "Oatmeal",
                            "portion_g": 80,
                            "kcal": 300,
                            "protein_g": 10,
                            "carbs_g": 50,
                            "fat_g": 5,
                            "sodium_mg": 10,
                        }
                    ],
                    "lunch": [
                        {
                            "name": "Chicken Salad",
                            "portion_g": 200,
                            "kcal": 450,
                            "protein_g": 40,
                            "carbs_g": 20,
                            "fat_g": 15,
                            "sodium_mg": 350,
                        }
                    ],
                    "dinner": [
                        {
                            "name": "Baked Salmon",
                            "portion_g": 180,
                            "kcal": 400,
                            "protein_g": 35,
                            "carbs_g": 10,
                            "fat_g": 20,
                            "sodium_mg": 200,
                        }
                    ],
                    "snack": [
                        {
                            "name": "Almonds",
                            "portion_g": 30,
                            "kcal": 180,
                            "protein_g": 6,
                            "carbs_g": 5,
                            "fat_g": 14,
                            "sodium_mg": 2,
                        }
                    ],
                },
            }
        ]
    }
    sample_grocery = {
        "items_by_department": {
            "Produce": [{"name": "Apples", "total_weight_g": 400}],
            "Meat & Seafood": [{"name": "Salmon", "total_weight_g": 180}],
        }
    }
    bundle = {
        "client_info": {
            "age": 30,
            "sex": "male",
            "height_cm": 175,
            "weight_kg": 75,
            "bmi": 24.5,
            "bmi_category": "Normal weight",
            "bmr": 1700,
            "tdee": 2200,
        },
        "target_nutrition": {
            "target_kcal": 2000,
            "protein_g": 130,
            "carbs_g": 220,
            "fat_g": 65,
            "fiber_g": 30,
            "sugar_g": 40,
            "water_ml": 2500,
        },
        "safety_gate": {"cleared": True, "flags": []},
        "clinical_rules": {"active_rules": ["General Guidelines"]},
        "risk_screening": {
            "predicted_category": "Healthy",
            "probabilities": {
                "Healthy": 0.85,
                "Overweight": 0.10,
                "Obese": 0.03,
                "Underweight": 0.02,
            },
            "top_risks": ["Moderate snack frequency"],
            "top_protective": ["Daily physical activity", "High vegetable consumption"],
        },
        "meal_plan": sample_plan,
        "grocery_list": sample_grocery,
    }

    pdf_bytes = generate_nutrition_pdf(bundle)
    assert len(pdf_bytes) > 2000

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        save_nutrition_pdf(bundle, tmp_path)
        assert Path(tmp_path).exists()
        assert Path(tmp_path).stat().st_size > 2000
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_loaders_and_feature_masks():
    """Verify data loaders and mask generation on existing raw files."""
    ob_df = load_raw_obesity()
    assert len(ob_df) > 1000
    mask = extract_likely_original_mask(ob_df)
    assert mask.sum() > 400

    diet_df = load_raw_diet_recommendations()
    assert len(diet_df) >= 1000

    alg_df = load_raw_allergens()
    assert alg_df is not None

    restr_df = load_raw_dietary_restrictions()
    assert restr_df is not None


def test_food_db_cached_and_unique_queries():
    """Verify FoodDatabase methods."""
    db = get_food_db()
    cats = db.get_unique_categories()
    assert len(cats) >= 5
    types_ = db.get_unique_food_types()
    assert len(types_) >= 3
    assert db.get_total_count() > 30000
