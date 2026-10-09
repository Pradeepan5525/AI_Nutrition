"""Page 3: PuLP Linear Programming Meal Plan Optimizer, Swaps & Grocery List."""

from __future__ import annotations

import streamlit as st

from app.ui_components import (
    init_session_state,
    inject_custom_css,
    render_auth_sidebar,
    render_hero,
    render_medical_disclaimer,
)
from nutri.foods.swaps import find_healthier_swaps
from nutri.plan.grocery import aggregate_grocery_list
from nutri.plan.optimizer import generate_meal_plan
from nutri.reports.pdf import generate_nutrition_pdf

st.set_page_config(
    page_title="My Diet Plan - Nutrition Intelligence", page_icon="📋", layout="wide"
)

inject_custom_css()
init_session_state()
render_auth_sidebar()
render_medical_disclaimer()

render_hero(
    title="📋 Personalized Linear Programming Meal Plan",
    subtitle=(
        "Synthesize mathematically balanced, single-day or 7-day meal schedules using "
        "mixed-integer linear programming (PuLP). Guarantees exact caloric targets (±5%), "
        "strict allergen safety, and clinical nutrient limits."
    ),
)

profile = st.session_state.user_profile
assess = st.session_state.assessment_result

# Determine default targets
default_kcal = float(assess["target_kcal"]) if assess else 2000.0
default_prot = float(assess["macros"]["protein_g"]) if assess else 110.0
default_sod = float(assess["micros"]["max_sodium_mg"]) if assess else 2300.0
default_sat_fat = float(assess["micros"]["max_sat_fat_g"]) if assess else 22.0
default_sugar = float(assess["micros"]["max_added_sugar_g"]) if assess else 50.0

# Sidebar controls
st.sidebar.header("⚙️ Optimization Parameters")
days = st.sidebar.radio("Plan Duration", options=[1, 7], format_func=lambda x: f"{x}-Day Schedule")

target_kcal = st.sidebar.number_input(
    "Target Daily Calories (kcal)",
    min_value=1200.0,
    max_value=4000.0,
    value=default_kcal,
    step=50.0,
    help="Guaranteed within ±5% tolerance by the mathematical solver.",
)

protein_target_g = st.sidebar.number_input(
    "Protein Floor Target (g)",
    min_value=30.0,
    max_value=250.0,
    value=default_prot,
    step=5.0,
)

max_sodium_mg = st.sidebar.number_input(
    "Max Daily Sodium (mg)",
    min_value=500.0,
    max_value=3500.0,
    value=default_sod,
    step=100.0,
    help="AHA DASH standard restricts sodium to <= 1,500 mg.",
)

max_sat_fat_g = st.sidebar.number_input(
    "Max Saturated Fat (g)",
    min_value=3.0,
    max_value=50.0,
    value=default_sat_fat,
    step=1.0,
)

max_sugar_g = st.sidebar.number_input(
    "Max Added Sugar (g)",
    min_value=5.0,
    max_value=100.0,
    value=default_sugar,
    step=2.0,
)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Safety & Preferences")

ALLERGEN_OPTIONS = ["peanuts", "gluten", "dairy", "soy", "eggs", "fish", "nuts"]
user_allergies = st.sidebar.multiselect(
    "Strict Allergen Exclusions",
    options=ALLERGEN_OPTIONS,
    default=profile.get("allergies", []),
    help="Strict tri-state verification: foods with 'present' or 'unknown' status are strictly excluded.",
)

strict_allergens = st.sidebar.checkbox(
    "Enforce Strict Tri-State Verification",
    value=True,
    help="When enabled, foods with unverified allergen status ('unknown') are treated as UNSAFE.",
)

DIETARY_OPTIONS = ["vegetarian", "vegan", "low_sodium", "low_sugar"]
dietary_restrictions = st.sidebar.multiselect(
    "Dietary Restrictions",
    options=DIETARY_OPTIONS,
    default=profile.get("dietary_restrictions", []),
)

# Run Optimization Button
generate_btn = st.button(
    "⚡ Solve Optimal Meal Schedule (PuLP MILP)", type="primary", use_container_width=True
)

