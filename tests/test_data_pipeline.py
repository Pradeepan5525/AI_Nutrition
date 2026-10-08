"""Unit and contract tests for data engineering pipeline."""

import numpy as np
import pandas as pd
import pytest

from nutri.config import FOODS_PARQUET
from nutri.data.cleaners import (
    check_physical_plausibility,
    deduplicate_usda_foods,
    fix_healthy_foods_sodium_unit_errors,
    impute_secondary_nutrients,
    normalize_food_name,
)
from nutri.data.loaders import (
    RawDietRow,
    RawObesityRow,
    load_raw_diet_recommendations,
    load_raw_obesity,
    validate_dataframe_schema,
)


def test_obesity_schema_validation():
    """Verify raw obesity dataset passes Pydantic schema validation."""
    df = load_raw_obesity()
    assert len(df) == 2111
    assert "NObeyesdad" in df.columns
    assert validate_dataframe_schema(df, RawObesityRow, sample_size=20) is True


def test_diet_recommendations_schema_validation():
    """Verify raw diet recommendations dataset passes Pydantic schema validation."""
    df = load_raw_diet_recommendations()
    assert len(df) == 1000
    assert "Diet_Recommendation" in df.columns
    assert validate_dataframe_schema(df, RawDietRow, sample_size=20) is True


def test_normalize_food_name():
    """Verify normalization of food name strings."""
    assert normalize_food_name("  Apple, Raw (Red Delicious)! ") == "apple, raw red delicious"
    assert normalize_food_name("CHICKEN BREAST - Cooked") == "chicken breast cooked"
    assert normalize_food_name("") == ""


def test_physical_plausibility_valid():
    """Test that standard valid food record passes plausibility."""
    valid_food = pd.Series(
        {
            "kcal_100g": 165.0,
            "protein_100g": 31.0,
            "fat_100g": 3.6,
            "sat_fat_100g": 1.0,
            "carbs_100g": 0.0,
            "sugar_100g": 0.0,
            "sodium_mg_100g": 74.0,
        }
    )
    ok, reason = check_physical_plausibility(valid_food)
    assert ok is True
    assert reason is None


def test_physical_plausibility_violations():
    """Test detection of invalid physical bounds."""
    # Negative calories
    neg = pd.Series({"kcal_100g": -50.0, "protein_100g": 10.0, "fat_100g": 2.0, "carbs_100g": 5.0})
    ok, reason = check_physical_plausibility(neg)
    assert ok is False
    assert "Negative value" in reason

    # Calories > 900
    super_kcal = pd.Series(
        {"kcal_100g": 950.0, "protein_100g": 10.0, "fat_100g": 2.0, "carbs_100g": 5.0}
    )
    ok, reason = check_physical_plausibility(super_kcal)
    assert ok is False
    assert "out of range" in reason

    # Macros sum > 105g
    macro_overflow = pd.Series(
        {"kcal_100g": 500.0, "protein_100g": 60.0, "fat_100g": 30.0, "carbs_100g": 40.0}
    )
    ok, reason = check_physical_plausibility(macro_overflow)
    assert ok is False
    assert "Macros sum exceeds" in reason

    # Saturated fat > total fat
    sat_overflow = pd.Series(
        {
            "kcal_100g": 200.0,
            "protein_100g": 10.0,
            "fat_100g": 5.0,
            "sat_fat_100g": 8.0,
            "carbs_100g": 10.0,
        }
    )
    ok, reason = check_physical_plausibility(sat_overflow)
    assert ok is False
    assert "Saturated fat" in reason


def test_fix_healthy_foods_sodium_unit_errors():
    """Test detection and fix of fractional sodium in grams."""
    sample_hf = pd.DataFrame(
        [
            {"food_name": "Almond butter, creamy", "sodium_mg": 0.996},
            {"food_name": "Table salt", "sodium_mg": 1000000.0},
            {"food_name": "Raw Apple", "sodium_mg": 1.0},
        ]
    )
    fixed_df, logs = fix_healthy_foods_sodium_unit_errors(sample_hf)
    # Almond butter 0.996g converted to 996mg
    assert fixed_df.loc[0, "sodium_mg"] == 996.0
    # Table salt set to NaN due to absurd extreme
    assert pd.isna(fixed_df.loc[1, "sodium_mg"])
    # Raw Apple (integer 1.0) preserved
    assert fixed_df.loc[2, "sodium_mg"] == 1.0
    assert len(logs) == 2


