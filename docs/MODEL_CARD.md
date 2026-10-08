# Model Card: Lifestyle-Based Obesity Risk Screening Model

**Model Name:** Calibrated LightGBM Obesity Risk Classifier  
**Model Version:** `0.1.0`  
**Artifact Path:** `artifacts/models/obesity_risk_pipeline.joblib`  
**Release Date:** October 2026  
**License:** MIT  

---

## 1. Intended Use and Scope

- **Intended Use:** Educational lifestyle screening tool estimating an adult's weight-status risk tier (`Underweight`, `Healthy`, `Overweight`, `Obese`) based purely on demographic and behavioral survey indicators.
- **Strict Clinical Boundary:** This model is **NOT a diagnostic medical device** and does not substitute for clinical measurement or physician consultation.
- **Target Audience:** Adults (18–75 years) seeking lifestyle awareness and personalized health coaching.
- **Out-of-Scope Uses:** Minors (<18), pregnant or lactating individuals, acute medical diagnosis, insurance underwriting, or surgical triaging.

---

## 2. Training Data and Target Formulation

- **Data Source:** `ObesityDataSet_raw_and_data_sinthetic.csv` (2,111 rows, 17 columns) collected across Mexico, Peru, and Colombia.
- **Deduplication:** 24 exact duplicate records were detected and purged, leaving 2,087 unique rows.
- **Input Features (14 Lifestyle & Demographic Factors):**
  - **Demographics:** `Age`, `Gender`, `family_history_with_overweight`
  - **Dietary Habits:** `FAVC` (high-calorie food frequency), `FCVC` (vegetable consumption frequency), `NCP` (number of main meals), `CAEC` (snacking between meals), `CH2O` (daily water intake)
  - **Physical & Sedentary Habits:** `FAF` (exercise frequency), `TUE` (daily screen time), `MTRANS` (primary transit mode)
  - **Health Habits:** `SMOKE`, `SCC` (calorie monitoring), `CALC` (alcohol consumption)
- **Strict Leakage Prevention:** `Height`, `Weight`, and `BMI` are **strictly excluded** from features, preventing trivial arithmetic leakage of the target definition.
- **Target Mapping (4 Clinical Tiers):**
  - `Underweight`: Derived from `Insufficient_Weight`
  - `Healthy`: Derived from `Normal_Weight`
  - `Overweight`: Derived from `Overweight_Level_I` and `Overweight_Level_II`
  - `Obese`: Derived from `Obesity_Type_I`, `Obesity_Type_II`, and `Obesity_Type_III`

---

## 3. Synthetic Data Limitation and Splitting Strategy

- **Empirical Reality:** The original dataset is ~76% synthetic (oversampled using SMOTE). Crucially, **100% of 'Healthy' (Normal_Weight) individuals in the raw dataset reside in the original human subset**; SMOTE was applied solely to augment minority classes (`Obese`, `Overweight`, `Underweight`).
- **Splitting Architecture:**
  1. Real human records (`likely_original`, 491 rows with integer survey answers) were split:
     - 50% (245 rows) reserved as a **Strict Held-Out Realism Benchmark** (never trained on).
     - 50% (246 rows) allocated to the training pool to ensure representation of the `Healthy` class.
  2. Synthetic records (1,596 rows) were split:
     - 80% (1,276 rows) allocated to the training pool.
     - 20% (320 rows) reserved as the **Synthetic Test Split**.
  3. Combined training set: 1,521 samples.

---

## 4. Benchmark Performance (Measured Empirical Results)

### Cross-Validation Comparison (Stratified 5-Fold on Training Set)

| Candidate Model | Mean CV Accuracy | CV Accuracy Std | Mean CV Macro-F1 | CV Macro-F1 Std |
| :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression (Baseline)** | 67.13% | ± 1.59% | 0.5692 | ± 0.0240 |
| **Random Forest** | 83.04% | ± 2.16% | 0.7672 | ± 0.0294 |
| **LightGBM (Selected Base)** | **86.72%** | **± 2.54%** | **0.8247** | **± 0.0338** |

### Final Calibrated LightGBM Evaluation: Synthetic vs Real Gap

| Metric | Synthetic Test Split (N=320) | Likely Original Holdout (N=246) | Performance Gap Analysis |
| :--- | :--- | :--- | :--- |
| **Overall Accuracy** | **93.13%** | **61.79%** | **-31.34% drop** on real humans |
| **Macro-F1 Score** | **0.7041** | **0.4731** | **-0.2310 drop** on real humans |
| **Multiclass Brier Score** | **0.1123** | **0.5307** | Calibration degrades on real data |
| **Underweight Recall** | 97.8% | 41.2% | Real humans exhibit nuanced habits |
| **Healthy Recall** | N/A (0 synthetic) | 82.3% | Strong identification of healthy lifestyles |
| **Overweight Recall** | 86.8% | 43.9% | Overlaps between pre-obesity and healthy |
| **Obese Recall** | 95.1% | 12.9% | Synthetic SMOTE over-separates extreme obesity |

> **Honest Scientific Takeaway:** Evaluated solely on synthetic data, the model appears to achieve 93.1% accuracy. However, when benchmarked against genuine human responses, accuracy is 61.8%. This gap exists because SMOTE creates synthetic points along smooth linear manifolds that do not capture the behavioral heterogeneity of real people.

---

## 5. Demographic Fairness and Subgroup Audit

Evaluated on the strict held-out human realism benchmark (N=246):

### By Gender
- **Male Subgroup (N=131):** Accuracy = **59.54%**, Macro-F1 = **0.4636**
- **Female Subgroup (N=115):** Accuracy = **64.35%**, Macro-F1 = **0.4928**
- **Disparity:** +4.8% accuracy in females, primarily driven by stronger predictive signal in meal structure (`NCP`) and snacking patterns (`CAEC`).

### By Age Group
- **Age < 25 (N=182):** Accuracy = **67.03%**, Macro-F1 = **0.4712**
- **Age 25–40 (N=56):** Accuracy = **46.43%**, Macro-F1 = **0.3170**
- **Age > 40 (N=8):** Accuracy = **50.00%**, Macro-F1 = **0.3889**
- **Limitation:** The dataset skews heavily toward university-aged young adults (<25). Generalization to middle-aged and older adults is limited and requires clinical caution.

---

## 6. Explainability Methodology (SHAP)

- Global and local feature importances are computed using `shap.TreeExplainer` on the fitted tree ensemble.
- For each prediction, the top 3 risk drivers and top 3 protective factors are translated into accessible, non-technical plain English explanations to empower user behavior change.

---

## 7. Model Governance and Safety Warnings

- **Screening Only:** Never display risk outputs without the mandatory medical disclaimer.
- **Fail-Safe Fallbacks:** Input features outside biological bounds are rejected with validation errors.
