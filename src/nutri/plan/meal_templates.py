"""Meal templates defining slot distributions and category affinities."""

from typing import Any, Dict

MEAL_SLOT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "breakfast": {
        "name": "Breakfast",
        "target_kcal_pct": 0.25,
        "min_items": 2,
        "max_items": 3,
        "preferred_categories": ["Grains & Pasta", "Dairy & Egg", "Fruits", "Legumes & Nuts"],
        "preferred_food_types": ["Grains", "Dairy", "Fruits", "Proteins"],
        "portion_bounds_g": {
            "Grains": (40.0, 150.0),
            "Dairy": (100.0, 250.0),
            "Fruits": (80.0, 200.0),
            "Proteins": (50.0, 150.0),
            "Other": (20.0, 100.0),
        },
    },
    "lunch": {
        "name": "Lunch",
        "target_kcal_pct": 0.35,
        "min_items": 2,
        "max_items": 4,
        "preferred_categories": [
            "Vegetables",
            "Meat & Poultry",
            "Fish & Seafood",
            "Grains & Pasta",
            "Legumes & Nuts",
        ],
        "preferred_food_types": ["Proteins", "Vegetables", "Grains"],
        "portion_bounds_g": {
            "Proteins": (80.0, 220.0),
            "Vegetables": (80.0, 250.0),
            "Grains": (50.0, 180.0),
            "Other": (20.0, 100.0),
        },
    },
    "dinner": {
        "name": "Dinner",
        "target_kcal_pct": 0.30,
        "min_items": 2,
        "max_items": 4,
        "preferred_categories": [
            "Vegetables",
            "Meat & Poultry",
            "Fish & Seafood",
            "Legumes & Nuts",
            "Grains & Pasta",
        ],
        "preferred_food_types": ["Proteins", "Vegetables", "Grains"],
        "portion_bounds_g": {
            "Proteins": (80.0, 220.0),
            "Vegetables": (100.0, 250.0),
            "Grains": (40.0, 150.0),
            "Other": (20.0, 100.0),
        },
    },
    "snack": {
        "name": "Snack",
        "target_kcal_pct": 0.10,
        "min_items": 1,
        "max_items": 2,
        "preferred_categories": ["Fruits", "Legumes & Nuts", "Dairy & Egg", "Snacks & Sweets"],
        "preferred_food_types": ["Fruits", "Snacks", "Dairy", "Proteins"],
        "portion_bounds_g": {
            "Fruits": (60.0, 180.0),
            "Proteins": (25.0, 80.0),
            "Dairy": (80.0, 180.0),
            "Snacks": (25.0, 80.0),
            "Other": (20.0, 80.0),
        },
    },
}


def get_slot_portion_bounds(slot_name: str, food_type: str) -> tuple[float, float]:
    """Retrieve realistic min and max portion bounds in grams for a given slot and food type."""
    slot_cfg = MEAL_SLOT_TEMPLATES.get(slot_name, MEAL_SLOT_TEMPLATES["lunch"])
    bounds_map = slot_cfg.get("portion_bounds_g", {})
    return bounds_map.get(food_type, bounds_map.get("Other", (30.0, 150.0)))
