"""Page 5: System Architecture, Data Cards, Model Card & Clinical Disclaimers."""

from __future__ import annotations

import streamlit as st

from app.ui_components import (
    init_session_state,
    inject_custom_css,
    render_hero,
    render_medical_disclaimer,
)

st.set_page_config(
    page_title="About & System Architecture - Nutrition Intelligence", page_icon="ℹ️", layout="wide"
)

inject_custom_css()
init_session_state()
render_medical_disclaimer()

render_hero(
    title="ℹ️ System Architecture, Data Cards & Clinical Governance",
    subtitle=(
        "Full technical specification, model transparency card, clinical guideline references, "
        "and data provenance documentation."
    ),
)

t1, t2, t3, t4 = st.tabs(
    ["🏗️ Architecture & Pipeline", "📦 Data Cards", "🧠 Model Card", "⚖️ Clinical Governance"]
)

with t1:
    st.subheader("Unified System Architecture")
    st.markdown(
        """
        The **AI-Powered Nutrition Intelligence System** is structured as an end-to-end, reproducible,
        clinical decision support framework:

        ```mermaid
        flowchart TD
            A[Raw Data Sources: USDA, Obesity Survey, Diet Recommendations] --> B[Data Pipelines & Schema Validation: Pydantic v2]
            B --> C[Harmonized Foods Parquet & SQLite Database: 32,847 Items]

            U[User / Patient Profile] --> D[Metabolic Assessment Engine: Mifflin-St Jeor & WHO BMI]
            U --> E[Lifestyle Risk Screener: Calibrated LightGBM - Height/Weight/BMI Excluded]
            U --> F[Clinical Guidelines & Conflict Resolution: AHA, ADA, DGA]

            D --> G[PuLP Mixed-Integer Linear Programming Solver]
            F --> G
            C --> G

            G --> H[Calorie-Exact Daily / 7-Day Meal Schedules: +/-5% kcal]
            G --> I[Department Grocery Aggregator]

            H --> J[Healthier Swap Recommendation Engine]
            H --> K[ReportLab 2-Page Clinical PDF Generator]
            E --> K
            D --> K
        ```
        """
    )
    st.markdown(
        """
        ### Technology Stack & Engineering Standards
        - **Data Pipeline:** pandas, pyarrow, SQLite3, Pydantic v2, YAML.
        - **Machine Learning:** scikit-learn, LightGBM, SHAP, joblib.
        - **Optimization:** PuLP Mixed-Integer Linear Programming (CBC Solver).
        - **REST API:** FastAPI, SlowAPI rate limiting, Uvicorn, Pydantic v2 schemas.
        - **User Interface:** Streamlit multi-page architecture, Plotly interactive graphics.
        - **PDF Reporting:** ReportLab publication engine.
        - **Testing & Quality:** pytest (68+ tests), pytest-cov, ruff formatting.
        """
    )

with t2:
    st.subheader("Data Cards & Provenance")

    st.markdown("#### 1. Estimation of Obesity Levels Based On Eating Habits (UCI)")
    st.write(
        "- **Citation:** Palechor & de la Hoz Manotas (2019), UCI Machine Learning Repository.\n"
        "- **Observations:** 2,111 total instances across 17 attributes.\n"
        "- **Critical Finding:** Only ~498 instances correspond to original human survey responses; the remaining ~1,613 were generated via SMOTE. 100% of 'Normal_Weight' individuals exist solely in the original human subset.\n"
        "- **Split Strategy:** Strict 50% split of human data into holdout to benchmark true human generalization."
    )

    st.markdown("#### 2. Diet Recommendation System Dataset")
    st.write(
        "- **Observations:** 6,561 records linking demographic attributes, disease status, and diet advice.\n"
        "- **Label Leakage Discovery:** `Diet_Recommendation` is 100% deterministically governed by `Disease_Type` (e.g. all 1,120 Diabetes rows receive 'Low Carb Diet'; all 1,072 Hypertension rows receive 'DASH Diet').\n"
        "- **Engineering Decision:** ML model training on this target was explicitly avoided. The deterministic mappings were formalized into transparent, evidence-based clinical rules."
    )

    st.markdown("#### 3. Harmonized Food Catalog")
    st.write(
        "- **Sources:** USDA Foundation Foods, SR Legacy, Healthy Foods dataset.\n"
        "- **Catalog Size:** 32,847 deduplicated, physically plausible food items.\n"
        "- **Deduplication:** Dropped 9,270 duplicate items using hierarchical precedence: Foundation > SR Legacy > Branded.\n"
        "- **Safety Standardization:** Verified tri-state allergen auditing across 7 critical allergens."
    )

