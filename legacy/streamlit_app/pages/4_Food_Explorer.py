"""Page 4: Harmonized Food Catalog Explorer, Health Score Breakdown & Nutrition Radars."""

from __future__ import annotations

import json

import plotly.graph_objects as go
import streamlit as st

from app.ui_components import (
    init_session_state,
    inject_custom_css,
    render_auth_sidebar,
    render_hero,
    render_medical_disclaimer,
)
from nutri.foods.food_db import get_food_db
from nutri.foods.scoring import explain_health_score
from nutri.foods.swaps import find_healthier_swaps

st.set_page_config(
    page_title="Food Catalog Explorer - Nutrition Intelligence", page_icon="🔍", layout="wide"
)

inject_custom_css()
init_session_state()
render_auth_sidebar()
render_medical_disclaimer()

render_hero(
    title="🔍 Harmonized Food Catalog & Health Score Explorer",
    subtitle=(
        "Search and analyze 32,800+ foods with tri-state allergen auditing, "
        "transparent Health Score v2 (0–100) breakdowns, and healthier swap recommendations."
    ),
)

db = get_food_db()

# Sidebar Filters
st.sidebar.header("🔍 Catalog Filters")
query = st.sidebar.text_input(
    "Food Name Keyword", value="", placeholder="e.g. Oats, Salmon, Apple, Chips"
)

categories = ["All"] + db.get_unique_categories()
selected_cat = st.sidebar.selectbox("Food Category", options=categories)

food_types = ["All"] + db.get_unique_food_types()
selected_type = st.sidebar.selectbox("Meal Slot Type", options=food_types)

