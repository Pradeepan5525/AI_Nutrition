"""Assessment router for metabolic calculations, guidelines, and safety gating."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import AssessRequest, AssessResponse
from nutri.assess.bmi import calculate_bmi, calculate_ideal_weight_range, get_bmi_category
from nutri.assess.energy import calculate_bmr, calculate_tdee
from nutri.assess.targets import calculate_nutrient_targets
from nutri.rules.conditions import resolve_clinical_rules
from nutri.rules.safety import evaluate_safety_gate

router = APIRouter(prefix="/assess", tags=["Assessment"])

DISCLAIMER_TEXT = (
    "Educational and nutritional intelligence calculation only. "
    "Not medical advice. Consult a healthcare provider before making major dietary adjustments."
)


@router.post("", response_model=AssessResponse)
def assess_user_profile(payload: AssessRequest) -> AssessResponse:
    """Perform comprehensive anthropometric, metabolic, and clinical safety assessment."""
    try:
        bmi = calculate_bmi(weight_kg=payload.weight_kg, height_cm=payload.height_cm)
        bmi_res = get_bmi_category(bmi=bmi, use_asian_cutoffs=payload.is_asian)
        min_wt, max_wt = calculate_ideal_weight_range(
            height_cm=payload.height_cm, use_asian_cutoffs=payload.is_asian
        )

        bmr = calculate_bmr(
            weight_kg=payload.weight_kg,
            height_cm=payload.height_cm,
            age=payload.age,
            sex=payload.sex,
        )
        tdee = calculate_tdee(bmr=bmr, activity_level=payload.activity_level)

        goal_map = {
            "weight_loss": "lose",
            "muscle_gain": "gain",
            "maintenance": "maintain",
        }
        nutri_goal = goal_map.get(payload.goal, "maintain")

        targets = calculate_nutrient_targets(
            tdee=tdee,
            weight_kg=payload.weight_kg,
            sex=payload.sex,
            goal=nutri_goal,
        )

        # Apply clinical guidelines and conflict resolution
        clinical_result = resolve_clinical_rules(
            active_conditions=payload.condition_flags,
            active_restrictions=payload.dietary_restrictions,
            base_targets=targets,
            weight_kg=payload.weight_kg,
        )

        adj_targets = clinical_result["adjusted_targets"]
        adj_macros = adj_targets["macros"]
        adj_micros = adj_targets["micros_and_guidance"]

        target_kcal = float(adj_targets["target_kcal"])
        deficit_or_surplus = round(target_kcal - tdee, 1)

        macro_dict = {
            "carbs_g": adj_macros["carbs_g"],
            "protein_g": adj_macros["protein_g"],
            "fat_g": adj_macros["fat_g"],
            "fiber_g": adj_micros["fiber_g"],
            "sugar_max_g": adj_micros["max_added_sugar_g"],
        }
        water_ml = float(adj_micros["daily_water_ml"])

        # Safety gate evaluation
        safety_status = evaluate_safety_gate(
            age=payload.age,
            bmi=bmi,
            weight_kg=payload.weight_kg,
            height_cm=payload.height_cm,
            is_pregnant=payload.is_pregnant,
            is_breastfeeding=payload.is_lactating,
            eating_disorder_history=payload.has_ed_history,
            goal=nutri_goal,
        )

        all_flags = safety_status["blockers"] + safety_status["advisories"]
        guidance_msg = (
            safety_status["blockers"][0]
            if safety_status["blockers"]
            else (
                safety_status["advisories"][0]
                if safety_status["advisories"]
                else "Standard automated planning cleared."
            )
        )

        return AssessResponse(
            bmi=bmi,
            bmi_category=bmi_res["category"],
            ideal_weight_min_kg=min_wt,
            ideal_weight_max_kg=max_wt,
            bmr_kcal=bmr,
            tdee_kcal=tdee,
            target_kcal=target_kcal,
            deficit_or_surplus_kcal=deficit_or_surplus,
            macros=macro_dict,
            water_ml=water_ml,
            safety_gate={
                "cleared": safety_status["safe_for_automated_plan"]
                and not safety_status["withhold_aggressive_targets"],
                "flags": all_flags,
                "guidance": guidance_msg,
            },
            clinical_constraints={
                "active_conditions": payload.condition_flags,
                "max_sodium_mg": adj_micros["max_sodium_mg"],
                "max_sat_fat_g": adj_micros["max_sat_fat_g"],
                "max_sugar_g": adj_micros["max_added_sugar_g"],
                "min_fiber_g": adj_micros["fiber_g"],
                "audit_trail": clinical_result["audit_trail"],
                "clinical_guidance": clinical_result["clinical_guidance"],
            },
            disclaimer=DISCLAIMER_TEXT,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Assessment calculation error: {str(e)}"
        ) from e