def test_usda_deduplication():
    """Test deduplication hierarchy prioritizing Foundation over Branded."""
    usda_mock = pd.DataFrame(
        [
            {
                "fdc_id": 1,
                "food_name": "Broccoli, raw",
                "data_type": "Branded",
                "saturated_fat_g": 0.1,
                "sugar_g": 1.5,
                "fiber_g": np.nan,
                "sodium_mg": 30.0,
                "calcium_mg": np.nan,
                "iron_mg": np.nan,
                "vitamin_c_mg": np.nan,
                "cholesterol_mg": np.nan,
            },
            {
                "fdc_id": 2,
                "food_name": "Broccoli, raw",
                "data_type": "Foundation",
                "saturated_fat_g": 0.05,
                "sugar_g": 1.4,
                "fiber_g": 2.6,
                "sodium_mg": 33.0,
                "calcium_mg": 47.0,
                "iron_mg": 0.7,
                "vitamin_c_mg": 89.2,
                "cholesterol_mg": 0.0,
            },
        ]
    )
    deduped, dropped = deduplicate_usda_foods(usda_mock)
    assert dropped == 1
    assert len(deduped) == 1
    assert deduped.iloc[0]["data_type"] == "Foundation"
    assert deduped.iloc[0]["fdc_id"] == 2


def test_impute_secondary_nutrients():
    """Test category-based median imputation with tracking flags."""
    df = pd.DataFrame(
        [
            {"category": "Vegetables", "fiber_100g": 3.0, "sugar_100g": np.nan},
            {"category": "Vegetables", "fiber_100g": 5.0, "sugar_100g": 2.0},
            {"category": "Fruits", "fiber_100g": np.nan, "sugar_100g": 12.0},
        ]
    )
    imputed = impute_secondary_nutrients(df, category_col="category")
    assert imputed.loc[0, "sugar_100g"] == 2.0
    assert bool(imputed.loc[0, "sugar_imputed"]) is True
    assert bool(imputed.loc[1, "sugar_imputed"]) is False
    assert "fiber_imputed" in imputed.columns


def test_processed_foods_parquet_contracts():
    """Contract tests verifying the harmonized foods parquet artifact."""
    if not FOODS_PARQUET.exists():
        pytest.skip("foods.parquet not generated yet")

    df = pd.read_parquet(FOODS_PARQUET)
    assert len(df) > 10000
    # No negative values for macronutrients
    for col in ["kcal_100g", "protein_100g", "fat_100g", "carbs_100g"]:
        assert (df[col] >= 0.0).all(), f"Found negative values in {col}"

    # Physical plausibility
    macro_sum = df["protein_100g"] + df["fat_100g"] + df["carbs_100g"]
    assert (macro_sum <= 105.0).all(), "Found macro sum exceeding 105g/100g"

    # Health score range [0, 100]
    assert (df["health_score_v2"] >= 0.0).all()
    assert (df["health_score_v2"] <= 100.0).all()

    # Required columns present
    req_cols = [
        "food_id",
        "name",
        "source",
        "category",
        "food_type",
        "kcal_100g",
        "protein_100g",
        "fat_100g",
        "carbs_100g",
        "allergen_flags",
        "health_score_v2",
    ]
    for c in req_cols:
        assert c in df.columns


def test_map_category():
    """Test mapping of raw descriptions to standard categories and food types."""
    from nutri.data.harmonizer import map_category

    cat, ftype = map_category("Fresh spinach leaves", "Baby Spinach")
    assert cat == "Vegetables"
    assert ftype == "Vegetables"

    cat, ftype = map_category("Fresh Salmon Fillet", "Atlantic Salmon")
    assert cat == "Fish & Seafood"
    assert ftype == "Proteins"

    cat, ftype = map_category("Greek Whole Milk Yogurt", "Dairy")
    assert cat == "Dairy & Egg"
    assert ftype == "Dairy"


def test_determine_dietary_restrictions():
    """Test determination of dietary tags (vegan, vegetarian, low sodium, etc.)."""
    from nutri.data.allergens import ALLERGEN_ABSENT
    from nutri.data.harmonizer import determine_dietary_restrictions

    vegan_allergens = {
        "gluten": ALLERGEN_ABSENT,
        "dairy": ALLERGEN_ABSENT,
        "eggs": ALLERGEN_ABSENT,
        "fish": ALLERGEN_ABSENT,
        "nuts": ALLERGEN_ABSENT,
        "peanuts": ALLERGEN_ABSENT,
        "soy": ALLERGEN_ABSENT,
    }
    tags = determine_dietary_restrictions(
        category="Vegetables",
        food_name="Steamed Broccoli Florets",
        allergens=vegan_allergens,
        sodium_mg=30.0,
        sugar_g=1.5,
    )
    assert "vegetarian" in tags
    assert "vegan" in tags
    assert "gluten_free" in tags
    assert "dairy_free" in tags
    assert "low_sodium" in tags
    assert "low_sugar" in tags

    meat_allergens = dict.fromkeys(vegan_allergens, ALLERGEN_ABSENT)
    meat_tags = determine_dietary_restrictions(
        category="Meat & Poultry",
        food_name="Grilled Chicken Breast",
        allergens=meat_allergens,
        sodium_mg=250.0,
        sugar_g=0.0,
    )
    assert "vegetarian" not in meat_tags
    assert "vegan" not in meat_tags
    assert "gluten_free" in meat_tags
