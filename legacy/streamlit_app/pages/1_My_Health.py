"""Page 1: Anthropometric, Metabolic, and Clinical Safety Assessment."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.ui_components import (
    init_session_state,
    inject_custom_css,
    render_auth_sidebar,
    render_hero,
    render_medical_disclaimer,
)
from nutri.assess.bmi import calculate_bmi, calculate_ideal_weight_range, get_bmi_category
from nutri.assess.energy import calculate_bmr, calculate_tdee
from nutri.assess.targets import calculate_nutrient_targets
from nutri.rules.conditions import resolve_clinical_rules
from nutri.rules.safety import evaluate_safety_gate

st.set_page_config(
    page_title="My Health Assessment - Nutrition Intelligence", page_icon="🩺", layout="wide"
)

inject_custom_css()
init_session_state()
render_auth_sidebar()
render_medical_disclaimer()

render_hero(
    title="🩺 Anthropometric & Clinical Health Assessment",
    subtitle="Evidence-based metabolic baseline, BMI classification, safety screening, and personalized macro targets.",
)

# Load profile from session state
profile = st.session_state.user_profile

st.sidebar.header("👤 Client Demographics & Goals")
age = st.sidebar.number_input(
    "Age (years)", min_value=12, max_value=110, value=int(profile.get("age", 28))
)
sex = st.sidebar.selectbox(
    "Biological Sex", options=["female", "male"], index=0 if profile.get("sex") == "female" else 1
)
height_cm = st.sidebar.number_input(
    "Height (cm)",
    min_value=100.0,
    max_value=230.0,
    value=float(profile.get("height_cm", 165.0)),
    step=0.5,
)
weight_kg = st.sidebar.number_input(
    "Weight (kg)",
    min_value=30.0,
    max_value=250.0,
    value=float(profile.get("weight_kg", 60.0)),
    step=0.5,
)

activity_levels = ["sedentary", "light", "moderate", "active", "very_active"]
activity_level = st.sidebar.selectbox(
    "Activity Level",
    options=activity_levels,
    index=activity_levels.index(profile.get("activity_level", "moderate")),
    help="Sedentary: Desk job; Light: 1-3 days/wk; Moderate: 3-5 days/wk; Active: 6-7 days/wk; Very Active: Physical job/2x day",
)

goals = ["maintenance", "weight_loss", "muscle_gain"]
goal = st.sidebar.selectbox(
    "Primary Dietary Goal",
    options=goals,
    index=goals.index(profile.get("goal", "maintenance")),
    format_func=lambda x: x.replace("_", " ").title(),
)

is_asian = st.sidebar.checkbox(
    "Use Asian-Specific BMI Cut-offs (WHO 2004)",
    value=bool(profile.get("is_asian", False)),
    help="Recommended by WHO Expert Consultation for individuals of South/East Asian ancestry (Overweight at >=23, Obese at >=27.5).",
)

st.sidebar.markdown("---")
st.sidebar.subheader("Clinical Conditions & History")
has_hypertension = st.sidebar.checkbox(
    "Hypertension / High Blood Pressure", value="hypertension" in profile.get("condition_flags", [])
)
has_diabetes = st.sidebar.checkbox(
    "Type 2 Diabetes", value="diabetes" in profile.get("condition_flags", [])
)
has_cholesterol = st.sidebar.checkbox(
    "High Cholesterol / Dyslipidemia",
    value="high_cholesterol" in profile.get("condition_flags", []),
)

st.sidebar.markdown("---")
st.sidebar.subheader("Safety Gate Flags")
is_pregnant = st.sidebar.checkbox("Currently Pregnant", value=False)
is_lactating = st.sidebar.checkbox("Currently Lactating / Nursing", value=False)
has_ed = st.sidebar.checkbox("History of Eating Disorders", value=False)

# Update state
condition_flags = []
if has_hypertension:
    condition_flags.append("hypertension")
if has_diabetes:
    condition_flags.append("diabetes")
if has_cholesterol:
    condition_flags.append("high_cholesterol")

st.session_state.user_profile.update(
    {
        "age": age,
        "sex": sex,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "activity_level": activity_level,
        "goal": goal,
        "is_asian": is_asian,
        "condition_flags": condition_flags,
    }
)

# Compute core calculations
bmi = calculate_bmi(weight_kg=weight_kg, height_cm=height_cm)
bmi_res = get_bmi_category(bmi=bmi, use_asian_cutoffs=is_asian)
min_wt, max_wt = calculate_ideal_weight_range(height_cm=height_cm, use_asian_cutoffs=is_asian)

bmr = calculate_bmr(weight_kg=weight_kg, height_cm=height_cm, age=age, sex=sex)
tdee = calculate_tdee(bmr=bmr, activity_level=activity_level)

goal_map = {"weight_loss": "lose", "muscle_gain": "gain", "maintenance": "maintain"}
nutri_goal = goal_map.get(goal, "maintain")
base_targets = calculate_nutrient_targets(tdee=tdee, weight_kg=weight_kg, sex=sex, goal=nutri_goal)

clinical_res = resolve_clinical_rules(
    active_conditions=condition_flags,
    active_restrictions=profile.get("dietary_restrictions", []),
    base_targets=base_targets,
    weight_kg=weight_kg,
)

adj_targets = clinical_res["adjusted_targets"]
adj_macros = adj_targets["macros"]
adj_micros = adj_targets["micros_and_guidance"]

safety_status = evaluate_safety_gate(
    age=age,
    bmi=bmi,
    weight_kg=weight_kg,
    height_cm=height_cm,
    is_pregnant=is_pregnant,
    is_breastfeeding=is_lactating,
    eating_disorder_history=has_ed,
    goal=nutri_goal,
)

# Cache result in session state
st.session_state.assessment_result = {
    "bmi": bmi,
    "bmi_category": bmi_res["category"],
    "min_weight": min_wt,
    "max_weight": max_wt,
    "bmr": bmr,
    "tdee": tdee,
    "target_kcal": adj_targets["target_kcal"],
    "macros": adj_macros,
    "micros": adj_micros,
    "safety_status": safety_status,
    "clinical_res": clinical_res,
}

# --- SECTION 1: SAFETY GATE BANNER ---
all_flags = safety_status["blockers"] + safety_status["advisories"]
if safety_status["blockers"]:
    st.error(
        f"🚨 **Safety Gate Active (Action Required):** {safety_status['blockers'][0]}\n\n"
        "Automated restrictive diet plans are suspended. Please seek direct medical evaluation."
    )
elif safety_status["advisories"]:
    st.warning(
        f"⚠️ **Clinical Advisory Flagged:** {safety_status['advisories'][0]}\n\n"
        "Conservative maintenance parameters applied."
    )
else:
    st.success(
        "✅ **Safety Gate Cleared:** Client profile cleared for automated evidence-based dietary planning."
    )

st.markdown("<br/>", unsafe_allow_html=True)

# --- SECTION 2: BMI & METABOLIC KPI ROW ---
col_bmi, col_bmr, col_tdee, col_tgt = st.columns(4)
with col_bmi:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Body Mass Index (BMI)</div>
            <div class="kpi-val">{bmi:.1f}</div>
            <div class="kpi-sub"><b>{bmi_res["category"]}</b> ({"Asian" if is_asian else "WHO"})</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_bmr:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Basal Metabolic Rate</div>
            <div class="kpi-val">{bmr:.0f} <span style="font-size:0.9rem">kcal</span></div>
            <div class="kpi-sub">Mifflin-St Jeor Formula</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_tdee:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Maintenance (TDEE)</div>
            <div class="kpi-val">{tdee:.0f} <span style="font-size:0.9rem">kcal</span></div>
            <div class="kpi-sub">{activity_level.capitalize()} multiplier</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_tgt:
    diff = round(adj_targets["target_kcal"] - tdee)
    diff_str = f"{diff:+d} kcal ({goal.replace('_', ' ')})"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Daily Target Energy</div>
            <div class="kpi-val">{adj_targets["target_kcal"]:.0f} <span style="font-size:0.9rem">kcal</span></div>
            <div class="kpi-sub">{diff_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br/>", unsafe_allow_html=True)

# --- SECTION 3: VISUAL GAUGES & MACRO BREAKDOWN ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("📊 BMI Classification Gauge")

    # Interactive Plotly Gauge
    max_gauge = 40.0 if not is_asian else 35.0
    normal_end = 22.9 if is_asian else 24.9
    overweight_end = 27.4 if is_asian else 29.9

    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=bmi,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"BMI ({bmi_res['category']})", "font": {"size": 18}},
            gauge={
                "axis": {"range": [14, max_gauge], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": "#0f172a", "thickness": 0.25},
                "bgcolor": "white",
                "borderwidth": 1,
                "bordercolor": "#cbd5e1",
                "steps": [
                    {"range": [14, 18.5], "color": "#93c5fd"},  # Underweight blue
                    {"range": [18.5, normal_end], "color": "#86efac"},  # Normal green
                    {
                        "range": [normal_end, overweight_end],
                        "color": "#fde047",
                    },  # Overweight yellow
                    {"range": [overweight_end, max_gauge], "color": "#fca5a5"},  # Obese red
                ],
            },
        )
    )
    fig_gauge.update_layout(height=260, margin={"l": 20, "r": 20, "t": 30, "b": 20})
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.info(
        f"💡 **Ideal Healthy Weight Range for {height_cm:.0f} cm:** "
        f"**{min_wt:.1f} kg – {max_wt:.1f} kg** (based on normal BMI bounds 18.5 – {normal_end})."
    )

with right_col:
    st.subheader("🥗 Macronutrient Energy Distribution")

    carbs_g = adj_macros["carbs_g"]
    prot_g = adj_macros["protein_g"]
    fat_g = adj_macros["fat_g"]

    macro_fig = go.Figure(
        data=[
            go.Pie(
                labels=["Carbohydrates", "Protein", "Dietary Fat"],
                values=[carbs_g * 4, prot_g * 4, fat_g * 9],
                hole=0.55,
                marker={"colors": ["#3b82f6", "#10b981", "#f59e0b"]},
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )
        ]
    )
    macro_fig.update_layout(
        height=260,
        margin={"l": 20, "r": 20, "t": 10, "b": 20},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.2, "xanchor": "center", "x": 0.5},
    )
    st.plotly_chart(macro_fig, use_container_width=True)

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Carbs",
        f"{carbs_g:.0f} g",
        f"{round(carbs_g * 4 / adj_targets['target_kcal'] * 100)}% kcal",
    )
    m2.metric(
        "Protein",
        f"{prot_g:.0f} g",
        f"{round(prot_g * 4 / adj_targets['target_kcal'] * 100)}% kcal",
    )
    m3.metric(
        "Fat", f"{fat_g:.0f} g", f"{round(fat_g * 9 / adj_targets['target_kcal'] * 100)}% kcal"
    )

st.divider()

# --- SECTION 4: CLINICAL GUIDELINES AUDIT TRAIL ---
st.subheader("📋 Active Evidence-Based Clinical Guidelines")

if condition_flags:
    st.write("Clinical guidelines actively modifying nutrient thresholds for this profile:")
    audit_data = []
    for k, info in clinical_res["audit_trail"].items():
        audit_data.append(
            {
                "Nutrient Bound": k.replace("_", " ").title(),
                "Effective Limit": f"{info['final_value']} {info['unit']}",
                "Ruling Guideline": info["ruling_condition"],
                "Citation": info["citation"],
                "Clinical Rationale": info["reason"],
            }
        )
    st.dataframe(audit_data, use_container_width=True, hide_index=True)
else:
    st.info(
        "No chronic condition flags selected. System applies standard general population healthy guidelines: "
        "Sodium ≤ 2,300 mg/day (DGA), Fiber ≥ 14 g/1,000 kcal, Added Sugar ≤ 10% energy, Saturated Fat ≤ 10%."
    )

# Micronutrient and Hydration Guidance row
st.markdown("#### Additional Essential Guidance")
g1, g2, g3 = st.columns(3)
g1.info(
    f"🌾 **Dietary Fiber Target:** **≥ {adj_micros['fiber_g']:.0f} g/day** (Promotes satiety and glycemic control)"
)
g2.info(
    f"🍯 **Added Sugar Ceiling:** **≤ {adj_micros['max_added_sugar_g']:.0f} g/day** (WHO / ADA chronic prevention)"
)
g3.info(
    f"💧 **Hydration Target:** **~{adj_micros['daily_water_liters']:.1f} Liters/day** ({adj_micros['daily_water_ml']} mL)"
)

st.markdown("<br/>", unsafe_allow_html=True)
st.caption(
    "Proceed to **2_Risk_Check** or **3_My_Diet_Plan** in the sidebar to generate tailored meal schedules."
)
