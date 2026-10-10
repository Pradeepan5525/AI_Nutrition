# Corrections and Modernization Plan: AI Nutrition Intelligence System

This document outlines the architectural and design corrections executed to transition the project to a **Login-First Architecture** with a unified **Single-Theme Design System** (one green accent on neutral gray/white), replacing the legacy Streamlit UI with a modern React + Vite + TypeScript frontend.

---

## 1. Current State Inventory

### 1.1 Backend & Core AI/ML Engine (`src/nutri/`)
- **`src/nutri/assess/`**: Mifflin-St Jeor BMR, WHO/Asian BMI categories, TDEE, macronutrient distributions, safety gating (minors, pregnancy, extremes).
- **`src/nutri/models/`**: Calibrated LightGBM 4-tier obesity lifestyle risk classifier with TreeSHAP explanations.
- **`src/nutri/rules/`**: Clinical guideline rules engine (Hypertension, Type 2 Diabetes, Dyslipidemia, Obesity) with strict conflict resolution.
- **`src/nutri/foods/`**: SQLite-backed food database (`foods.db`), Health Score v2 (0–100), tri-state allergen safety, and healthier same-category swaps.
- **`src/nutri/plan/`**: Mixed-Integer Linear Programming (PuLP) for single and 7-day meal optimization and grocery aggregation.
- **`src/nutri/reports/`**: ReportLab publication-grade PDF generator.
- **`src/nutri/auth/`**: Argon2 & PBKDF2 password hashing, JWT access token issuing, httpOnly SameSite cookie refresh token rotation, brute-force lockout, and user service.

### 1.2 Enhanced API (`api/`)
- FastAPI app with authenticated routers:
  - `/auth`: Register, login, refresh, logout, me, legacy OAuth2 token endpoints.
  - `/users`: Profile updates, password changes, GDPR data export, account deletion, assessment history, risk results, meal plans, weight logs, goals/alerts, and notifications.
  - `/assess`, `/risk`, `/plan`, `/foods/*`, and `/report`: All protected via `Depends(get_current_user)`.
- CORS configured for Vite frontend (`http://localhost:5173`, `http://127.0.0.1:5173`).

### 1.3 Modern Frontend (`web/`)
- React 18 + Vite + TypeScript + Tailwind CSS + React Router + TanStack Query + Lucide + Recharts.
- Design System: Strict 12-token system defined in `web/src/styles/tokens.css` with zero external hex codes.
- Legacy Streamlit app cleanly archived to `legacy/streamlit_app/`.

---

## 2. Completed Checklist

### Phase 1: Repository Hygiene & Legacy Archive
- [x] Create `legacy/streamlit_app/` and move `app/` contents into it.
- [x] Remove Streamlit from active run paths, Dockerfile, and runtime configs.

### Phase 2: Database, User Storage & Authentication Enhancement
- [x] Define SQLAlchemy database models (`users`, `profiles`, `assessments`, `risk_results`, `meal_plans`, `weight_logs`, `goals_alerts`, `notifications`, `refresh_tokens`) supporting SQLite & Postgres.
- [x] Set up Alembic migration environment and generate baseline migration (`ab9bc25a71ef_initial_schema.py`).
- [x] Implement enhanced authentication in `src/nutri/auth/`:
  - [x] Password hashing with Argon2 (with backwards-compatible PBKDF2 verification).
  - [x] Brute-force lockout (5 failed attempts triggers 15-minute lockout).
  - [x] JWT access token (15-30 min) in memory + httpOnly, SameSite refresh token cookie (7-30 days) with token rotation on use.
- [x] Implement required endpoints:
  - [x] `POST /auth/register` (email validation, password rules, disclaimer requirement)
  - [x] `POST /auth/login` (generic 401 error, lockout tracking, refresh cookie)
  - [x] `POST /auth/refresh` (cookie-based refresh token rotation)
  - [x] `POST /auth/logout` (revokes refresh token and clears cookie)
  - [x] `GET /auth/me` (returns current user profile and role)
  - [x] `PUT /users/me/profile` (persists clinical/dietary preferences)
  - [x] `GET /users/me/export` (GDPR data portability JSON export)
  - [x] `DELETE /users/me` (cascading removal of all user rows)
  - [x] Per-user history CRUD for assessments, risk screenings, meal plans, weight logs, and alerts.
