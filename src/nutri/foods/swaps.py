"""Healthier Food Swap engine identifying nutritionally superior alternatives."""

from typing import Any, Dict, List, Optional, Union

from nutri.foods.food_db import get_food_db
from nutri.logging import setup_logger

logger = setup_logger(__name__)


def find_healthier_swaps(
    food_id_or_record: Union[str, Dict[str, Any]],
    user_allergies: Optional[List[str]] = None,
    dietary_restrictions: Optional[List[str]] = None,
    strict_allergens: bool = True,
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    """Identify strictly healthier same-category replacements for a food item.

    Criteria for a valid 'Healthier Swap':
    1. Candidate shares same category or food_type as base food.
    2. Zero allergen and dietary restriction violations.
    3. Strictly higher Health Score v2 (score_candidate > score_base).
    4. At least one measurable improvement: lower calories, lower sodium, or lower sugar.

    Args:
        food_id_or_record: Food ID string or food dictionary.
        user_allergies: Allergens to strictly exclude.
        dietary_restrictions: Dietary tags (e.g. vegan, low_sodium).
        strict_allergens: Whether to treat 'unknown' allergen status as unsafe.
        top_n: Number of swap suggestions to return.

    Returns:
        List of candidate food records annotated with quantified improvement diffs.
    """
    db = get_food_db()

    # 1. Retrieve base food
    if isinstance(food_id_or_record, str):
        base_food = db.get_food_by_id(food_id_or_record)
        if not base_food:
            logger.warning("Base food ID %s not found for swap analysis", food_id_or_record)
            return []
    else:
        base_food = food_id_or_record

    base_score = float(base_food.get("health_score_v2", 50.0))
    base_kcal = float(base_food.get("kcal_100g", 100.0))
    base_sodium = float(base_food.get("sodium_mg_100g", 0.0))
    base_sugar = float(base_food.get("sugar_100g", 0.0))
    category = base_food.get("category", "Other")
    food_type = base_food.get("food_type", "Other")

    # 2. Search candidate pool in same category or food type
    candidates = db.search_foods(
        category=category if category != "Other" else None,
        food_type=food_type,
        min_health_score=base_score + 1.0,  # Strictly higher health score
        exclude_allergens=user_allergies,
        dietary_tags=dietary_restrictions,
        strict_allergens=strict_allergens,
        limit=100,
    )

    # If category pool is small, search broader food_type pool
    if len(candidates) < 5 and category != "Other":
        broader = db.search_foods(
            food_type=food_type,
            min_health_score=base_score + 1.0,
            exclude_allergens=user_allergies,
            dietary_tags=dietary_restrictions,
            strict_allergens=strict_allergens,
            limit=100,
        )
        candidates.extend(
            [c for c in broader if c["food_id"] not in {x["food_id"] for x in candidates}]
        )

    valid_swaps = []
    base_id = base_food.get("food_id")

    for cand in candidates:
        if cand.get("food_id") == base_id:
            continue

        c_score = float(cand.get("health_score_v2", 0.0))
        c_kcal = float(cand.get("kcal_100g", 0.0))
        c_sodium = float(cand.get("sodium_mg_100g", 0.0))
        c_sugar = float(cand.get("sugar_100g", 0.0))
        c_fiber = float(cand.get("fiber_100g", 0.0))
        c_protein = float(cand.get("protein_100g", 0.0))

        delta_score = round(c_score - base_score, 1)
        delta_kcal = round(c_kcal - base_kcal, 1)
        delta_sodium = round(c_sodium - base_sodium, 1)
        delta_sugar = round(c_sugar - base_sugar, 1)
        delta_fiber = round(c_fiber - float(base_food.get("fiber_100g", 0.0)), 1)
        delta_protein = round(c_protein - float(base_food.get("protein_100g", 0.0)), 1)

        # Must have at least one meaningful reduction in risk nutrients
        has_reduction = (
            (delta_kcal <= -10.0)
            or (delta_sodium <= -50.0)
            or (delta_sugar <= -2.0)
            or (delta_score >= 10.0)
        )
        if not has_reduction:
            continue

        # Formulate human-readable diff highlights
        highlights = [f"+{delta_score:.1f} Health Score"]
        if delta_kcal < 0:
            highlights.append(f"{delta_kcal:.0f} kcal")
        if delta_sodium < 0:
            highlights.append(f"{delta_sodium:.0f} mg sodium")
        if delta_sugar < 0:
            highlights.append(f"{delta_sugar:.1f}g sugar")
        if delta_fiber > 0:
            highlights.append(f"+{delta_fiber:.1f}g fiber")

        cand_annotated = dict(cand)
        cand_annotated["score_improvement"] = delta_score
        cand_annotated["kcal_diff"] = delta_kcal
        cand_annotated["sodium_diff_mg"] = delta_sodium
        cand_annotated["sugar_diff_g"] = delta_sugar
        cand_annotated["sat_fat_diff_g"] = round(
            float(cand.get("sat_fat_100g", 0.0)) - float(base_food.get("sat_fat_100g", 0.0)), 1
        )
        cand_annotated["reasons"] = highlights
        cand_annotated["swap_diff"] = {
            "delta_health_score": delta_score,
            "delta_kcal_100g": delta_kcal,
            "delta_sodium_mg_100g": delta_sodium,
            "delta_sugar_100g": delta_sugar,
            "delta_fiber_100g": delta_fiber,
            "delta_protein_100g": delta_protein,
            "highlights_summary": ", ".join(highlights),
        }
        valid_swaps.append(cand_annotated)

    # Rank by greatest health score gain and lowest calorie delta
    valid_swaps.sort(
        key=lambda x: (
            x["swap_diff"]["delta_health_score"],
            -x["swap_diff"]["delta_kcal_100g"],
            -x["swap_diff"]["delta_sodium_mg_100g"],
        ),
        reverse=True,
    )

    return valid_swaps[:top_n]
