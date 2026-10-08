"""Grocery list aggregation engine grouping meal plan items by category."""

from typing import Any, Dict


def generate_grocery_list(meal_plan_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate all ingredients across a meal plan (1-day or 7-day) into a categorized grocery list.

    Returns:
        Structured grocery list grouped by department category with total quantities.
    """
    daily_plans = meal_plan_payload.get("daily_plans", [])
    if not daily_plans and "meals" in meal_plan_payload:
        daily_plans = [meal_plan_payload]

    # Map of category -> {food_id: {name, total_g, food_type}}
    categorized_items: Dict[str, Dict[str, Dict[str, Any]]] = {}
    total_grocery_weight_g = 0.0

    for day in daily_plans:
        meals = day.get("meals", {})
        for _slot_name, food_items in meals.items():
            for item in food_items:
                fid = item.get("food_id")
                name = item.get("name")
                cat = item.get("category", "Other")
                portion_g = float(item.get("portion_g", 0.0))

                if cat not in categorized_items:
                    categorized_items[cat] = {}

                if fid not in categorized_items[cat]:
                    categorized_items[cat][fid] = {
                        "food_id": fid,
                        "name": name,
                        "category": cat,
                        "food_type": item.get("food_type", "Other"),
                        "total_grams": 0.0,
                    }

                categorized_items[cat][fid]["total_grams"] += portion_g
                total_grocery_weight_g += portion_g

    # Format into sorted lists per category
    departments = {}
    for cat, items_dict in sorted(categorized_items.items()):
        dept_list = []
        for fid, itm in sorted(items_dict.items(), key=lambda x: x[1]["name"]):
            tot_g = round(itm["total_grams"], 1)
            kg_est = round(tot_g / 1000.0, 2)
            dept_list.append(
                {
                    "food_id": fid,
                    "name": itm["name"],
                    "total_grams": tot_g,
                    "total_weight_g": tot_g,
                    "display_quantity": f"{tot_g:.0f}g ({kg_est:.2f} kg)"
                    if tot_g >= 500
                    else f"{tot_g:.0f}g",
                }
            )
        departments[cat] = dept_list

    return {
        "departments": departments,
        "items_by_department": departments,
        "total_unique_items": sum(len(items) for items in departments.values()),
        "total_weight_kg": round(total_grocery_weight_g / 1000.0, 2),
        "days_covered": len(daily_plans),
    }


aggregate_grocery_list = generate_grocery_list
