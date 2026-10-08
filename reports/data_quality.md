# Comprehensive Data Quality and Harmonization Report

**Generated:** Automated Pipeline Run  
**Target File:** `E:\AI_Nutrition\data\processed\foods.parquet` & `E:\AI_Nutrition\data\processed\foods.db`  
**Final Cleaned Food Count:** **32,847 records**

---

## 1. Raw Dataset Overview and Row Counts

| Dataset | Raw Records | Processed Retained | Retained % | Primary Source / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **USDA FoodData Central** | 40,000 | 28,305 | 70.8% | Foundation, SR Legacy, Branded foods (deduplicated by priority) |
| **Healthy Foods Database** | 9,028 | 22 | 0.2% | Curated whole foods with sodium unit corrections |
| **Open Food Facts** | 4,997 | 4,510 | 90.3% | Commercial products with Nutri-Score & allergen testing |
| **External Regional Foods** | Sample included | 10 | 100.0% | User-extensible regional cuisine table (`data/external/`) |
| **Total Harmonized** | **54,025** | **32,847** | **60.8%** | Unified schema per-100g |

---

## 2. Data Cleaning Actions & Drop Summary

1. **USDA Deduplication:**
   - 9,100+ raw entries had duplicated normalized names.
   - Preserved highest-quality record per name using hierarchy: `Foundation (3) > SR Legacy (2) > Branded (1)`.
   - Records with complete secondary nutrients were retained.

2. **Healthy Foods Unit Errors Corrected:**
   - Detected and corrected unit discrepancies in `sodium_mg` (e.g. `Almond butter, creamy` reported as 0.996g = 996mg).
   - Removed extreme unphysical outliers (e.g., sodium > 50,000 mg/100g).

3. **Core Macronutrient Integrity:**
   - Zero blind macro imputation: rows missing `calories`, `protein`, `fat`, or `carbs` were dropped.
   - Secondary nutrients (`sat_fat`, `sugar`, `fiber`, `sodium`, `cholesterol`, `calcium`, `iron`, `vitamin_c`) were imputed strictly using category medians, tracked by `*_imputed` boolean flags.

4. **Physical Plausibility Bounds:**
   - Strict enforcement: Calories in [0, 900] kcal/100g.
   - Macro summation constraint: `protein + fat + carbs <= 105g/100g`.
   - Sub-component bounds: `sugar <= carbs + 1.0g`, `sat_fat <= fat + 0.5g`.
   - Non-negativity check on all nutritional columns.
   - All dropped violations logged to `data_quality_log.csv`.

---

## 3. Allergen Safety Status Distribution

The system strictly enforces a tri-state status (`present`, `absent`, `unknown`) across all 7 supported allergens. "Unknown" is never treated as safe.

| Allergen | Present Count | Absent Count | Unknown / Unverified Count |
| :--- | :--- | :--- | :--- |
| **Gluten** | 8,068 | 24,654 | 125 |
| **Dairy** | 10,223 | 22,500 | 124 |
| **Tree Nuts** | 2,958 | 29,765 | 124 |
| **Peanuts** | 815 | 31,832 | 200 |
| **Soy** | 7,175 | 25,546 | 126 |
| **Eggs** | 2,966 | 29,765 | 116 |
| **Fish** | 1,020 | 31,702 | 125 |

---

## 4. Health Score v2 Summary Statistics

- **Mean Health Score:** 46.9 / 100
- **Median Health Score:** 47.9 / 100
- **25th - 75th Percentile:** 37.4 - 55.8
- **Top Scoring Categories:** Vegetables (48.4), Fruits (42.4)
- **Lowest Scoring Categories:** Snacks & Sweets (37.4)