with t3:
    st.subheader("Model Card: Calibrated Lifestyle Obesity Risk Classifier")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(
            """
            - **Model Type:** Calibrated LightGBM (Gradient Boosting)
            - **Target:** 4 Clinical Tiers (`Underweight`, `Healthy`, `Overweight`, `Obese`)
            - **Feature Count:** 14 demographic and modifiable lifestyle features
            - **Permitted Features:** Age, Gender, Family History, FAVC, FCVC, NCP, CAEC, SMOKE, CH2O, SCC, FAF, TUE, CALC, MTRANS.
            - **Explicitly Excluded Features:** **Height, Weight, BMI** (strictly omitted to evaluate behavioral predisposition rather than body dimensions).
            """
        )
    with col_m2:
        st.markdown(
            """
            - **5-Fold Cross Validation:** Macro-F1 = **0.8247** (outperformed Random Forest 0.7672 and Logistic Regression 0.5692)
            - **Synthetic Test Set:** Accuracy = **93.13%**, Macro-F1 = **0.7041**, Brier Score = **0.1123**
            - **Likely-Original Real Holdout:** Accuracy = **61.79%**, Macro-F1 = **0.4731**, Brier Score = **0.5307**
            - **Interpretability:** TreeExplainer SHAP computing per-instance contribution values.
            """
        )

with t4:
    st.subheader("Clinical Governance & Safety Standard")

    st.markdown(
        """
        ### 1. Safety Gate Contraindications
        Automated dietary planning and caloric restriction are immediately withheld upon detecting:
        - **Minors (< 18 years):** Pediatric nutritional needs require clinical dietitian oversight.
        - **Elderly (> 75 years):** Sarcopenia risk requires geriatric medical supervision.
        - **Pregnancy & Lactation:** Elevated micronutrient needs; deficits strictly withheld.
        - **Eating Disorder History:** Weight tracking and calorie restrictions blocked.
        - **Extreme BMI (< 16.0 or > 45.0):** Immediate clinical referral advised.

        ### 2. Tri-State Allergen Verification Standard
        Standard binary classification (safe vs unsafe) fails in medical contexts because unverified foods
        pose life-threatening anaphylactic risks. We enforce a **tri-state allergen framework**:
        - `present`: Food confirmed to contain allergen -> **BLOCKED**
        - `absent`: Food verified allergen-free in source database -> **PERMITTED**
        - `unknown`: Ingredient list ambiguous or unverified -> **TREATED AS UNSAFE** under strict mode.

        ### 3. Clinical Guidelines Citations
        - **Hypertension:** American Heart Association (AHA) DASH Diet standard: Sodium ≤ 1,500 mg/day.
        - **Type 2 Diabetes:** American Diabetes Association (ADA 2024) Standards of Care: Added Sugar ≤ 5% of energy, Fiber ≥ 18 g/1,000 kcal.
        - **High Cholesterol:** AHA/ACC Dyslipidemia Guidelines: Saturated Fat ≤ 7% of energy, Dietary Cholesterol ≤ 200 mg/day.
        - **Caloric Safety Floors:** Minimum 1,200 kcal/day for females and 1,500 kcal/day for males (American College of Sports Medicine).
        """
    )
