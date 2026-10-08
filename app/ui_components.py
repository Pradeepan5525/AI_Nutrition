"""Shared UI design system, styling, and reusable components for Streamlit application."""

from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    """Inject modern, clean CSS styling across all pages."""
    css = """
    <style>
        /* Modern font & body styling */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Top disclaimer header banner */
        .disclaimer-banner {
            background: linear-gradient(90deg, #fef2f2 0%, #fff1f2 100%);
            border: 1px solid #fecaca;
            border-left: 4px solid #ef4444;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 0.82rem;
            color: #991b1b;
            margin-bottom: 20px;
            line-height: 1.4;
        }

        /* Hero / Header Card */
        .hero-box {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f766e 100%);
            color: white;
            padding: 24px 28px;
            border-radius: 14px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.15);
        }
        .hero-title {
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 6px;
            color: #ffffff;
        }
        .hero-subtitle {
            font-size: 0.95rem;
            color: #cbd5e1;
            line-height: 1.5;
        }

        /* KPI / Metric Card */
        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        .kpi-card:hover {
            border-color: #cbd5e1;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .kpi-label {
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 4px;
        }
        .kpi-val {
            font-size: 1.6rem;
            font-weight: 700;
            color: #0f172a;
        }
        .kpi-sub {
            font-size: 0.78rem;
            color: #059669;
            margin-top: 4px;
        }

        /* Badges */
        .badge-safe {
            background-color: #dcfce7;
            color: #166534;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-warn {
            background-color: #fef3c7;
            color: #92400e;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-danger {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }

        /* Slot Meal Container */
        .meal-slot-header {
            background-color: #f8fafc;
            border-left: 4px solid #0d9488;
            padding: 8px 12px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 1.05rem;
            color: #0f172a;
            margin-top: 14px;
            margin-bottom: 8px;
        }

        /* Sidebar enhancement */
        .css-1d391kg {
            background-color: #f8fafc;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_medical_disclaimer() -> None:
    """Display persistent clinical and educational safety banner."""
    st.markdown(
        """
        <div class="disclaimer-banner">
            <strong>⚠️ Clinical & Educational Disclaimer:</strong> This system is an AI research application
            for nutritional education and dietary planning. It is <strong>not medical advice</strong>, does not diagnose
            disease, and cannot replace consultation with a physician or registered dietitian.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str) -> None:
    """Render a modern visual hero header banner."""
    st.markdown(
        f"""
        <div class="hero-box">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    """Ensure session state default profile parameters exist across page transitions."""
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {
            "age": 28,
            "sex": "female",
            "height_cm": 165.0,
            "weight_kg": 60.0,
            "activity_level": "moderate",
            "goal": "maintenance",
            "is_asian": False,
            "condition_flags": [],
            "allergies": [],
            "dietary_restrictions": [],
        }
    if "assessment_result" not in st.session_state:
        st.session_state.assessment_result = None
    if "risk_result" not in st.session_state:
        st.session_state.risk_result = None
    if "meal_plan_result" not in st.session_state:
        st.session_state.meal_plan_result = None