if generate_btn:
    with st.spinner("Formulating Mixed-Integer Linear Program and solving with CBC..."):
        try:
            plan_res = generate_meal_plan(
                target_kcal=target_kcal,
                protein_target_g=protein_target_g,
                max_sodium_mg=max_sodium_mg,
                max_sat_fat_g=max_sat_fat_g,
                max_sugar_g=max_sugar_g,
                user_allergies=user_allergies,
                dietary_restrictions=dietary_restrictions,
                strict_allergens=strict_allergens,
                days=days,
            )
            grocery_res = aggregate_grocery_list(plan_res)
            st.session_state.meal_plan_result = {
                "plan": plan_res,
                "grocery": grocery_res,
            }
            st.success(f"✨ Optimal meal plan solved in {plan_res['solve_time_sec']:.2f} seconds!")
        except Exception as e:
            st.error(f"Solver Error: {str(e)}")

# Display Plan if available
if st.session_state.meal_plan_result is not None:
    plan_data = st.session_state.meal_plan_result["plan"]
    grocery_data = st.session_state.meal_plan_result["grocery"]
    daily_plans = plan_data.get("daily_plans", [])

    if not daily_plans:
        st.warning("No feasible plan found. Try relaxing allergen or sodium constraints.")
    else:
        # Day Tabs if multi-day
        if len(daily_plans) > 1:
            day_tabs = st.tabs([f"Day {dp['day_number']}" for dp in daily_plans])
        else:
            day_tabs = [st.container()]

        for tab_idx, tab in enumerate(day_tabs):
            with tab:
                curr_plan = daily_plans[tab_idx]
                day_num = curr_plan.get("day_number", tab_idx + 1)
                totals = curr_plan["daily_totals"]
                err_pct = curr_plan.get("calorie_error_pct", 0.0)

                # Day summary KPIs
                k1, k2, k3, k4, k5 = st.columns(5)
                k1.metric(
                    "Energy Intake", f"{totals['kcal']:.0f} kcal", f"{err_pct:+.1f}% vs Target"
                )
                k2.metric(
                    "Protein", f"{totals['protein_g']:.0f} g", f"Floor: {protein_target_g:.0f}g"
                )
                k3.metric(
                    "Carbohydrates",
                    f"{totals['carbs_g']:.0f} g",
                    f"Fiber: {totals['fiber_g']:.0f}g",
                )
                k4.metric(
                    "Dietary Fat", f"{totals['fat_g']:.0f} g", f"Sat: {totals['sat_fat_g']:.0f}g"
                )
                k5.metric("Sodium", f"{totals['sodium_mg']:.0f} mg", f"Cap: {max_sodium_mg:.0f}mg")

                if curr_plan.get("relaxation_log"):
                    with st.expander("ℹ️ Applied Constraint Relaxations"):
                        for r in curr_plan["relaxation_log"]:
                            st.write(f"- {r}")

                st.markdown("<br/>", unsafe_allow_html=True)

                # Meal Slots
                meals = curr_plan.get("meals", {})
                for slot in ["breakfast", "lunch", "dinner", "snack"]:
                    items = meals.get(slot, [])
                    slot_kcal = sum(it.get("kcal", 0) for it in items)
                    st.markdown(
                        f"""
                        <div class="meal-slot-header">
                            {slot.capitalize()} &nbsp; • &nbsp; <span style="font-weight:400; font-size:0.95rem; color:#475569">{slot_kcal:.0f} kcal ({len(items)} items)</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    for _item_idx, itm in enumerate(items):
                        c_name, c_portion, c_macros, c_score, c_swap = st.columns(
                            [3, 1.2, 3, 1.2, 1.6]
                        )
                        with c_name:
                            st.markdown(f"**{itm['name']}**")
                            st.caption(
                                f"Category: {itm.get('category', 'Other')} | Type: {itm.get('food_type', 'Other')}"
                            )
                        with c_portion:
                            st.markdown(f"**{itm['portion_g']:.0f} g**")
                            st.caption(f"{itm['kcal']:.0f} kcal")
                        with c_macros:
                            st.caption(
                                f"P: {itm['protein_g']:.1f}g • C: {itm['carbs_g']:.1f}g • "
                                f"F: {itm['fat_g']:.1f}g • Na: {itm['sodium_mg']:.0f}mg"
                            )
                        with c_score:
                            hs = itm.get("health_score_v2", 50.0)
                            color_tag = (
                                "#166534" if hs >= 65 else ("#b45309" if hs >= 45 else "#991b1b")
                            )
                            st.markdown(
                                f"<span style='color:{color_tag}; font-weight:700'>Score: {hs:.1f}</span>",
                                unsafe_allow_html=True,
                            )

                        with c_swap:
                            with st.popover("🔄 Swaps"):
                                st.write(f"**Healthier Alternatives for {itm['name'][:25]}:**")
                                swaps = find_healthier_swaps(
                                    itm["food_id"], user_allergies=user_allergies, top_n=3
                                )
                                if swaps:
                                    for s in swaps:
                                        st.markdown(f"**{s.get('name', 'Alternative Item')}**")
                                        imp = s.get("score_improvement") or (s.get("swap_diff", {}).get("delta_health_score", 0.0))
                                        k_diff = s.get("kcal_diff") or (s.get("swap_diff", {}).get("delta_kcal_100g", 0.0))
                                        na_diff = s.get("sodium_diff_mg") or (s.get("swap_diff", {}).get("delta_sodium_mg_100g", 0.0))
                                        st.caption(
                                            f"Score: +{imp:.1f} | Δ kcal: {k_diff:+.0f} | Δ Na: {na_diff:+.0f}mg"
                                        )
                                        st.markdown("---")
                                else:
                                    st.write(
                                        "No higher-scoring same-category swaps found (already optimal)."
                                    )

        st.divider()

        # Department-Grouped Grocery List Section
        st.subheader("🛒 Consolidated Grocery Shopping List")
        st.write(
            f"Aggregated across all {len(daily_plans)} days of the meal plan. "
            f"**Total estimated purchase weight:** **{grocery_data.get('total_weight_kg', 0):.2f} kg** "
            f"({grocery_data.get('total_unique_items', 0)} unique ingredients)."
        )

        dept_cols = st.columns(3)
        depts = grocery_data.get("departments", {})
        for idx, (dept_name, items_list) in enumerate(depts.items()):
            col_target = dept_cols[idx % 3]
            with col_target:
                with st.expander(f"📦 {dept_name} ({len(items_list)} items)", expanded=True):
                    for itm in items_list:
                        st.markdown(f"- **{itm['name']}**: `{itm['display_quantity']}`")

        st.divider()

        # PDF Report Download Section
        st.subheader("📥 Export Clinical Summary Report")
        st.write(
            "Generate a publication-grade, 2-page clinical PDF summary with patient demographics, risk screening, meal plan tables, and grocery checklist."
        )

        # Prepare export bundle
        export_bundle = {
            "client_info": {
                "age": profile.get("age", 28),
                "sex": profile.get("sex", "female"),
                "height_cm": profile.get("height_cm", 165.0),
                "weight_kg": profile.get("weight_kg", 60.0),
                "bmi": assess.get("bmi", 22.0) if assess else 22.0,
                "bmi_category": assess.get("bmi_category", "Normal weight")
                if assess
                else "Normal weight",
                "bmr": assess.get("bmr", 1400.0) if assess else 1400.0,
                "tdee": assess.get("tdee", 1900.0) if assess else 1900.0,
            },
            "target_nutrition": {
                "target_kcal": target_kcal,
                "protein_g": protein_target_g,
                "carbs_g": round((target_kcal - protein_target_g * 4 - max_sat_fat_g * 9) / 4),
                "fat_g": round(target_kcal * 0.28 / 9),
                "fiber_g": round(target_kcal * 14 / 1000),
                "sugar_g": max_sugar_g,
                "water_ml": round(float(profile.get("weight_kg", 60.0)) * 35.0),
            },
            "safety_gate": {
                "cleared": assess.get("safety_status", {}).get("safe_for_automated_plan", True)
                if assess
                else True,
                "flags": assess.get("safety_status", {}).get("blockers", []) if assess else [],
            },
            "clinical_rules": {
                "active_rules": profile.get("condition_flags", []),
            },
            "risk_screening": st.session_state.risk_result,
            "meal_plan": plan_data,
            "grocery_list": grocery_data,
        }

        try:
            pdf_bytes = generate_nutrition_pdf(export_bundle)
            st.download_button(
                label="📄 Download 2-Page Clinical Nutrition Report (PDF)",
                data=pdf_bytes,
                file_name="clinical_nutrition_intelligence_report.pdf",
                mime="application/pdf",
                type="primary",
            )
        except Exception as e:
            st.error(f"PDF compilation error: {str(e)}")
