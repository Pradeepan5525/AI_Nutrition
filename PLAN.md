# Project Plan: AI-Powered Nutrition Intelligence System

This plan outlines the architecture, implementation phases, verification steps, and delivery criteria for the AI-Powered Nutrition Intelligence System for Health Assessment and Personalized Diet Recommendations.

---

## Phase Checklist

### Phase 0: Setup and Environment Initialization
- [x] Create repository directory tree (`data/{raw,interim,processed,external}`, `notebooks/`, `src/nutri/...`, `api/`, `app/`, `tests/`, `scripts/`, `docs/`, `reports/`)
- [x] Copy and verify raw dataset files into `data/raw/`
- [x] Configure `pyproject.toml`, dependencies, and linting/formatting tools (`ruff`, `pytest`, `mypy`)
- [x] Initialize `docs/DECISIONS.md` for architectural and clinical design rationale
- [x] Create base `Makefile` for developer workflow

### Phase 1: Data Engineering & Exploratory Data Analysis (EDA)
- [x] Build data loaders with schema validation (`src/nutri/data/loaders.py`)
- [x] Implement raw data cleaning and normalization pipeline (`src/nutri/data/cleaners.py`, `harmonizer.py`)
  - [x] Standardize all food nutrients to per-100g basis (handling units, ml to g beverage equivalence)
  - [x] Deduplicate food items prioritizing Foundation > SR Legacy > Branded datasets
  - [x] Impute secondary micronutrients using category medians with `*_imputed` tracking flags
  - [x] Physical plausibility validation: calories (0-900 kcal/100g), macro sum (<= 105g/100g), sugar <= carbs, sat fat <= fat
  - [x] Fix healthy foods database unit errors (sodium mg vs g) and log violations to `reports/data_quality_log.csv`
  - [x] Regional food extensibility: implement schema loader for `data/external/` with regional food example
- [x] Build tri-state allergen detection engine (`src/nutri/data/allergens.py`) with ingredient keyword matching (`present`, `absent`, `unknown`)
- [x] Export unified dataset to `data/processed/foods.parquet` and SQLite database (`data/processed/foods.db`) with indexes
- [x] Generate comprehensive data quality report (`reports/data_quality.md`)
- [x] Create 4 EDA notebooks / scripts with verifiable findings:
  - [x] `01_eda_obesity`: Synthetics analysis, ordinal fractional patterns, and `likely_original` subset identification
  - [x] `02_eda_diet_leakage`: Proof of 100% target leakage between `Disease_Type` and `Diet_Recommendation`
  - [x] `03_eda_foods`: Nutritional distribution, missingness, and cluster analysis
  - [x] `04_model_eval`: Model baseline benchmarks and calibration
- [x] Write unit and contract tests (`tests/test_data_pipeline.py`, `tests/test_allergens.py`) and verify pass

### Phase 2: Deterministic Health Assessment Engine
- [x] Implement BMI calculator (`src/nutri/assess/bmi.py`) with standard WHO and Asian-population thresholds
- [x] Implement BMR (Mifflin-St Jeor) and TDEE calculator (`src/nutri/assess/energy.py`) with activity multipliers
- [x] Build Goal & Caloric Target engine (`src/nutri/assess/targets.py`) with safe rate-of-loss limits, calorie floors (1200 kcal F / 1500 kcal M)
- [x] Implement macro and micronutrient distribution engine (protein, fat, carb balance, fiber, sodium, added sugar limits)
- [x] Implement Clinical Safety Gate (`src/nutri/rules/safety.py`) guarding against minors (<18), seniors (>75), pregnancy, eating disorders, and extreme BMIs (<16 or >45)
- [x] Write exhaustive unit tests (`tests/test_assess.py`) comparing against hand-computed clinical cases

### Phase 3: Obesity-Risk Machine Learning Model
- [x] Extract lifestyle and demographic features while strictly excluding Height, Weight, and BMI (`src/nutri/features/obesity_features.py`)
- [x] Create both 4-tier clinical risk target (Underweight, Healthy, Overweight, Obese) and 7-class baseline target
- [x] Train, tune, and compare models via 5-fold Stratified CV: Logistic Regression, Random Forest, LightGBM, and Calibrated LightGBM (`src/nutri/models/train_risk.py`)
- [x] Track experiments locally with MLflow (`mlruns/`)
- [x] Evaluate performance on both synthetic test split and `likely_original` holdout split; compute accuracy, macro-F1, recall, Brier score, calibration
- [x] Explainability module: SHAP feature importance and patient-friendly top 3 risk factors (`src/nutri/models/explain.py`)
- [x] Demographic fairness audit across gender and age groups
- [x] Persist pipeline artifacts (`artifacts/models/obesity_risk_pipeline.joblib`) with schema validation wrapper (`src/nutri/models/predict.py`)
- [x] Document model provenance and limitations in `docs/MODEL_CARD.md`
- [x] Write unit tests (`tests/test_risk_model.py`) verifying inference, probabilities summing to 1.0, and metric floors

