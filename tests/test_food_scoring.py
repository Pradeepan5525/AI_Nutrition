"""Tests for transparent Health Score v2 calculation."""

from nutri.foods.scoring import calculate_health_score_v2, explain_health_score


def test_health_score_fruits_vegetables_outrank_candy():
    """Verify core requirement: fruits and vegetables outrank candy and fried snacks."""
    # Spinach / Broccoli (nutrient-dense, high fiber, low sugar, low sodium)
    spinach_score = calculate_health_score_v2(
        kcal_100g=23.0,
        protein_100g=2.9,
        fat_100g=0.4,
        sat_fat_100g=0.1,
        carbs_100g=3.6,
        sugar_100g=0.4,
        fiber_100g=2.2,
        sodium_mg_100g=79.0,
        calcium_mg_100g=99.0,
        iron_mg_100g=2.7,
        vitamin_c_mg_100g=28.1,
    )

    broccoli_score = calculate_health_score_v2(
        kcal_100g=34.0,
        protein_100g=2.8,
        fat_100g=0.4,
        sat_fat_100g=0.1,
        carbs_100g=6.6,
        sugar_100g=1.7,
        fiber_100g=2.6,
        sodium_mg_100g=33.0,
        calcium_mg_100g=47.0,
        iron_mg_100g=0.7,
        vitamin_c_mg_100g=89.2,
    )

    apple_score = calculate_health_score_v2(
        kcal_100g=52.0,
        protein_100g=0.3,
        fat_100g=0.2,
        sat_fat_100g=0.0,
        carbs_100g=13.8,
        sugar_100g=10.4,
        fiber_100g=2.4,
        sodium_mg_100g=1.0,
    )

    # Candy / Potato Chips / Milk Chocolate
    candy_score = calculate_health_score_v2(
        kcal_100g=387.0,
        protein_100g=0.0,
        fat_100g=0.2,
        sat_fat_100g=0.0,
        carbs_100g=96.0,
        sugar_100g=75.0,
        fiber_100g=0.0,
        sodium_mg_100g=38.0,
    )

    potato_chips_score = calculate_health_score_v2(
        kcal_100g=536.0,
        protein_100g=7.0,
        fat_100g=34.6,
        sat_fat_100g=11.0,
        carbs_100g=53.0,
        sugar_100g=0.5,
        fiber_100g=3.0,
        sodium_mg_100g=525.0,
    )

    milk_chocolate_score = calculate_health_score_v2(
        kcal_100g=535.0,
        protein_100g=7.6,
        fat_100g=29.7,
        sat_fat_100g=18.5,
        carbs_100g=59.4,
        sugar_100g=51.5,
        fiber_100g=3.4,
        sodium_mg_100g=79.0,
    )

    # Assertions
    assert spinach_score > 60.0
    assert broccoli_score > 60.0
    assert apple_score > 45.0

    assert candy_score < 35.0
    assert potato_chips_score < 45.0
    assert milk_chocolate_score < 30.0

    # Fruits & Veggies decisively beat Candy & Fried snacks
    assert spinach_score > candy_score
    assert broccoli_score > potato_chips_score
    assert apple_score > milk_chocolate_score


def test_health_score_bounds():
    """Verify health score is always strictly bounded [0.0, 100.0]."""
    # Extreme junk food
    extreme_bad = calculate_health_score_v2(
        kcal_100g=800.0,
        protein_100g=0.0,
        fat_100g=70.0,
        sat_fat_100g=50.0,
        carbs_100g=90.0,
        sugar_100g=90.0,
        fiber_100g=0.0,
        sodium_mg_100g=5000.0,
    )
    assert extreme_bad >= 0.0

    # Extreme superfood
    extreme_good = calculate_health_score_v2(
        kcal_100g=100.0,
        protein_100g=25.0,
        fat_100g=1.0,
        sat_fat_100g=0.0,
        carbs_100g=10.0,
        sugar_100g=0.0,
        fiber_100g=10.0,
        sodium_mg_100g=20.0,
        calcium_mg_100g=500.0,
        iron_mg_100g=10.0,
        vitamin_c_mg_100g=100.0,
        nutriscore_grade="a",
    )
    assert extreme_good <= 100.0


def test_explain_health_score():
    """Verify explanation breakdown highlights key positive and negative nutrient attributes."""
    exp = explain_health_score(
        kcal_100g=150.0,
        protein_100g=14.0,
        sat_fat_100g=6.0,
        sugar_100g=18.0,
        fiber_100g=4.0,
        sodium_mg_100g=750.0,
    )
    assert any("protein" in p.lower() for p in exp["positives"])
    assert any("fiber" in p.lower() for p in exp["positives"])
    assert any("sugar" in n.lower() for n in exp["negatives"])
    assert any("sodium" in n.lower() for n in exp["negatives"])
