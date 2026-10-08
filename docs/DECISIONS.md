# Architecture and Clinical Decisions Log (DECISIONS.md)

This log documents all key architectural, algorithmic, and clinical engineering decisions made in the AI-Powered Nutrition Intelligence System, adhering to safety, explainability, and reproducible evidence.

---

## Decision 1: Separation of Synthetic vs Real Data in Obesity Dataset
- **Context:** The `ObesityDataSet_raw_and_data_sinthetic.csv` (2,111 rows) contains ~77% SMOTE-generated synthetic rows. Ordinal survey variables (FCVC, NCP, CH2O, FAF, TUE) contain fractional values that never appear in real survey responses.
- **Decision:** Split the dataset such that all rows with whole numbers across Age and all 5 ordinal features are isolated into a `likely_original` held-out test split (~498 rows). The remaining data is used for cross-validated model tuning and a synthetic test split.
- **Rationale:** Prevents optimistic synthetic-leakage bias. Provides honest evaluation of model generalization to real humans.

## Decision 2: Elimination of Target Leakage in Diet Recommendations Dataset
- **Context:** `diet_recommendations_dataset.csv` has a deterministic mapping where `Disease_Type == Diabetes` always maps to `Low_Carb`, `Hypertension` maps to `Low_Sodium`, and `Obesity`/None maps to `Balanced`.
- **Decision:** Do NOT train a predictive ML model on `Diet_Recommendation`. Document the 100% leakage via cross-tabulation and cross-validation in `notebooks/02_eda_diet_leakage.ipynb`. Use the dataset purely for realistic vocabulary, clinical parameter distributions, and demo profiles.
- **Rationale:** Presenting a 100% accuracy model on a synthetic rule artifact is scientifically invalid and misleading.

## Decision 3: Exclude Anthropometric Features (Height, Weight, BMI) from Obesity Risk Prediction
- **Context:** The target `NObeyesdad` is directly derived from BMI cutoffs (`Weight / (Height^2)`). If Height and Weight are included, any classifier trivially reverses the arithmetic formula.
- **Decision:** The Obesity Risk ML model uses strictly lifestyle, behavioral, and demographic features (Gender, Age, family history, FAVC, FCVC, NCP, CAEC, SMOKE, CH2O, SCC, FAF, TUE, CALC, MTRANS).
- **Rationale:** The clinical purpose of the risk model is lifestyle screening: "Given your daily habits, what is your weight-status vulnerability?", not recalculating BMI.

## Decision 4: Transparent Health Score v2 (0–100) Formulation
- **Context:** The raw USDA/OpenFoodFacts `health_score` is opaque, inconsistently rounded, and missing in many rows.
- **Decision:** Implement an evidence-based, transparent score `health_score_v2` that rewards nutrient density (protein, dietary fiber, vitamins/minerals per kcal) and penalizes excessive free sugars, saturated fats, and sodium per 100g. Blend with Nutri-Score where available.
- **Rationale:** Total transparency and determinism ensure the scoring can be inspected, explained, and defended clinically.

## Decision 5: Tri-State Allergen Classification with Fail-Safe Conservatism
- **Context:** Food allergy reactions can be severe and life-threatening. Missing data in allergen columns does not mean the food is allergen-free.
- **Decision:** Every allergen is classified into one of three states: `present`, `absent`, or `unknown`. Any food missing verified allergen disclosures or ingredient specifications is marked as `unknown`. Hard filtering treats `unknown` as excluded whenever strict allergen protection is activated.
- **Rationale:** Patient safety is non-negotiable. "Unknown" must never be equated to "safe".

## Decision 6: Linear Programming with PuLP for Meal Optimization
- **Context:** Rule-based heuristics cannot reliably balance multidimensional macro and micronutrient constraints simultaneously while maintaining dietary diversity and realistic portions.
- **Decision:** Formulate meal planning as a Mixed-Integer / Linear Programming problem using PuLP with CBC solver. Optimize objective function (maximizing health score and meal fit while penalizing repeated ingredients) subject to daily calorie (±5%), macronutrient ranges, and condition thresholds.
- **Rationale:** LP guarantees mathematical optimality and determinism, or provides explicit proof of infeasibility that triggers transparent constraint relaxation.

## Decision 7: Multi-Condition Conflict Resolution Hierarchy
- **Context:** Users with co-morbidities (e.g., Hypertension + Diabetes + Obesity) may receive conflicting nutritional guidelines.
- **Decision:** Apply the **strictest bound** across all applicable clinical guidelines. For example, sodium is capped at 1500 mg (Hypertension/AHA) rather than 2300 mg (General/DGA). Every resulting constraint records the originating clinical guideline and citation in its explanation metadata.
- **Rationale:** Safety first, with total auditable transparency to the user.
