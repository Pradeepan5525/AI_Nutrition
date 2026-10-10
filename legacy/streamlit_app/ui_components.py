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
    """Ensure session state default profile and auth parameters exist across page transitions."""
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None

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


def render_auth_sidebar() -> None:
    """Render the user authentication module in the Streamlit sidebar."""
    from nutri.auth.security import create_access_token
    from nutri.auth.user_db import get_user_db

    db = get_user_db()

    st.sidebar.markdown("### 🔐 User Portal")

    # 1. Logged in state
    if st.session_state.auth_user:
        user = st.session_state.auth_user
        role = user.get("role", "patient")
        role_label = "🩺 Clinician / Dietitian" if role == "clinician" else "👤 Patient"

        st.sidebar.markdown(
            f"""
            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:12px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <strong style="color:#0f172a; font-size:0.95rem;">{user.get("full_name") or user.get("username")}</strong>
                </div>
                <div style="font-size:0.75rem; color:#64748b; margin-bottom:8px;">@{user.get("username")} • {user.get("email")}</div>
                <div style="display:inline-block; font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:12px; {"background:#ccfbf1; color:#0f766e;" if role == "clinician" else "background:#dbeafe; color:#1d4ed8;"}">
                    {role_label}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_save, c_out = st.sidebar.columns([1.2, 1])
        with c_save:
            if st.button(
                "💾 Sync Profile",
                key="btn_sync_profile",
                help="Save current health stats to your account",
            ):
                updated = db.update_user_profile(user["id"], st.session_state.user_profile)
                if updated:
                    st.session_state.auth_user = updated
                    st.sidebar.success("Profile saved!")
        with c_out:
            if st.button("🚪 Log Out", key="btn_logout"):
                st.session_state.auth_user = None
                st.session_state.auth_token = None
                st.rerun()

        st.sidebar.divider()
        return

    # 2. Not logged in state
    with st.sidebar.expander("🔑 Login / Account Access", expanded=True):
        tab_login, tab_demo, tab_reg = st.tabs(["Sign In", "Demo", "Register"])

        with tab_login:
            login_id = st.text_input("Username or Email", key="auth_login_user")
            login_pwd = st.text_input("Password", type="password", key="auth_login_pwd")
            if st.button("Sign In", key="btn_auth_signin", use_container_width=True):
                if not login_id or not login_pwd:
                    st.error("Please enter your username and password.")
                else:
                    auth_res = db.authenticate_user(login_id, login_pwd)
                    if auth_res:
                        token = create_access_token(
                            {
                                "sub": auth_res["username"],
                                "user_id": auth_res["id"],
                                "role": auth_res["role"],
                            }
                        )
                        st.session_state.auth_user = auth_res
                        st.session_state.auth_token = token
                        # If user has a saved profile, load it
                        if auth_res.get("saved_profile"):
                            st.session_state.user_profile.update(auth_res["saved_profile"])
                        st.success(
                            f"Welcome back, {auth_res.get('full_name') or auth_res['username']}!"
                        )
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

        with tab_demo:
            st.caption("1-Click Instant Login for Evaluation:")
            if st.button("👤 Demo Patient", key="btn_demo_patient", use_container_width=True):
                demo = db.get_user_by_username("demo_user")
                if demo:
                    st.session_state.auth_user = demo
                    st.session_state.auth_token = create_access_token(
                        {"sub": demo["username"], "user_id": demo["id"], "role": demo["role"]}
                    )
                    if demo.get("saved_profile"):
                        st.session_state.user_profile.update(demo["saved_profile"])
                    st.success("Signed in as Demo Patient!")
                    st.rerun()

            if st.button("🩺 Demo Clinician", key="btn_demo_clinician", use_container_width=True):
                demo = db.get_user_by_username("clinician_demo")
                if demo:
                    st.session_state.auth_user = demo
                    st.session_state.auth_token = create_access_token(
                        {"sub": demo["username"], "user_id": demo["id"], "role": demo["role"]}
                    )
                    st.success("Signed in as Demo Clinician!")
                    st.rerun()

        with tab_reg:
            reg_user = st.text_input("Username", key="auth_reg_user")
            reg_email = st.text_input("Email", key="auth_reg_email")
            reg_name = st.text_input("Full Name", key="auth_reg_name")
            reg_pwd = st.text_input("New Password", type="password", key="auth_reg_pwd")
            reg_role = st.selectbox("Role", ["patient", "clinician"], key="auth_reg_role")

            if st.button("Create Account", key="btn_auth_register", use_container_width=True):
                if not reg_user or not reg_email or not reg_pwd:
                    st.error("Username, email, and password are required.")
                elif len(reg_pwd) < 6:
                    st.error("Password must be at least 6 characters.")
                elif db.get_user_by_username(reg_user):
                    st.error(f"Username '{reg_user}' is already taken.")
                elif db.get_user_by_email(reg_email):
                    st.error(f"Email '{reg_email}' is already registered.")
                else:
                    new_u = db.create_user(
                        username=reg_user,
                        email=reg_email,
                        password=reg_pwd,
                        full_name=reg_name,
                        role=reg_role,
                        initial_profile=st.session_state.user_profile,
                    )
                    st.session_state.auth_user = new_u
                    st.session_state.auth_token = create_access_token(
                        {"sub": new_u["username"], "user_id": new_u["id"], "role": new_u["role"]}
                    )
                    st.success("Account created successfully! Welcome aboard.")
                    st.rerun()

    st.sidebar.divider()