- [x] Enforce `get_current_user` dependency across `/assess`, `/risk`, `/plan`, `/foods/*`, and `/report`.
- [x] Provide `.env.example` and production security startup checks.
- [x] Create `scripts/create_demo_user.py` reading credentials strictly from environment variables.

### Phase 3: Frontend Web Application (`web/`)
- [x] Scaffold React + Vite + TypeScript + Tailwind CSS application in `web/`.
- [x] Implement Design System in `web/src/styles/tokens.css` and `tailwind.config.js` with exact 12-token constraint:
  - `--bg`: `#F6F8FA`
  - `--surface`: `#FFFFFF`
  - `--border`: `#E5E9EE`
  - `--text`: `#0F172A`
  - `--muted`: `#64748B`
  - `--primary`: `#047857`
  - `--primary-hover`: `#065F46`
  - `--primary-soft`: `#ECFDF5`
  - `--primary-accent`: `#10B981`
  - `--hero-from`: `#064E3B`
  - `--hero-to`: `#0B1F1A`
  - `--warning`: `#B45309` / `--warning-soft`: `#FEF3C7`
  - `--danger`: `#B91C1C` / `--danger-soft`: `#FEE2E2`
- [x] Create `scripts/check_colors.py` asserting zero unapproved hex values in `web/src/` (PASS).
- [x] Build Auth Context & Protected Routing:
  - [x] Full-page skeleton on auth loading (never flash protected content).
  - [x] Unauthenticated visitors redirected to `/login`.
  - [x] First-time user redirected to `/onboarding`.
  - [x] Token refresh handling with 401 interceptor showing session-expired toast.
- [x] Build Application Pages & Components:
  - [x] **Auth**: Split-panel Login & Register with password toggle, strength meter, disclaimer.
  - [x] **Onboarding**: 3-step wizard (Basics, Lifestyle/Goal, Clinical/Allergens) with prefill storage.
  - [x] **AppShell**: Sticky navbar with active green pill, notifications bell, user avatar menu, 1200px container, and operational footer.
  - [x] **Dashboard**: "Welcome back", Today's Targets dark gradient card, Active Alerts card, 6 Intelligence Module cards, quick stats.
  - [x] **Health Check**: Form with presets + Dark BMI gauge card, BMR/TDEE cards, macro bars, save to history.
  - [x] **Risk Predictor**: Lifestyle habits form + Dark "Highest likelihood" card, Top 3 progress bars, SHAP factors (amber/green).
  - [x] **Diet Planner**: Today / 7-Day / Grocery tabs, meal cards with Swap modal, rule explanation panel, PDF download.
  - [x] **Food Explorer**: Filter card, results table, slide-over detail drawer with tri-state allergens, 3-way food comparison.
  - [x] **Condition Advisor**: Guideline limits, food guidance, evidence & citations card, common precautions.
  - [x] **Progress & Alerts**: Weight log with green Recharts line chart, goal setting, active/triggered alerts, notifications.
  - [x] **History**: Filterable table of past assessments, risk screenings, and meal plans with deletion.
  - [x] **Profile**: Account settings, password update, Export Data, Delete Account confirm modal.
  - [x] **404 & Error Boundary**.

### Phase 4: Containerization & Tooling
- [x] Update `docker-compose.yml` to run `api` (port 8000) and `web` (port 5173 / nginx build).
- [x] Create `web/Dockerfile` with multi-stage build and `web/nginx.conf` with SPA routing and API reverse proxy.
- [x] Update root `Dockerfile` to expose port 8000.
- [x] Update `Makefile` with targets: `setup`, `api`, `web`, `dev`, `docker`, `test`, `e2e`, `check-colors`.

### Phase 5: Verification, Testing & Documentation
- [x] Run `scripts/check_colors.py`: 100% compliant (PASS).
- [x] Run backend test suite: 86 passed, 0 failed, 81% coverage on `src/nutri/` (PASS).
- [x] Run Playwright E2E suite (`scripts/run_e2e_tests.py`): 20 passed, 0 failed (PASS).
- [x] Capture responsive screenshots at 1440px and 390px in `reports/ui_screenshots/` (22 screenshots generated, no horizontal scroll).
- [x] Record decisions in `docs/DECISIONS.md` and update `README.md`.