min_score = st.sidebar.slider(
    "Minimum Health Score v2 (0-100)", min_value=0.0, max_value=90.0, value=0.0, step=5.0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Safety Exclusions")

ALLERGEN_LIST = ["peanuts", "gluten", "dairy", "soy", "eggs", "fish", "nuts"]
excluded_allergens = st.sidebar.multiselect("Exclude Allergens", options=ALLERGEN_LIST)
strict_allergens = st.sidebar.checkbox(
    "Strict Tri-State Mode",
    value=True,
    help="When enabled, foods with 'unknown' allergen status are strictly excluded.",
)

DIET_TAGS = ["vegetarian", "vegan", "gluten_free", "dairy_free", "nut_free"]
selected_diet_tags = st.sidebar.multiselect("Dietary Restrictions", options=DIET_TAGS)

# Query Database
with st.spinner("Querying harmonized foods database..."):
    results = db.search_foods(
        query=query,
        category=selected_cat if selected_cat != "All" else None,
        food_type=selected_type if selected_type != "All" else None,
        min_health_score=min_score,
        exclude_allergens=excluded_allergens,
        dietary_tags=selected_diet_tags,
        strict_allergens=strict_allergens,
        limit=50,
    )
    total_matches = db.count_matching_foods(
        query=query,
        category=selected_cat if selected_cat != "All" else None,
        food_type=selected_type if selected_type != "All" else None,
        min_health_score=min_score,
        exclude_allergens=excluded_allergens,
        dietary_tags=selected_diet_tags,
        strict_allergens=strict_allergens,
    )

st.write(f"Showing **{len(results)}** of **{total_matches:,}** matching items:")

if not results:
    st.info("No foods matched your query and safety filter combination.")
else:
    # Summary Table
    table_rows = []
    for r in results:
        table_rows.append(
            {
                "Food ID": r["food_id"],
                "Name": r["name"],
                "Category": r.get("category", "Other"),
                "Health Score": round(float(r["health_score_v2"]), 1),
                "Nutri-Score": (r.get("nutriscore") or "N/A").upper(),
                "Energy (kcal)": round(float(r["kcal_100g"]), 1),
                "Protein (g)": round(float(r["protein_100g"]), 1),
                "Carbs (g)": round(float(r["carbs_100g"]), 1),
                "Fat (g)": round(float(r["fat_100g"]), 1),
                "Fiber (g)": round(float(r["fiber_100g"]), 1),
                "Sugar (g)": round(float(r["sugar_100g"]), 1),
                "Sodium (mg)": round(float(r["sodium_mg_100g"]), 0),
            }
        )

    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.divider()

    # Deep Dive Inspector Section
    st.subheader("🔬 Food Item Deep-Dive & Health Score Breakdown")
    food_names = [f"{r['name']} ({r['food_id']})" for r in results]
    selected_option = st.selectbox("Select food item to inspect in detail:", options=food_names)
    selected_id = selected_option.split("(")[-1].replace(")", "").strip()
    selected_food = next(r for r in results if r["food_id"] == selected_id)

    col_meta, col_radar = st.columns([1.1, 1.0])

    with col_meta:
        st.markdown(f"### {selected_food['name']}")
        st.caption(
            f"Source: {selected_food.get('source', 'usda').upper()} | Category: {selected_food.get('category')} | Slot Type: {selected_food.get('food_type')}"
        )

        score_val = float(selected_food["health_score_v2"])
        score_color = (
            "#166534" if score_val >= 65 else ("#b45309" if score_val >= 45 else "#991b1b")
        )
        st.markdown(
            f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 18px; margin: 12px 0;">
                <span style="font-size: 0.82rem; font-weight: 700; text-transform: uppercase; color: #64748b;">Health Score v2</span><br/>
                <span style="font-size: 2.2rem; font-weight: 800; color: {score_color};">{score_val:.1f} / 100</span>
                <span style="font-size: 0.9rem; color: #64748b; margin-left: 12px;">(Nutri-Score Grade: <strong>{(selected_food.get("nutriscore") or "Unknown").upper()}</strong>)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Health score formula breakdown
        explanation = explain_health_score(selected_food)
        st.markdown("**Health Score Drivers:**")
        for drv in explanation.get("drivers", []):
            st.markdown(f"- {drv}")

        # Allergen status audit
        st.markdown("**Allergen Verification (Tri-State Audit):**")
        raw_flags = selected_food.get("allergen_flags")
        if isinstance(raw_flags, str):
            try:
                flags_dict = json.loads(raw_flags)
            except Exception:
                flags_dict = {}
        else:
            flags_dict = raw_flags or {}

        tag_spans = []
        for alg, stat in flags_dict.items():
            if stat == "present":
                tag_spans.append(f"<span class='badge-danger'>{alg}: PRESENT</span>")
            elif stat == "absent":
                tag_spans.append(f"<span class='badge-safe'>{alg}: ABSENT</span>")
            else:
                tag_spans.append(f"<span class='badge-warn'>{alg}: UNKNOWN</span>")
        st.markdown(" ".join(tag_spans), unsafe_allow_html=True)

    with col_radar:
        st.markdown("#### Nutritional Profile (per 100g)")

        # Radar comparison against typical benchmarks
        nutrients = [
            "Protein (g)",
            "Fiber (g)",
            "Carbs (g)",
            "Dietary Fat (g)",
            "Sugar (g)",
            "Sodium (mg/10)",
        ]
        values = [
            float(selected_food["protein_100g"]),
            float(selected_food["fiber_100g"]),
            float(selected_food["carbs_100g"]),
            float(selected_food["fat_100g"]),
            float(selected_food["sugar_100g"]),
            float(selected_food["sodium_mg_100g"]) / 10.0,
        ]

        radar_fig = go.Figure(
            data=go.Scatterpolar(
                r=values + [values[0]],
                theta=nutrients + [nutrients[0]],
                fill="toself",
                fillcolor="rgba(13, 148, 136, 0.25)",
                line={"color": "#0d9488", "width": 2},
                name=selected_food["name"][:20],
            )
        )
        radar_fig.update_layout(
            polar={"radialaxis": {"visible": True, "range": [0, max(max(values) * 1.1, 10)]}},
            showlegend=False,
            height=320,
            margin={"l": 30, "r": 30, "t": 20, "b": 20},
        )
        st.plotly_chart(radar_fig, use_container_width=True)

    st.markdown("---")

    # Healthier Alternatives Section
    st.subheader(f"💡 Strictly Healthier Replacements for '{selected_food['name']}'")
    st.write(
        "Our swap algorithm queries the catalog for items in the exact same category or slot type "
        "with strictly higher Health Score v2 and lower calories, sodium, or sugar:"
    )

    swaps = find_healthier_swaps(selected_food, top_n=4)
    if not swaps:
        st.info(
            "No higher-scoring same-category alternatives found. This food is already at or near the top of its nutritional tier."
        )
    else:
        swap_cols = st.columns(len(swaps))
        for i, s in enumerate(swaps):
            with swap_cols[i]:
                st.markdown(
                    f"""
                    <div style="border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; background: white; height: 100%;">
                        <div style="font-weight: 700; font-size: 0.92rem; margin-bottom: 4px;">{s["name"][:35]}</div>
                        <div style="color: #166534; font-weight: 700; font-size: 1.1rem;">Score: {s["health_score_v2"]:.1f} (+{s["score_improvement"]:.1f})</div>
                        <div style="font-size: 0.78rem; color: #475569; margin: 6px 0;">
                            Δ kcal: <strong>{s["kcal_diff"]:+.0f}</strong><br/>
                            Δ Sodium: <strong>{s["sodium_diff_mg"]:+.0f} mg</strong><br/>
                            Δ Sugar: <strong>{s["sugar_diff_g"]:+.1f} g</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
