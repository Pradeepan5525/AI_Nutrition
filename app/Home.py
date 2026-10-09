"""AI-Powered Nutrition Intelligence System - Streamlit Main Entry Point."""

from __future__ import annotations

import streamlit as st

from app.ui_components import (
    init_session_state,
    inject_custom_css,
    render_auth_sidebar,
    render_hero,
    render_medical_disclaimer,
)
from nutri.foods.food_db import get_food_db

# Configure page settings
st.set_page_config(
    page_title="AI Nutrition Intelligence System",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject styling and initialize state
inject_custom_css()
init_session_state()
render_auth_sidebar()

# Top safety disclaimer
render_medical_disclaimer()

# Hero Section
render_hero(
    title="🥗 AI-Powered Nutrition Intelligence System",
    subtitle=(
        "Next-generation clinical nutrition intelligence combining metabolic modeling, "
        "calibrated machine learning risk screening, evidence-based guideline rules, and "
        "mixed-integer linear programming meal optimization."
    ),
)

# Telemetry KPIs
db = get_food_db()
total_foods = db.get_total_count()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Verified Food Catalog</div>
            <div class="kpi-val">{total_foods:,}</div>
            <div class="kpi-sub">USDA + Foundation Harmonized</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        """
        <div class="kpi-card">
            <div class="kpi-label">Risk ML Architecture</div>
            <div class="kpi-val">Calibrated LightGBM</div>
            <div class="kpi-sub">4 Tiers • SHAP Explainability</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        """
        <div class="kpi-card">
            <div class="kpi-label">Optimization Engine</div>
            <div class="kpi-val">PuLP MILP (CBC)</div>
            <div class="kpi-sub">Exact ±5% Calorie Bounds</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        """
        <div class="kpi-card">
            <div class="kpi-label">Safety Gate Standard</div>
            <div class="kpi-val">Tri-State Strict</div>
            <div class="kpi-sub">Minors • Seniors • Pregnancy Gated</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br/>", unsafe_allow_html=True)

# Pre-loaded Demo Profiles
st.subheader("⚡ Quick Start: Explore Pre-Loaded Personas")
st.write(
    "Select a pre-configured clinical profile to instantly populate assessment data across all pages:"
)

personas = {
    "Alex (Healthy Active Professional)": {
        "age": 28,
        "sex": "female",
        "height_cm": 168.0,
        "weight_kg": 62.0,
        "activity_level": "moderate",
        "goal": "maintenance",
        "is_asian": False,
        "condition_flags": [],
        "allergies": [],
        "dietary_restrictions": [],
    },
    "Marcus (Hypertension & Sodium Sensitivity)": {
        "age": 52,
        "sex": "male",
        "height_cm": 178.0,
        "weight_kg": 88.0,
        "activity_level": "sedentary",
        "goal": "weight_loss",
        "is_asian": False,
        "condition_flags": ["hypertension"],
        "allergies": ["peanuts"],
        "dietary_restrictions": ["low_sodium"],
    },
    "Priya (Asian Cutoffs & Type 2 Diabetes Management)": {
        "age": 44,
        "sex": "female",
        "height_cm": 158.0,
        "weight_kg": 66.0,
        "activity_level": "light",
        "goal": "weight_loss",
        "is_asian": True,
        "condition_flags": ["diabetes"],
        "allergies": ["dairy"],
        "dietary_restrictions": ["vegetarian"],
    },
    "Elena (Plant-Based Athlete with Celiac / Gluten Allergy)": {
        "age": 25,
        "sex": "female",
        "height_cm": 172.0,
        "weight_kg": 64.0,
        "activity_level": "active",
        "goal": "muscle_gain",
        "is_asian": False,
        "condition_flags": [],
        "allergies": ["gluten"],
        "dietary_restrictions": ["vegan"],
    },
}

p_cols = st.columns(4)
for i, (name, profile) in enumerate(personas.items()):
    with p_cols[i]:
        st.markdown(f"**{name.split('(')[0].strip()}**")
        st.caption(f"_{name.split('(')[1].replace(')', '')}_")
        if st.button("Load Persona", key=f"btn_persona_{i}"):
            st.session_state.user_profile = profile
            st.session_state.assessment_result = None
            st.session_state.meal_plan_result = None
            st.success(
                f"Loaded {name.split('(')[0].strip()}! Head to **1_My_Health** in the sidebar."
            )

st.divider()

# System Modules Walkthrough
st.subheader("🧭 Guided Clinical Intelligence Workflow")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown("#### 1. Anthropometric Assessment")
    st.write(
        "Mifflin-St Jeor BMR, WHO/Asian BMI categorizations, maintenance TDEE, "
        "and macronutrient distributions with protective caloric floors."
    )
    st.page_link("pages/1_My_Health.py", label="Open My Health →", icon="🩺")

with m2:
    st.markdown("#### 2. Lifestyle Risk Screening")
    st.write(
        "Screen behavioral habits for obesity predisposition without body dimensions bias. "
        "Generates SHAP plain-English driver waterfall explanations."
    )
    st.page_link("pages/2_Risk_Check.py", label="Open Risk Check →", icon="📊")

with m3:
    st.markdown("#### 3. Optimized Diet Planning")
    st.write(
        "PuLP mixed-integer linear programming synthesizes single-day or 7-day meal plans "
        "meeting exact calorie (±5%), sodium, and sugar targets with grocery aggregation."
    )
    st.page_link("pages/3_My_Diet_Plan.py", label="Open Diet Plan →", icon="📋")

with m4:
    st.markdown("#### 4. Food Catalog Explorer")
    st.write(
        "Search 32,000+ foods with tri-state allergen exclusions, inspect Health Score v2 (0-100), "
        "and explore strictly healthier same-category replacements."
    )
    st.page_link("pages/4_Food_Explorer.py", label="Open Food Explorer →", icon="🔍")

st.markdown("<br/>", unsafe_allow_html=True)
st.caption(
    "AI Nutrition Intelligence System v1.0.0 • Developed with scikit-learn, LightGBM, SHAP, PuLP, FastAPI, and Streamlit."
)
