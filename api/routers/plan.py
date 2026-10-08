"""Meal planning optimizer router providing 1-day and 7-day LP-optimized schedules."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import PlanRequest, PlanResponse
from nutri.plan.grocery import aggregate_grocery_list
from nutri.plan.optimizer import generate_meal_plan

router = APIRouter(prefix="/plan", tags=["Meal Optimization"])

PLAN_DISCLAIMER = (
    "Algorithmic meal optimization provides balanced nutritional templates. "
    "Check individual packaged ingredients for exact allergen warnings before consumption."
)


@router.post("", response_model=PlanResponse)
def optimize_meal_plan(payload: PlanRequest) -> PlanResponse:
    """Solve mixed-integer linear program to generate personalized daily or 7-day meal plans."""
    try:
        plan_result = generate_meal_plan(
            target_kcal=payload.target_kcal,
            protein_target_g=payload.protein_target_g,
            max_sodium_mg=payload.max_sodium_mg,
            max_sat_fat_g=payload.max_sat_fat_g,
            max_sugar_g=payload.max_sugar_g,
            user_allergies=payload.user_allergies,
            dietary_restrictions=payload.dietary_restrictions,
            strict_allergens=payload.strict_allergens,
            days=payload.days,
        )

        daily_plans = plan_result.get("daily_plans", [])
        if not daily_plans:
            raise HTTPException(
                status_code=422,
                detail="Could not formulate a feasible meal plan under the requested constraints. "
                "Try relaxing allergen or dietary restrictions.",
            )

        grocery_list = aggregate_grocery_list(plan_result)

        return PlanResponse(
            days_requested=payload.days,
            daily_plans=daily_plans,
            grocery_list=grocery_list,
            solver_status="Optimal (or Relaxed Feasible)" if daily_plans else "Infeasible",
            solver_time_sec=plan_result.get("solve_time_sec", 0.0),
            disclaimer=PLAN_DISCLAIMER,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Meal plan optimization failure: {str(e)}"
        ) from e
