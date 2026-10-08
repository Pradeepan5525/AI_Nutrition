"""PuLP Linear Programming optimizer for daily and weekly meal plans."""

import time
from typing import Any, Dict, List, Optional, Set, Tuple

import pulp

from nutri.foods.food_db import get_food_db
from nutri.logging import setup_logger
from nutri.plan.meal_templates import MEAL_SLOT_TEMPLATES, get_slot_portion_bounds

logger = setup_logger(__name__)


def select_candidate_pool(
    slot_name: str,
    user_allergies: Optional[List[str]] = None,
    dietary_restrictions: Optional[List[str]] = None,
    strict_allergens: bool = True,
    max_candidates: int = 15,
    banned_food_ids: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """Select top eligible foods for a meal slot respecting allergen and dietary boundaries."""
    db = get_food_db()
    slot_cfg = MEAL_SLOT_TEMPLATES[slot_name]
    preferred_types = slot_cfg["preferred_food_types"]
    banned = banned_food_ids or set()

    candidates = []
    # Collect candidates across preferred food types
    for ftype in preferred_types:
        foods = db.search_foods(
            food_type=ftype,
            min_health_score=40.0,
            exclude_allergens=user_allergies,
            dietary_tags=dietary_restrictions,
            strict_allergens=strict_allergens,
            limit=12,
        )
        for f in foods:
            if f["food_id"] not in banned and f["food_id"] not in {
                c["food_id"] for c in candidates
            }:
                candidates.append(f)

    # Sort descending by health score and take top N
    candidates.sort(key=lambda x: x["health_score_v2"], reverse=True)
    return candidates[:max_candidates]


def solve_daily_meal_plan(
    target_kcal: float,
    protein_target_g: float,
    max_sodium_mg: float,
    max_sat_fat_g: float,
    max_sugar_g: float,
    user_allergies: Optional[List[str]] = None,
    dietary_restrictions: Optional[List[str]] = None,
    strict_allergens: bool = True,
    banned_food_ids: Optional[Set[str]] = None,
    relaxation_level: int = 0,
    cumulative_relaxation_log: Optional[List[str]] = None,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Formulate and solve a mixed-integer linear programming daily meal plan.

    Tolerance standard: Caloric target within +/- 5% under optimal solve.
    Infeasibility handling: Relaxes bounds progressively across 3 levels.
    """
    relaxation_log: List[str] = list(cumulative_relaxation_log or [])

    # Apply relaxation adjustments if level > 0
    cal_tol = 0.05
    eff_sodium = max_sodium_mg
    eff_sat_fat = max_sat_fat_g
    eff_sugar = max_sugar_g
    eff_protein = protein_target_g * 0.85

    if relaxation_level == 1:
        cal_tol = 0.08
        relaxation_log.append("Relaxed daily calorie tolerance window from +/-5% to +/-8%.")
    elif relaxation_level == 2:
        cal_tol = 0.08
        eff_sodium = max_sodium_mg * 1.15
        eff_sat_fat = max_sat_fat_g * 1.15
        relaxation_log.append("Relaxed daily sodium and saturated fat constraints by +15%.")
    elif relaxation_level >= 3:
        cal_tol = 0.08
        eff_sodium = max_sodium_mg * 1.15
        eff_sat_fat = max_sat_fat_g * 1.15
        eff_sugar = max_sugar_g * 1.25
        eff_protein = protein_target_g * 0.75
        relaxation_log.append("Relaxed daily added sugar cap (+25%) and protein floor (-15%).")

    min_kcal = target_kcal * (1.0 - cal_tol + 0.001)
    max_kcal = target_kcal * (1.0 + cal_tol - 0.002)

    # Select candidate food pools per slot
    slots = ["breakfast", "lunch", "dinner", "snack"]
    slot_candidates: Dict[str, List[Dict[str, Any]]] = {}

    for s in slots:
        cands = select_candidate_pool(
            slot_name=s,
            user_allergies=user_allergies,
            dietary_restrictions=dietary_restrictions,
            strict_allergens=strict_allergens,
            banned_food_ids=banned_food_ids,
        )
        if len(cands) < 2:
            # Fallback to broader candidate search if restrictive filters reduced pool
            db = get_food_db()
            cands = db.search_foods(
                min_health_score=30.0,
                exclude_allergens=user_allergies,
                dietary_tags=dietary_restrictions,
                strict_allergens=strict_allergens,
                limit=15,
            )
        slot_candidates[s] = cands

    # Create PuLP model
    prob = pulp.LpProblem("Daily_Meal_Plan_Optimizer", pulp.LpMaximize)

    # Variables: portion x_{s,i} (in grams) and binary indicator z_{s,i}
    x_vars: Dict[Tuple[str, str], pulp.LpVariable] = {}
    z_vars: Dict[Tuple[str, str], pulp.LpVariable] = {}
    food_map: Dict[str, Dict[str, Any]] = {}

    for s in slots:
        cfg = MEAL_SLOT_TEMPLATES[s]
        for f in slot_candidates[s]:
            fid = f["food_id"]
            food_map[fid] = f
            var_key = (s, fid)

            min_g, max_g = get_slot_portion_bounds(s, f.get("food_type", "Other"))
            z_vars[var_key] = pulp.LpVariable(f"z_{s}_{fid}", cat=pulp.LpBinary)
            x_vars[var_key] = pulp.LpVariable(f"x_{s}_{fid}", lowBound=0.0, upBound=max_g)

            # Link portion bounds to binary indicator: z * min_g <= x <= z * max_g
            prob += x_vars[var_key] >= z_vars[var_key] * min_g
            prob += x_vars[var_key] <= z_vars[var_key] * max_g

        # Slot item count bounds
        prob += (
            pulp.lpSum([z_vars[(s, f["food_id"])] for f in slot_candidates[s]]) >= cfg["min_items"]
        )
        prob += (
            pulp.lpSum([z_vars[(s, f["food_id"])] for f in slot_candidates[s]]) <= cfg["max_items"]
        )

    # Global Daily Nutrient Constraints
    # Calories: [min_kcal, max_kcal]
    total_kcal = pulp.lpSum(
        [
            (food_map[fid]["kcal_100g"] / 100.0) * x_vars[(s, fid)]
            for s in slots
            for fid in [f["food_id"] for f in slot_candidates[s]]
        ]
    )
    prob += total_kcal >= min_kcal, "Min_Calories"
    prob += total_kcal <= max_kcal, "Max_Calories"

    # Sodium <= max_sodium
    total_sodium = pulp.lpSum(
        [
            (food_map[fid]["sodium_mg_100g"] / 100.0) * x_vars[(s, fid)]
            for s in slots
            for fid in [f["food_id"] for f in slot_candidates[s]]
        ]
    )
    prob += total_sodium <= eff_sodium, "Max_Sodium"

    # Saturated Fat <= max_sat_fat
    total_sat_fat = pulp.lpSum(
        [
            (food_map[fid]["sat_fat_100g"] / 100.0) * x_vars[(s, fid)]
            for s in slots
            for fid in [f["food_id"] for f in slot_candidates[s]]
        ]
    )
    prob += total_sat_fat <= eff_sat_fat, "Max_Sat_Fat"

    # Added Sugar <= max_sugar
    total_sugar = pulp.lpSum(
        [
            (food_map[fid]["sugar_100g"] / 100.0) * x_vars[(s, fid)]
            for s in slots
            for fid in [f["food_id"] for f in slot_candidates[s]]
        ]
    )
    prob += total_sugar <= eff_sugar, "Max_Sugar"

    # Protein >= eff_protein
    total_protein = pulp.lpSum(
        [
            (food_map[fid]["protein_100g"] / 100.0) * x_vars[(s, fid)]
            for s in slots
            for fid in [f["food_id"] for f in slot_candidates[s]]
        ]
    )
    prob += total_protein >= eff_protein, "Min_Protein"

    # Objective: Maximize health score of selected portions
    prob += pulp.lpSum(
        [
            (food_map[fid]["health_score_v2"] / 100.0) * x_vars[(s, fid)]
            for s in slots
            for fid in [f["food_id"] for f in slot_candidates[s]]
        ]
    )

    # Solve with CBC
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=5)
    status = prob.solve(solver)

    if status != pulp.LpStatusOptimal:
        if relaxation_level < 3:
            logger.info("Plan infeasible at relaxation level %d; escalating...", relaxation_level)
            return solve_daily_meal_plan(
                target_kcal=target_kcal,
                protein_target_g=protein_target_g,
                max_sodium_mg=max_sodium_mg,
                max_sat_fat_g=max_sat_fat_g,
                max_sugar_g=max_sugar_g,
                user_allergies=user_allergies,
                dietary_restrictions=dietary_restrictions,
                strict_allergens=strict_allergens,
                banned_food_ids=banned_food_ids,
                relaxation_level=relaxation_level + 1,
                cumulative_relaxation_log=relaxation_log,
            )
        else:
            logger.warning("Meal plan solver failed even after 3 levels of constraint relaxation.")
            return None, relaxation_log

    # Extract chosen plan
    meals: Dict[str, List[Dict[str, Any]]] = {s: [] for s in slots}
    day_totals = {
        "kcal": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "carbs_g": 0.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 0.0,
        "sat_fat_g": 0.0,
    }

    for s in slots:
        for f in slot_candidates[s]:
            fid = f["food_id"]
            portion_val = pulp.value(x_vars[(s, fid)])
            if portion_val and portion_val >= 10.0:
                portion_g = round(float(portion_val), 1)
                factor = portion_g / 100.0
                item_kcal = round(f["kcal_100g"] * factor, 1)
                item_protein = round(f["protein_100g"] * factor, 1)
                item_fat = round(f["fat_100g"] * factor, 1)
                item_carbs = round(f["carbs_100g"] * factor, 1)
                item_fiber = round(f["fiber_100g"] * factor, 1)
                item_sugar = round(f["sugar_100g"] * factor, 1)
                item_sodium = round(f["sodium_mg_100g"] * factor, 1)
                item_sat_fat = round(f["sat_fat_100g"] * factor, 1)

                meals[s].append(
                    {
                        "food_id": fid,
                        "name": f["name"],
                        "category": f["category"],
                        "food_type": f["food_type"],
                        "portion_g": portion_g,
                        "kcal": item_kcal,
                        "protein_g": item_protein,
                        "fat_g": item_fat,
                        "carbs_g": item_carbs,
                        "fiber_g": item_fiber,
                        "sugar_g": item_sugar,
                        "sodium_mg": item_sodium,
                        "sat_fat_g": item_sat_fat,
                        "health_score_v2": f["health_score_v2"],
                    }
                )

                day_totals["kcal"] += item_kcal
                day_totals["protein_g"] += item_protein
                day_totals["fat_g"] += item_fat
                day_totals["carbs_g"] += item_carbs
                day_totals["fiber_g"] += item_fiber
                day_totals["sugar_g"] += item_sugar
                day_totals["sodium_mg"] += item_sodium
                day_totals["sat_fat_g"] += item_sat_fat

    # Round totals
    day_totals = {k: round(v, 1) for k, v in day_totals.items()}
    calorie_error_pct = round(((day_totals["kcal"] - target_kcal) / target_kcal) * 100.0, 2)

    return {
        "meals": meals,
        "daily_totals": day_totals,
        "target_kcal": target_kcal,
        "calorie_error_pct": calorie_error_pct,
        "relaxation_log": relaxation_log,
        "relaxation_level": relaxation_level,
    }, relaxation_log


def generate_meal_plan(
    target_kcal: float,
    protein_target_g: float,
    max_sodium_mg: float = 2300.0,
    max_sat_fat_g: float = 22.0,
    max_sugar_g: float = 50.0,
    user_allergies: Optional[List[str]] = None,
    dietary_restrictions: Optional[List[str]] = None,
    strict_allergens: bool = True,
    days: int = 1,
) -> Dict[str, Any]:
    """Generate 1-day or 7-day personalized meal schedule with diversity protection."""
    start_time = time.time()
    user_allergies = user_allergies or []
    dietary_restrictions = dietary_restrictions or []

    daily_plans = []
    used_food_counts: Dict[str, int] = {}

    for day_idx in range(1, days + 1):
        # Exclude foods already used 2+ times in the week to enforce variety
        banned_ids = {fid for fid, count in used_food_counts.items() if count >= 2}

        plan, relax_log = solve_daily_meal_plan(
            target_kcal=target_kcal,
            protein_target_g=protein_target_g,
            max_sodium_mg=max_sodium_mg,
            max_sat_fat_g=max_sat_fat_g,
            max_sugar_g=max_sugar_g,
            user_allergies=user_allergies,
            dietary_restrictions=dietary_restrictions,
            strict_allergens=strict_allergens,
            banned_food_ids=banned_ids,
        )

        if not plan:
            # Fallback without variety ban if needed
            plan, relax_log = solve_daily_meal_plan(
                target_kcal=target_kcal,
                protein_target_g=protein_target_g,
                max_sodium_mg=max_sodium_mg,
                max_sat_fat_g=max_sat_fat_g,
                max_sugar_g=max_sugar_g,
                user_allergies=user_allergies,
                dietary_restrictions=dietary_restrictions,
                strict_allergens=strict_allergens,
                banned_food_ids=set(),
            )

        if plan:
            plan["day_number"] = day_idx
            daily_plans.append(plan)
            # Track used foods
            for _slot, items in plan["meals"].items():
                for itm in items:
                    fid = itm["food_id"]
                    used_food_counts[fid] = used_food_counts.get(fid, 0) + 1

    solve_time_sec = round(time.time() - start_time, 2)
    logger.info("Generated %d-day meal plan in %.2f seconds", days, solve_time_sec)

    return {
        "days": days,
        "daily_plans": daily_plans,
        "solve_time_sec": solve_time_sec,
        "constraints": {
            "target_kcal": target_kcal,
            "protein_target_g": protein_target_g,
            "max_sodium_mg": max_sodium_mg,
            "max_sat_fat_g": max_sat_fat_g,
            "max_sugar_g": max_sugar_g,
        },
    }
