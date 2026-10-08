"""Page 2: Calibrated Lifestyle Obesity Risk Screening with SHAP Explainability."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.ui_components import (
    init_session_state,
    inject_custom_css,
    render_hero,
    render_medical_disclaimer,
)
from nutri.models.predict import predict_obesity_risk

st.set_page_config(
    page_title="Lifestyle Risk Check - Nutrition Intelligence", page_icon="📊", layout="wide"
)

inject_custom_css()
init_session_state()
render_medical_disclaimer()

render_hero(
    title="📊 Multi-Factor Lifestyle Risk Screening",
    subtitle=(
        "Screen behavioral and demographic lifestyle habits for obesity risk predisposition. "
        "Anthropometric measurements (Height, Weight, BMI) are strictly excluded to avoid circularity."
    ),
)

profile = st.session_state.user_profile

st.markdown(
    """
    > **Methodological Standard:** This clinical screening tool isolates **modifiable dietary, activity, and environmental habits**
    > from current body size. We evaluate behavioral predisposition rather than measuring body size twice.
    """
)

# 14 Lifestyle Questionnaire Inputs
with st.form("risk_assessment_form"):
    st.subheader("1. Dietary & Snacking Behaviors")
    c1, c2, c3 = st.columns(3)
    with c1:
        favc = st.selectbox(
            "Frequent consumption of high-calorie food (FAVC)?",
            options=["no", "yes"],
            help="Frequent intake of fried, fast, or energy-dense processed foods.",
        )
    with c2:
        fcvc = st.slider(
            "Vegetable intake frequency (FCVC)",
            min_value=1.0,
            max_value=3.0,
            value=2.0,
            step=0.5,
            help="1.0 = Never/Rarely, 2.0 = Sometimes, 3.0 = Always / With every meal",
        )
    with c3:
        ncp = st.slider(
            "Number of main daily meals (NCP)",
            min_value=1.0,
            max_value=4.0,
            value=3.0,
            step=1.0,
            help="Number of dedicated sit-down meals per day.",
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        caec = st.selectbox(
            "Consumption of food between meals (CAEC)?",
            options=["no", "Sometimes", "Frequently", "Always"],
            index=1,
            help="Snacking patterns between breakfast, lunch, and dinner.",
        )
    with c5:
        ch2o = st.slider(
            "Daily water intake (CH2O scale)",
            min_value=1.0,
            max_value=3.0,
            value=2.0,
            step=0.5,
            help="1.0 = < 1 Liter, 2.0 = 1 to 2 Liters, 3.0 = > 2 Liters",
        )
    with c6:
        scc = st.selectbox(
            "Do you monitor your daily calorie intake (SCC)?",
            options=["no", "yes"],
            help="Regular tracking of nutritional consumption.",
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("2. Physical Activity & Daily Habits")
    c7, c8, c9 = st.columns(3)
    with c7:
        faf = st.slider(
            "Physical activity frequency (FAF scale)",
            min_value=0.0,
            max_value=3.0,
            value=1.0,
            step=0.5,
            help="0.0 = Sedentary, 1.0 = 1-2 days/week, 2.0 = 2-4 days/week, 3.0 = 4-5+ days/week",
        )
    with c8:
        tue = st.slider(
            "Recreational screen/device time (TUE scale)",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.5,
            help="0.0 = 0 to 2 hours, 1.0 = 3 to 5 hours, 2.0 = > 5 hours per day",
        )
    with c9:
        mtrans = st.selectbox(
            "Primary mode of daily transportation (MTRANS)",
            options=["Public_Transportation", "Automobile", "Walking", "Motorbike", "Bike"],
            help="Transportation mode determining incidental daily activity.",
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("3. Demographics, Family History & Substances")
    c10, c11, c12 = st.columns(3)
    with c10:
        fam_history = st.selectbox(
            "Family history of overweight or obesity?",
            options=["yes", "no"],
            index=0,
            help="First-degree relatives with diagnosed obesity or overweight history.",
        )
    with c11:
        smoke = st.selectbox(
            "Smoking habit (SMOKE)?",
            options=["no", "yes"],
            help="Current regular tobacco cigarette smoking.",
        )
    with c12:
        calc = st.selectbox(
            "Alcohol consumption frequency (CALC)?",
            options=["no", "Sometimes", "Frequently", "Always"],
            index=1,
            help="Frequency of alcoholic beverage intake.",
        )

    submit_btn = st.form_submit_button(
        "🔍 Run Calibrated Risk Model Screening", use_container_width=True
    )

if submit_btn or st.session_state.risk_result is not None:
    # Build feature dictionary
    user_habits = {
        "Age": float(profile.get("age", 28)),
        "Gender": str(profile.get("sex", "female")).capitalize(),
        "family_history_with_overweight": fam_history
        if submit_btn
        else st.session_state.risk_result["inputs"].get("family_history_with_overweight", "yes"),
        "FAVC": favc if submit_btn else st.session_state.risk_result["inputs"].get("FAVC", "yes"),
        "FCVC": fcvc if submit_btn else st.session_state.risk_result["inputs"].get("FCVC", 2.0),
        "NCP": ncp if submit_btn else st.session_state.risk_result["inputs"].get("NCP", 3.0),
        "CAEC": caec
        if submit_btn
        else st.session_state.risk_result["inputs"].get("CAEC", "Sometimes"),
        "SMOKE": smoke if submit_btn else st.session_state.risk_result["inputs"].get("SMOKE", "no"),
        "CH2O": ch2o if submit_btn else st.session_state.risk_result["inputs"].get("CH2O", 2.0),
        "SCC": scc if submit_btn else st.session_state.risk_result["inputs"].get("SCC", "no"),
        "FAF": faf if submit_btn else st.session_state.risk_result["inputs"].get("FAF", 1.0),
        "TUE": tue if submit_btn else st.session_state.risk_result["inputs"].get("TUE", 1.0),
        "CALC": calc
        if submit_btn
        else st.session_state.risk_result["inputs"].get("CALC", "Sometimes"),
        "MTRANS": mtrans
        if submit_btn
        else st.session_state.risk_result["inputs"].get("MTRANS", "Public_Transportation"),
    }

    if submit_btn:
        with st.spinner("Executing calibrated LightGBM risk pipeline and SHAP tree explainer..."):
            res = predict_obesity_risk(user_habits, include_explanations=True)
            res["inputs"] = user_habits
            st.session_state.risk_result = res
    else:
        res = st.session_state.risk_result

    pred_tier = res["risk_tier"]
    probs = res["probabilities"]
    top_risks = res["top_risk_drivers"]
    top_prot = res["top_protective_factors"]

    st.markdown("---")
    st.subheader("Screening Outcome & Risk Probability Profile")

    # Header tier badge
    tier_colors = {
        "Healthy": "#10b981",
        "Underweight": "#3b82f6",
        "Overweight": "#f59e0b",
        "Obese": "#ef4444",
    }
    tier_color = tier_colors.get(pred_tier, "#64748b")

    st.markdown(
        f"""
        <div style="background-color: {tier_color}15; border-left: 6px solid {tier_color}; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
            <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: {tier_color};">Predicted Behavioral Lifestyle Tier</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a; margin: 4px 0;">{pred_tier}</div>
            <div style="font-size: 0.88rem; color: #334155;">Calibrated probability of lifestyle habits placing client in the <strong>{pred_tier}</strong> category: <strong>{probs.get(pred_tier, 0) * 100:.1f}%</strong>.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Plotly Probabilities Horizontal Bar Chart
    r1, r2 = st.columns([1.1, 1.0])

    with r1:
        st.markdown("#### Calibrated Probability Distribution")
        tiers = ["Underweight", "Healthy", "Overweight", "Obese"]
        prob_vals = [probs.get(t, 0.0) * 100 for t in tiers]
        bar_colors = ["#93c5fd", "#86efac", "#fde047", "#fca5a5"]

        fig_prob = go.Figure(
            go.Bar(
                x=prob_vals,
                y=tiers,
                orientation="h",
                text=[f"{v:.1f}%" for v in prob_vals],
                textposition="auto",
                marker={"color": bar_colors, "line": {"color": "#64748b", "width": 1}},
            )
        )
        fig_prob.update_layout(
            xaxis={"title": "Calibrated Confidence (%)", "range": [0, 100]},
            yaxis={"autorange": "reversed"},
            height=280,
            margin={"l": 10, "r": 20, "t": 10, "b": 30},
        )
        st.plotly_chart(fig_prob, use_container_width=True)

    with r2:
        st.markdown("#### Key Factor Breakdown (SHAP Explanations)")

        st.markdown("**Top Modifiable Risk Drivers (Pushing toward higher tier):**")
        if top_risks and top_risks[0] != "None dominant":
            for r in top_risks:
                st.warning(f"🔺 **{r}**")
        else:
            st.info("No dominant elevated risk drivers detected in this lifestyle profile.")

        st.markdown("**Top Protective Lifestyle Factors (Protecting healthy tier):**")
        if top_prot and top_prot[0] != "None dominant":
            for p in top_prot:
                st.success(f"🛡️ **{p}**")
        else:
            st.info("No dominant protective lifestyle factors detected.")

    st.divider()

    # Scientific Rigor Notice (Synthetic Holdout Gap)
    with st.expander("🔬 Model Card Transparency: Synthetic vs Human Generalization Gap"):
        st.markdown(
            """
            ### Dataset Evaluation Notice (Honest Engineering Standard)
            The obesity dataset contains **both real survey responses and SMOTE-synthesized interpolations**.
            In our cross-validation and evaluation pipeline:
            - **Synthetic Test Accuracy:** **93.13%** (Macro-F1: 0.7041, Brier: 0.1123)
            - **Likely-Original Real Human Holdout Accuracy:** **61.79%** (Macro-F1: 0.4731, Brier: 0.5307)

            **Why does this gap exist?**
            SMOTE generates dense, clean synthetic clusters between points that overestimate real-world generalization.
            When evaluated on true un-interpolated human survey respondents, real-world behavioral variability
            proves substantially harder to classify from 14 lifestyle questions without physical weight.

            We explicitly disclose this gap to provide clinical transparency rather than inflated synthetic metrics.
            """
        )