### Phase 4: Condition-Aware Rule Engine
- [x] Create evidence-based clinical rules in configuration (`src/nutri/rules/clinical_rules.yaml` & `conditions.py`)
- [x] Implement condition rules with authoritative citations:
  - [x] Hypertension (DASH guidelines: sodium <= 1500-2300 mg, potassium/fiber boost, processed meat limits)
  - [x] Type 2 Diabetes / Dysglycemia (added sugar limits, low glycemic carb proxies, fiber targets)
  - [x] Hypercholesterolemia (saturated fat < 10% kcal, cholesterol limits, soluble fiber emphasis)
  - [x] Overweight / Obesity (deficit floors, protein/fiber satiety targets)
  - [x] Dietary restrictions (Low Sodium, Low Sugar, Vegetarian, Vegan, Gluten-Free, Dairy-Free, Nut-Free)
- [x] Implement multi-condition conflict resolution engine with strictness hierarchy and transparent audit trail ("why this limit")
- [x] Write `docs/CLINICAL_RULES.md` with complete rationale, formula references, and citations
- [x] Write comprehensive unit tests (`tests/test_clinical_rules.py`) covering multi-condition conflicts

### Phase 5: Food Scoring & Smart Recommendation Engine
- [x] Formulate and implement transparent `health_score_v2` (0-100) balancing nutrient density, fiber, protein vs. sat fat, sodium, free sugar (`src/nutri/foods/scoring.py`)
- [x] Validate health score: test fruits/vegetables outrank ultra-processed snacks
- [x] Implement hard safety filtering pipeline (strict exclusion of confirmed and unverified allergens, dietary restrictions)
- [x] Implement content-based ranking engine taking into account nutrient target fit and diversity (`src/nutri/foods/search.py`)
- [x] Implement "Healthier Swap" algorithm (`src/nutri/foods/swaps.py`) identifying same-category items with superior nutritional profile
- [x] Write tests (`tests/test_food_scoring.py`, `tests/test_swaps.py`) verifying allergen safety guarantees and swap improvements

### Phase 6: Meal-Plan Optimizer (PuLP Linear Programming)
- [x] Build meal-slot templates by food category (breakfast, lunch, dinner, snack) (`src/nutri/plan/meal_templates.py`)
- [x] Implement PuLP linear programming model for daily meal generation (`src/nutri/plan/optimizer.py`)
  - [x] Hard bounds: calories (+/- 5%), protein/fat/carbs, sodium, saturated fat, sugar limits
  - [x] Diversity penalties and repetition limits
  - [x] Realistic portion size bounds (min/max grams per food category)
- [x] Implement 7-day plan generator with inter-day variety constraints
- [x] Implement automated constraint relaxation with clear user diagnostics upon infeasibility
- [x] Build grocery list aggregator (`src/nutri/plan/grocery.py`)
- [x] Write comprehensive tests (`tests/test_optimizer.py`) verifying calorie tolerances and constraint satisfaction

### Phase 7: REST API (FastAPI)
- [x] Create Pydantic v2 schemas (`api/schemas.py`) for all request/response payloads
- [x] Build endpoints (`api/routers/`):
  - [x] `POST /assess`: Health & energy calculations with safety gate
  - [x] `POST /risk`: Obesity lifestyle risk screening and SHAP explanation
  - [x] `POST /plan`: Single-day and 7-day meal optimization
  - [x] `GET /foods/search`: Paginated food query with allergen/restriction filters
  - [x] `GET /foods/{id}/swaps`: Healthier replacement suggestions
  - [x] `POST /report`: Downloadable PDF report generation
  - [x] `GET /health` and `GET /version`: Operational telemetry
- [x] Add CORS middleware, rate limiting (`slowapi`), and structured logging
- [x] Write integration test suite (`tests/test_api.py`) using `TestClient`

### Phase 8: Interactive Multi-Page Streamlit Application
- [x] Design high-aesthetic, responsive theme with modern typography, custom CSS tokens, and clean layout
- [x] Implement application pages (`app/`):
  - [x] `Home.py`: System overview, methodology, clinical safety disclaimer
  - [x] `1_My_Health.py`: Interactive BMI gauge, TDEE calculator, goal setter, safety warnings
  - [x] `2_Risk_Check.py`: Lifestyle questionnaire, risk probability gauge, SHAP driver waterfall
  - [x] `3_My_Diet_Plan.py`: Condition picker, 1-day/7-day meal schedule, swap buttons, grocery list
  - [x] `4_Food_Explorer.py`: Food search, nutrition radar comparisons, health score breakdown
  - [x] `5_About.py`: Data cards, model card, ethical disclaimers, bias analysis
- [x] Integrate PDF export generator and pre-loaded demo profiles
- [x] Verify complete UI interactivity with zero dead buttons or unhandled errors

### Phase 9: Production Polish, Optimization & Telemetry
- [x] Add caching for high-frequency SQLite food queries
- [x] Verify meal plan optimizer solves within < 3 seconds
- [x] Build data and prediction drift monitoring script (`scripts/check_drift.py`)
- [x] Document local MLflow server execution instructions in README

### Phase 10: Quality Assurance, Documentation & Packaging
- [x] Run full test suite with coverage report (`pytest --cov=src/nutri --cov-report=term-missing`) ensuring >= 80% coverage
- [x] Create `Dockerfile` and `docker-compose.yml` for unified API + UI orchestration
- [x] Write `docs/DATA_CARD.md`, `docs/MODEL_CARD.md`, `docs/CLINICAL_RULES.md`, `docs/DECISIONS.md`
- [x] Write comprehensive academic/engineering report `REPORT.md` with measured empirical results
- [x] Write comprehensive `README.md` with architecture diagram, quickstart, and screenshots
- [x] End-to-end verification of `make setup`, `make data`, `make train`, `make test`, and containerized run
