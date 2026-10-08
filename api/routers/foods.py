"""Food repository query router: search, filtering, and healthier swap recommendations."""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.schemas import FoodItem, FoodSearchResponse, FoodSwapItem, FoodSwapResponse
from nutri.foods.food_db import get_food_db
from nutri.foods.swaps import find_healthier_swaps

router = APIRouter(prefix="/foods", tags=["Foods"])


def _row_to_food_item(r: dict) -> FoodItem:
    """Helper to convert database row dict to typed FoodItem schema."""
    allergens = {}
    if r.get("allergen_flags"):
        try:
            allergens = (
                json.loads(r["allergen_flags"])
                if isinstance(r["allergen_flags"], str)
                else r["allergen_flags"]
            )
        except Exception:
            allergens = {}

    tags = []
    if r.get("restriction_tags"):
        tags = [t.strip() for t in r["restriction_tags"].split(",") if t.strip()]

    return FoodItem(
        food_id=str(r.get("food_id", "")),
        name=str(r.get("name", "")),
        category=str(r.get("category", "Other")),
        food_type=str(r.get("food_type", "Other")),
        health_score_v2=round(float(r.get("health_score_v2", 0.0)), 1),
        nutri_score=str(r.get("nutriscore") or "unknown"),
        kcal_100g=round(float(r.get("kcal_100g", 0.0)), 1),
        protein_100g=round(float(r.get("protein_100g", 0.0)), 1),
        carbs_100g=round(float(r.get("carbs_100g", 0.0)), 1),
        fat_100g=round(float(r.get("fat_100g", 0.0)), 1),
        fiber_100g=round(float(r.get("fiber_100g", 0.0)), 1),
        sugar_100g=round(float(r.get("sugar_100g", 0.0)), 1),
        sodium_mg_100g=round(float(r.get("sodium_mg_100g", 0.0)), 1),
        sat_fat_100g=round(float(r.get("sat_fat_100g", 0.0)), 1),
        cholesterol_mg_100g=round(float(r.get("cholesterol_mg_100g", 0.0)), 1),
        allergens=allergens,
        dietary_restrictions=tags,
    )


@router.get("/search", response_model=FoodSearchResponse)
def search_foods(
    q: str = Query("", description="Full or partial food name search query"),
    category: Optional[str] = Query(None, description="Food category filter"),
    food_type: Optional[str] = Query(None, description="Food slot type filter"),
    min_health_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum Health Score v2"),
    exclude_allergens: Optional[List[str]] = Query(None, description="Allergens to exclude"),
    dietary_tags: Optional[List[str]] = Query(
        None, description="Dietary tags e.g. vegan, low_sodium"
    ),
    strict_allergens: bool = Query(True, description="Strict tri-state allergen safety"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size limit"),
) -> FoodSearchResponse:
    """Search catalog foods with allergen screening, dietary tags, and pagination."""
    db = get_food_db()
    offset = (page - 1) * page_size

    total_matches = db.count_matching_foods(
        query=q,
        category=category,
        food_type=food_type,
        min_health_score=min_health_score,
        exclude_allergens=exclude_allergens,
        dietary_tags=dietary_tags,
        strict_allergens=strict_allergens,
    )

    rows = db.search_foods(
        query=q,
        category=category,
        food_type=food_type,
        min_health_score=min_health_score,
        exclude_allergens=exclude_allergens,
        dietary_tags=dietary_tags,
        strict_allergens=strict_allergens,
        limit=page_size,
        offset=offset,
    )

    results = [_row_to_food_item(r) for r in rows]

    return FoodSearchResponse(
        total_matches=total_matches,
        page=page,
        page_size=page_size,
        results=results,
    )


@router.get("/{food_id}/swaps", response_model=FoodSwapResponse)
def get_food_swaps(
    food_id: str,
    max_swaps: int = Query(5, ge=1, le=20, description="Maximum number of swap alternatives"),
    strict_allergens: bool = Query(True, description="Enforce strict tri-state allergen safety"),
) -> FoodSwapResponse:
    """Identify strictly healthier same-category alternatives for a given food."""
    db = get_food_db()
    original = db.get_food_by_id(food_id)
    if not original:
        raise HTTPException(status_code=404, detail=f"Food ID '{food_id}' not found in database.")

    raw_swaps = find_healthier_swaps(
        food_id_or_record=food_id,
        strict_allergens=strict_allergens,
        top_n=max_swaps,
    )

    formatted_swaps = []
    for s in raw_swaps:
        formatted_swaps.append(
            FoodSwapItem(
                food_id=s["food_id"],
                name=s["name"],
                category=s.get("category", "Other"),
                health_score_v2=round(float(s.get("health_score_v2", 0.0)), 1),
                score_improvement=round(float(s.get("score_improvement", 0.0)), 1),
                kcal_diff=round(float(s.get("kcal_diff", 0.0)), 1),
                sodium_diff_mg=round(float(s.get("sodium_diff_mg", 0.0)), 1),
                sugar_diff_g=round(float(s.get("sugar_diff_g", 0.0)), 1),
                sat_fat_diff_g=round(float(s.get("sat_fat_diff_g", 0.0)), 1),
                reasons=s.get("reasons", []),
            )
        )

    return FoodSwapResponse(
        original_food={
            "food_id": original["food_id"],
            "name": original["name"],
            "category": original["category"],
            "health_score_v2": original["health_score_v2"],
            "kcal_100g": original["kcal_100g"],
            "sodium_mg_100g": original["sodium_mg_100g"],
            "sugar_100g": original["sugar_100g"],
        },
        count=len(formatted_swaps),
        swaps=formatted_swaps,
    )
