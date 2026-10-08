"""Tri-state allergen detection and safety classification engine."""

import json
import re
from typing import Any, Dict, Optional, Set

from nutri.logging import setup_logger

logger = setup_logger(__name__)

# Tri-state constants
ALLERGEN_PRESENT = "present"
ALLERGEN_ABSENT = "absent"
ALLERGEN_UNKNOWN = "unknown"

# Comprehensive allergen keyword patterns
ALLERGEN_KEYWORDS: Dict[str, Set[str]] = {
    "gluten": {
        "wheat",
        "barley",
        "rye",
        "gluten",
        "spelt",
        "semolina",
        "durum",
        "triticale",
        "bulgur",
        "couscous",
        "malt",
        "kamut",
        "farro",
    },
    "dairy": {
        "milk",
        "dairy",
        "cheese",
        "butter",
        "cream",
        "yogurt",
        "yoghurt",
        "casein",
        "caseinate",
        "whey",
        "lactose",
        "ghee",
        "curd",
        "custard",
        "parmesan",
        "cheddar",
        "mozzarella",
        "ricotta",
    },
    "nuts": {
        "almond",
        "walnut",
        "cashew",
        "pecan",
        "pistachio",
        "hazelnut",
        "macadamia",
        "brazil nut",
        "chestnut",
        "pine nut",
        "walnuts",
        "cashews",
        "almonds",
        "pecans",
        "pistachios",
        "hazelnuts",
        "tree nut",
    },
    "peanuts": {"peanut", "peanuts", "groundnut", "arachis", "peanut butter"},
    "soy": {
        "soy",
        "soya",
        "soybean",
        "soybeans",
        "tofu",
        "edamame",
        "tempeh",
        "miso",
        "tamari",
        "natto",
        "shoyu",
        "soymilk",
        "soy lecithin",
    },
    "eggs": {
        "egg",
        "eggs",
        "albumin",
        "ovalbumin",
        "mayonnaise",
        "meringue",
        "egg yolk",
        "egg white",
    },
    "fish": {
        "fish",
        "salmon",
        "tuna",
        "cod",
        "tilapia",
        "trout",
        "anchovy",
        "mackerel",
        "bass",
        "sardine",
        "sardines",
        "haddock",
        "halibut",
        "snapper",
        "pollock",
        "catfish",
        "swordfish",
        "herring",
    },
}

# Compiled regex patterns for boundary-sensitive keyword matching
_REGEX_PATTERNS = {
    allergen: re.compile(
        r"\b(" + "|".join(re.escape(k) for k in sorted(keywords, key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )
    for allergen, keywords in ALLERGEN_KEYWORDS.items()
}


def detect_allergen_tri_state(
    food_name: str,
    ingredients: Optional[str] = None,
    raw_flags: Optional[Dict[str, Any]] = None,
    is_packaged: bool = False,
    is_foundation_raw: bool = False,
) -> Dict[str, str]:
    """Detect presence, absence, or unverified status of supported allergens.

    Tri-state rules:
    - 'present': explicitly flagged True in source data, or matched by keyword
      in ingredient list or product name.
    - 'absent': verified absent from ingredient list / verified allergen testing,
      or known single-ingredient raw produce/meat with no matching keywords.
    - 'unknown': missing ingredient info and no authoritative negative disclosure.

    Args:
        food_name: Food or product title.
        ingredients: Ingredient listing string if available.
        raw_flags: Dictionary of source allergen booleans (e.g. contains_gluten).
        is_packaged: Whether the food is a commercial packaged product.
        is_foundation_raw: Whether the food is a single-ingredient whole food.

    Returns:
        Dict mapping allergen name to 'present' | 'absent' | 'unknown'.
    """
    raw_flags = raw_flags or {}
    text_to_search = f"{food_name or ''} {ingredients or ''}".lower()
    has_ingredients = bool(ingredients and len(str(ingredients).strip()) > 3)

    result: Dict[str, str] = {}

    for allergen, pattern in _REGEX_PATTERNS.items():
        # 1. Check positive source flags
        flag_val = raw_flags.get(f"contains_{allergen}", None)
        if flag_val is True or flag_val == 1 or str(flag_val).lower() == "true":
            result[allergen] = ALLERGEN_PRESENT
            continue

        # 2. Check keyword pattern match in name & ingredients
        if pattern.search(text_to_search):
            result[allergen] = ALLERGEN_PRESENT
            continue

        # 3. Explicit negative flag in source dataset with ingredient verification
        if flag_val is False or flag_val == 0 or str(flag_val).lower() == "false":
            result[allergen] = ALLERGEN_ABSENT
            continue

        # 4. Verified whole food (Foundation / SR Legacy raw single items)
        if is_foundation_raw and not pattern.search(text_to_search):
            result[allergen] = ALLERGEN_ABSENT
            continue

        # 5. Packaged product with detailed ingredients list that didn't match keyword
        if is_packaged and has_ingredients and not pattern.search(text_to_search):
            # If comprehensive ingredient text is present and keyword is absent,
            # it's considered verified absent
            result[allergen] = ALLERGEN_ABSENT
            continue

        # 6. Default fail-safe: unverified = unknown (never assume safe!)
        result[allergen] = ALLERGEN_UNKNOWN

    return result


def allergen_flags_to_json(flags: Dict[str, str]) -> str:
    """Serialize allergen flags to JSON string."""
    return json.dumps(flags, sort_keys=True)


def parse_allergen_json(flags_json: str) -> Dict[str, str]:
    """Parse JSON string back to allergen flags dict."""
    try:
        return json.loads(flags_json)
    except Exception:
        return dict.fromkeys(ALLERGEN_KEYWORDS, ALLERGEN_UNKNOWN)


def is_food_safe_for_allergies(
    allergen_flags: Dict[str, str],
    user_allergies: list[str],
    strict: bool = True,
) -> bool:
    """Check if a food is safe given user allergies.

    Args:
        allergen_flags: Food allergen status mapping.
        user_allergies: List of allergen names user is allergic to.
        strict: If True, treats 'unknown' as unsafe. If False, only 'present' is unsafe.

    Returns:
        True if safe, False if unsafe.
    """
    for allergen in user_allergies:
        allergen_clean = allergen.lower().strip()
        status = allergen_flags.get(allergen_clean, ALLERGEN_UNKNOWN)
        if status == ALLERGEN_PRESENT:
            return False
        if strict and status == ALLERGEN_UNKNOWN:
            return False
    return True
