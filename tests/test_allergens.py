"""Tests for tri-state allergen detection and safety filtering."""

import pytest

from nutri.data.allergens import (
    ALLERGEN_ABSENT,
    ALLERGEN_PRESENT,
    ALLERGEN_UNKNOWN,
    detect_allergen_tri_state,
    is_food_safe_for_allergies,
    parse_allergen_json,
)


@pytest.mark.parametrize(
    "food_name,ingredients,expected_allergen",
    [
        ("Whole Wheat Sourdough Bread", "wheat flour, water, yeast, salt", "gluten"),
        ("Greek Yogurt Whole Milk", "pasteurized whole milk, live active cultures", "dairy"),
        ("Creamy Almond Butter", "roasted almonds, salt", "nuts"),
        ("Crunchy Peanut Butter", "peanuts, salt", "peanuts"),
        ("Organic Firm Tofu", "water, soybeans, calcium sulfate", "soy"),
        ("Cage Free Scrambled Eggs", "whole eggs, salt", "eggs"),
        ("Atlantic Salmon Fillet", "wild caught salmon", "fish"),
    ],
)
def test_allergen_keyword_positive_detection(food_name, ingredients, expected_allergen):
    """Test that all 7 allergens are accurately detected as present via keywords."""
    res = detect_allergen_tri_state(food_name, ingredients=ingredients)
    assert res[expected_allergen] == ALLERGEN_PRESENT


def test_allergen_tri_state_unknown_for_unverified():
    """Test that missing ingredients for processed food yields 'unknown', never 'absent'."""
    res = detect_allergen_tri_state(
        food_name="Generic Mystery Protein Bar",
        ingredients=None,
        is_packaged=True,
    )
    # None of the allergens should be assumed absent!
    for _allergen, status in res.items():
        assert status == ALLERGEN_UNKNOWN


def test_allergen_tri_state_absent_for_verified_foundation_food():
    """Test that single-ingredient whole foods (e.g. raw apple) have non-allergens marked absent."""
    res = detect_allergen_tri_state(
        food_name="Apple, raw, with skin",
        ingredients="",
        is_foundation_raw=True,
    )
    assert res["gluten"] == ALLERGEN_ABSENT
    assert res["dairy"] == ALLERGEN_ABSENT
    assert res["nuts"] == ALLERGEN_ABSENT
    assert res["peanuts"] == ALLERGEN_ABSENT
    assert res["fish"] == ALLERGEN_ABSENT


def test_is_food_safe_for_allergies_strict_vs_lenient():
    """Verify allergen safety gate behavior with strict vs lenient settings."""
    flags = {
        "gluten": ALLERGEN_ABSENT,
        "dairy": ALLERGEN_UNKNOWN,
        "peanuts": ALLERGEN_PRESENT,
        "nuts": ALLERGEN_ABSENT,
        "soy": ALLERGEN_ABSENT,
        "eggs": ALLERGEN_ABSENT,
        "fish": ALLERGEN_ABSENT,
    }

    # Peanut allergy: present -> unsafe under both
    assert is_food_safe_for_allergies(flags, ["peanuts"], strict=True) is False
    assert is_food_safe_for_allergies(flags, ["peanuts"], strict=False) is False

    # Gluten allergy: absent -> safe under both
    assert is_food_safe_for_allergies(flags, ["gluten"], strict=True) is True
    assert is_food_safe_for_allergies(flags, ["gluten"], strict=False) is True

    # Dairy allergy: unknown -> unsafe under strict, safe under lenient
    assert is_food_safe_for_allergies(flags, ["dairy"], strict=True) is False
    assert is_food_safe_for_allergies(flags, ["dairy"], strict=False) is True


def test_parse_allergen_json():
    """Test JSON parsing round-trip for allergen flags."""
    json_str = '{"gluten": "absent", "dairy": "present"}'
    parsed = parse_allergen_json(json_str)
    assert parsed["gluten"] == "absent"
    assert parsed["dairy"] == "present"

    invalid_parsed = parse_allergen_json("invalid json string")
    assert invalid_parsed["gluten"] == ALLERGEN_UNKNOWN
