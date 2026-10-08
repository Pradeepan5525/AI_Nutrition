"""Content-based food search, filtering, and personalized ranking engine."""

from typing import Any, Dict, List, Optional

from nutri.foods.food_db import get_food_db
from nutri.logging import setup_logger

logger = setup_logger(__name__)


def score_food_fitness(
    food: Dict[str, Any],
    macro_priorities: Optional[Dict[str, float]] = None,
    condition_penalties: Optional[Dict[str, float]] = None,
) -> float:
    """Calculate fitness score combining baseline health score with personalized macro fit.

    Formula:
    fitness = 0.5 * health_score_v2 + 0.3 * protein_density_fit - 0.2 * condition_penalties
    """
    health_score = float(food.get("health_score_v2", 50.0))
    kcal = float(food.get("kcal_100g", 100.0))
    protein = float(food.get("protein_100g", 0.0))
    sodium = float(food.get("sodium_mg_100g", 0.0))
    sugar = float(food.get("sugar_100g", 0.0))

    # Protein density factor: protein grams per 100 kcal
    protein_per_100kcal = (protein / kcal * 100.0) if kcal > 0 else 0.0
    protein_bonus = min(20.0, protein_per_100kcal * 2.0)

    # Condition penalties
    penalty = 0.0
    cond_penalties = condition_penalties or {}
    if cond_penalties.get("hypertension", False):
        if sodium > 400.0:
            penalty += min(25.0, (sodium - 400.0) / 40.0)

    if cond_penalties.get("diabetes", False):
        if sugar > 10.0:
            penalty += min(25.0, (sugar - 10.0) * 1.5)

    fitness = (0.6 * health_score) + (0.4 * protein_bonus) - penalty
    return round(float(max(0.0, min(100.0, fitness))), 1)


def search_and_rank_foods(
    query: str = "",
    category: Optional[str] = None,
    food_type: Optional[str] = None,
    user_allergies: Optional[List[str]] = None,
    dietary_restrictions: Optional[List[str]] = None,
    strict_allergens: bool = True,
    active_conditions: Optional[List[str]] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Hard-filters allergens and restrictions first, then ranks by personalized fitness."""
    db = get_food_db()

    # 1. Hard database filtering (Zero allergen tolerance)
    raw_results = db.search_foods(
        query=query,
        category=category,
        food_type=food_type,
        exclude_allergens=user_allergies,
        dietary_tags=dietary_restrictions,
        strict_allergens=strict_allergens,
        limit=max(limit * 2, 100),  # fetch larger pool for personalized reranking
        offset=offset,
    )

    if not raw_results:
        return []

    # 2. Build condition penalty flags
    conditions_dict = {cond.lower().strip(): True for cond in (active_conditions or [])}

    # 3. Personalized re-ranking
    scored_items = []
    for item in raw_results:
        fitness = score_food_fitness(item, condition_penalties=conditions_dict)
        item_copy = dict(item)
        item_copy["personalized_fitness_score"] = fitness
        scored_items.append(item_copy)

    # Sort descending by personalized fitness, then health score
    scored_items.sort(
        key=lambda x: (x["personalized_fitness_score"], x["health_score_v2"]),
        reverse=True,
    )

    return scored_items[:limit]
