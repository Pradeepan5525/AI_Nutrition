"""Unit tests for search, ranking, healthier swaps, and allergen safety guarantees."""

from nutri.foods.food_db import get_food_db
from nutri.foods.search import score_food_fitness, search_and_rank_foods
from nutri.foods.swaps import find_healthier_swaps


def test_allergen_exclusion_guarantee_in_search():
    """Safety Guarantee: No food containing the user's allergen is ever returned in search."""
    db = get_food_db()

    # Search with strict peanut exclusion
    peanut_free_results = db.search_foods(
        query="butter",
        exclude_allergens=["peanuts"],
        strict_allergens=True,
        limit=30,
    )

    for item in peanut_free_results:
        assert item["allergen_peanuts"] == "absent", (
            f"Found non-absent peanut in item: {item['name']}"
        )
        assert "peanut" not in item["name"].lower()


def test_allergen_exclusion_guarantee_in_swaps():
    """Safety Guarantee: Healthier swaps never recommend a food violating the user's allergen."""
    # Base food: Potato chips
    mock_base = {
        "food_id": "mock_chips",
        "name": "Salty Potato Chips",
        "category": "Snacks & Sweets",
        "food_type": "Snacks",
        "health_score_v2": 25.0,
        "kcal_100g": 540.0,
        "sodium_mg_100g": 600.0,
        "sugar_100g": 2.0,
        "fiber_100g": 2.0,
        "protein_100g": 6.0,
    }

    # User is allergic to gluten and dairy
    swaps = find_healthier_swaps(
        food_id_or_record=mock_base,
        user_allergies=["gluten", "dairy"],
        strict_allergens=True,
        top_n=5,
    )

    for cand in swaps:
        assert cand["allergen_gluten"] == "absent", (
            f"Swap violated gluten exclusion: {cand['name']}"
        )
        assert cand["allergen_dairy"] == "absent", f"Swap violated dairy exclusion: {cand['name']}"


def test_swap_is_strictly_healthier():
    """Verify that every recommended swap has a strictly higher Health Score v2."""
    mock_cookie = {
        "food_id": "mock_cookie",
        "name": "Chocolate Chip Cookie",
        "category": "Snacks & Sweets",
        "food_type": "Snacks",
        "health_score_v2": 20.0,
        "kcal_100g": 490.0,
        "sodium_mg_100g": 380.0,
        "sugar_100g": 35.0,
        "fiber_100g": 1.5,
        "protein_100g": 4.5,
    }

    swaps = find_healthier_swaps(mock_cookie, top_n=5)
    assert len(swaps) > 0

    for cand in swaps:
        diff = cand["swap_diff"]
        assert diff["delta_health_score"] > 0, "Swap must have strictly higher health score"
        assert cand["health_score_v2"] > mock_cookie["health_score_v2"]
        assert len(diff["highlights_summary"]) > 0


def test_ranking_determinism():
    """Verify that identical search queries produce 100% deterministic ordered results."""
    run1 = search_and_rank_foods(query="rice", limit=10)
    run2 = search_and_rank_foods(query="rice", limit=10)

    assert len(run1) == len(run2)
    for item1, item2 in zip(run1, run2, strict=True):
        assert item1["food_id"] == item2["food_id"]
        assert item1["personalized_fitness_score"] == item2["personalized_fitness_score"]


def test_score_food_fitness():
    """Verify fitness scoring blends health score with conditions and protein fit."""
    sample_food = {
        "health_score_v2": 70.0,
        "kcal_100g": 120.0,
        "protein_100g": 18.0,
        "sodium_mg_100g": 150.0,
        "sugar_100g": 1.0,
    }
    fitness = score_food_fitness(sample_food)
    assert 50.0 <= fitness <= 100.0

    # With hypertension penalty on high-sodium food
    salty_food = {
        "health_score_v2": 60.0,
        "kcal_100g": 200.0,
        "protein_100g": 10.0,
        "sodium_mg_100g": 1200.0,
        "sugar_100g": 0.0,
    }
    fit_normal = score_food_fitness(salty_food)
    fit_htn = score_food_fitness(salty_food, condition_penalties={"hypertension": True})
    assert fit_htn < fit_normal, (
        "Hypertension penalty must reduce fitness score for high-sodium food"
    )
