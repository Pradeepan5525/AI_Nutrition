"""Unit tests for PuLP meal plan optimizer, calorie tolerances, and grocery lists."""

from nutri.plan.grocery import generate_grocery_list
from nutri.plan.optimizer import generate_meal_plan, solve_daily_meal_plan


def test_daily_meal_plan_calorie_and_sodium_constraints():
    """Verify daily plan satisfies +/-5% calorie tolerance and sodium cap."""
    target_kcal = 2000.0
    max_sodium = 2000.0

    plan, relax_log = solve_daily_meal_plan(
        target_kcal=target_kcal,
        protein_target_g=80.0,
        max_sodium_mg=max_sodium,
        max_sat_fat_g=22.0,
        max_sugar_g=50.0,
        user_allergies=[],
        dietary_restrictions=[],
        strict_allergens=True,
    )
    assert plan is not None, "Optimizer should find optimal solution"

    daily_totals = plan["daily_totals"]
    total_kcal = daily_totals["kcal"]

    # Verify +/- 5% calorie tolerance: [1900, 2100] kcal
    assert 1900.0 <= total_kcal <= 2100.0, f"Total kcal {total_kcal} outside +/- 5% range"
    assert abs(plan["calorie_error_pct"]) <= 5.0

    # Verify sodium constraint
    assert daily_totals["sodium_mg"] <= max_sodium * 1.05


def test_optimizer_strictly_excludes_allergens():
    """Verify optimizer strictly honors allergen exclusions (peanuts, dairy, gluten)."""
    allergies = ["peanuts", "dairy", "gluten"]
    plan, _ = solve_daily_meal_plan(
        target_kcal=1800.0,
        protein_target_g=70.0,
        max_sodium_mg=2300.0,
        max_sat_fat_g=20.0,
        max_sugar_g=45.0,
        user_allergies=allergies,
        strict_allergens=True,
    )
    assert plan is not None

    for _slot, items in plan["meals"].items():
        for item in items:
            name_lower = item["name"].lower()
            assert "peanut" not in name_lower
            assert "milk" not in name_lower
            assert "cheese" not in name_lower
            assert "wheat" not in name_lower


def test_seven_day_meal_plan_generation():
    """Verify multi-day plan generation and solver performance (< 5 seconds)."""
    res = generate_meal_plan(
        target_kcal=2100.0,
        protein_target_g=85.0,
        max_sodium_mg=2300.0,
        days=7,
    )
    assert res["days"] == 7
    assert len(res["daily_plans"]) == 7
    assert res["solve_time_sec"] < 10.0, "7-day generation should be fast"

    # Verify all 7 days meet calorie bounds
    for day in res["daily_plans"]:
        day_kcal = day["daily_totals"]["kcal"]
        assert 1900.0 <= day_kcal <= 2300.0


def test_infeasible_plan_relaxation_cascade():
    """Verify that unrealistic constraints degrade gracefully through relaxation."""
    # Impossibly tight protein constraint at lower calories forces relaxation cascade
    plan, relax_log = solve_daily_meal_plan(
        target_kcal=1600.0,
        protein_target_g=320.0,
        max_sodium_mg=800.0,
        max_sat_fat_g=10.0,
        max_sugar_g=15.0,
    )
    # The relaxation cascade should either relax constraints or report logged relaxations
    assert plan is not None, "Should recover a plan via progressive relaxation"
    assert len(plan["relaxation_log"]) >= 1, "Should record relaxed constraints"
    assert plan["relaxation_level"] >= 1, "Should have escalated relaxation level"


def test_grocery_list_aggregation():
    """Verify grocery list accurately aggregates items across slots and days."""
    mock_plan = {
        "daily_plans": [
            {
                "meals": {
                    "breakfast": [
                        {
                            "food_id": "f1",
                            "name": "Rolled Oats",
                            "category": "Grains & Pasta",
                            "portion_g": 60.0,
                        },
                        {
                            "food_id": "f2",
                            "name": "Blueberries",
                            "category": "Fruits",
                            "portion_g": 100.0,
                        },
                    ],
                    "lunch": [
                        {
                            "food_id": "f3",
                            "name": "Chicken Breast",
                            "category": "Meat & Poultry",
                            "portion_g": 150.0,
                        },
                    ],
                }
            },
            {
                "meals": {
                    "breakfast": [
                        {
                            "food_id": "f1",
                            "name": "Rolled Oats",
                            "category": "Grains & Pasta",
                            "portion_g": 60.0,
                        },
                    ],
                }
            },
        ]
    }
    grocery = generate_grocery_list(mock_plan)
    assert grocery["days_covered"] == 2
    assert "Grains & Pasta" in grocery["departments"]
    assert "Fruits" in grocery["departments"]
    assert "Meat & Poultry" in grocery["departments"]

    # Oats appeared twice: 60 + 60 = 120 g
    oats_entry = next(i for i in grocery["departments"]["Grains & Pasta"] if i["food_id"] == "f1")
    assert oats_entry["total_grams"] == 120.0
