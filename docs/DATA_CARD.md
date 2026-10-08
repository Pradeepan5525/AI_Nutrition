# Data Cards: AI Nutrition Intelligence System

This document provides rigorous, standardized Data Cards for all three datasets consumed and processed by the system.

---

## 1. Estimation of Obesity Levels Based On Eating Habits and Physical Condition

### Overview & Provenance
- **Source:** [UCI Machine Learning Repository: Estimation of Obesity Levels](https://archive.icsuci.edu/dataset/544/estimation+of+obesity+levels+based+on+eating+habits+and+physical+condition)
- **Primary Authors:** Fabio Mendoza Palechor and Alexis de la Hoz Manotas (2019)
- **Total Records:** 2,111 rows, 17 attributes
- **Format:** CSV (`data/raw/ObesityDataSet_raw_and_data_sinthetic.csv`)

### Composition & Critical Synthetic Artifact Discovery
- **Real vs Synthetic Instances:**
  - Real human survey respondents: **~498 instances (23.6%)**.
  - Synthetically generated via SMOTE: **~1,613 instances (76.4%)**.
- **Human Identification Heuristic:**
  True human respondents possess integer values for Age and ordinal survey responses (`FCVC`, `NCP`, `CH2O`, `FAF`, `TUE`), whereas SMOTE interpolation yields floating-point fractions (e.g. `Age = 24.321`, `FCVC = 2.187`).
- **Class Skew in Real Data:**
  **100% of the `Normal_Weight` (Healthy) instances reside exclusively in the original human responses.** The SMOTE procedure was only applied to minority classes, leaving `Normal_Weight` un-interpolated.
- **Evaluation Implication:**
  Evaluating models on a standard random train/test split leaks SMOTE cluster density into the test set, creating an inflated accuracy metric (**93.13%**). When strictly benchmarked against held-out real human respondents, true generalization drops to **61.79%**.

### Feature Schema & Permitted Inputs
| Feature Name | Type | Permitted in Risk Model | Clinical Description |
| :--- | :--- | :---: | :--- |
| `Gender` | Categorical | Yes | Biological sex (`Female`, `Male`) |
| `Age` | Numeric | Yes | Age in years [10, 100] |
| `family_history_with_overweight` | Binary | Yes | First-degree family history (`yes`, `no`) |
| `FAVC` | Binary | Yes | Frequent consumption of high-calorie foods |
| `FCVC` | Continuous | Yes | Frequency of vegetable consumption (1.0 to 3.0) |
| `NCP` | Continuous | Yes | Number of main meals (1.0 to 4.0) |
| `CAEC` | Categorical | Yes | Snacking consumption between meals |
| `SMOKE` | Binary | Yes | Smoking habit (`yes`, `no`) |
| `CH2O` | Continuous | Yes | Daily water consumption (1.0 to 3.0) |
| `SCC` | Binary | Yes | Caloric intake monitoring (`yes`, `no`) |
| `FAF` | Continuous | Yes | Physical activity frequency (0.0 to 3.0) |
| `TUE` | Continuous | Yes | Screen/device time frequency (0.0 to 2.0) |
| `CALC` | Categorical | Yes | Alcohol consumption frequency |
| `MTRANS` | Categorical | Yes | Transportation mode (determines incidental activity) |
| **`Height`** | Numeric | **NO** | **STRICTLY EXCLUDED** (Body dimension) |
| **`Weight`** | Numeric | **NO** | **STRICTLY EXCLUDED** (Body dimension) |
| **`BMI`** | Numeric | **NO** | **STRICTLY EXCLUDED** (Direct target proxy) |

### Target Variable Harmonization
The raw target `NObeyesdad` contains 7 classes. These are mapped to 4 clinical decision tiers:
- `Insufficient_Weight` $\rightarrow$ **Underweight**
- `Normal_Weight` $\rightarrow$ **Healthy**
- `Overweight_Level_I`, `Overweight_Level_II` $\rightarrow$ **Overweight**
- `Obesity_Type_I`, `Obesity_Type_II`, `Obesity_Type_III` $\rightarrow$ **Obese**

---

## 2. Diet Recommendation System Dataset

### Overview & Provenance
- **Source:** Kaggle Diet Recommendation System Dataset
- **Total Records:** 1,000 raw patient records
- **Format:** CSV (`data/raw/diet_recommendations_dataset.csv`)

### Empirical Discovery: 100% Deterministic Label Leakage
During exploratory data analysis (`notebooks/02_eda_diet_leakage.ipynb`), mutual information and cross-tabulation revealed complete deterministic dependency between `Disease_Type` and `Diet_Recommendation`:
- Every patient with `Disease_Type == "Diabetes"` receives `Diet_Recommendation == "Low_Carb"`.
- Every patient with `Disease_Type == "Hypertension"` receives `Diet_Recommendation == "Low_Sodium"`.
- Every patient with `Disease_Type == "None"` receives `Diet_Recommendation == "Balanced"`.

```
Cross-Tabulation Matrix:
Disease_Type     Balanced    Low_Carb    Low_Sodium
---------------------------------------------------
Diabetes                0         237             0
Hypertension            0           0           254
None                  509           0             0
```
- **Engineering Decision (ADR-004):**
  Training a machine learning model on this target was explicitly rejected as deceptive engineering. Instead, the deterministic rule was codified into our clinical rules engine (`src/nutri/rules/conditions.py`) with explicit medical guideline citations (AHA DASH, ADA Standards of Care).

---

## 3. Harmonized Food Catalog

### Overview & Data Integration
- **Raw Catalogs Ingested:**
  1. USDA Comprehensive Foods (`comprehensive_foods_usda.csv`): 38,719 rows
  2. Healthy Foods Database (`healthy_foods_database.csv`): 3,400 rows
- **Processed Catalog Size:** **32,847 deduplicated items** (`data/processed/foods.parquet`, `data/processed/foods.db`)

### Cleaning, Deduplication & Quality Transformations
1. **Deduplication Priority Hierarchy:**
   Foods with identical normalized names were resolved using source hierarchy:
   $$\text{USDA Foundation} > \text{USDA SR Legacy} > \text{USDA Branded} > \text{Healthy Foods}$$
   A total of **9,270 duplicate food items** were dropped.
2. **Sodium Unit Correction:**
   In the raw Healthy Foods dataset, sodium values were inconsistently reported in grams instead of milligrams (e.g. `sodium = 0.45` representing 0.45 g = 450 mg). Values with `< 10` for high-calorie processed items were scaled $\times 1,000$ to standardize on milligrams.
3. **Physical Plausibility Bounds:**
   Every food was validated against thermodynamic physical constraints per 100g:
   - Energy: $0.0 \le \text{kcal} \le 900.0$
   - Macronutrient sum: $\text{protein} + \text{carbs} + \text{fat} \le 105.0\text{ g}$
4. **Category-Median Imputation with Tracking Flags:**
   Missing secondary nutrients (saturated fat, dietary fiber, sodium, cholesterol, calcium, iron, vitamin C) were imputed using category medians. Every imputed value is paired with an explicit boolean flag column (`sat_fat_imputed`, `fiber_imputed`, `sodium_mg_imputed`) to guarantee clinical data transparency.

### Tri-State Allergen Framework
Standard binary allergen flags (safe vs unsafe) create fatal risks when unverified foods are assumed safe. Every food item is mapped to 7 allergen columns (`allergen_peanuts`, `allergen_gluten`, `allergen_dairy`, `allergen_soy`, `allergen_eggs`, `allergen_fish`, `allergen_nuts`) with tri-state values:
- `present`: Ingredient keyword verified present -> **Blocked**.
- `absent`: Verified single-ingredient foundation food -> **Permitted**.
- `unknown`: Ambiguous or unlisted ingredient composition -> **Treated as Unsafe under strict mode**.
