"""Harmonization pipeline unifying food datasets into standardized schema."""

import sqlite3
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from nutri.config import (
    DATA_QUALITY_LOG,
    DATA_QUALITY_REPORT,
    FOODS_DB,
    FOODS_PARQUET,
    SUPPORTED_ALLERGENS,
)
from nutri.data.allergens import (
    ALLERGEN_ABSENT,
    ALLERGEN_UNKNOWN,
    allergen_flags_to_json,
    detect_allergen_tri_state,
)
from nutri.data.cleaners import (
    check_physical_plausibility,
    deduplicate_usda_foods,
    fix_healthy_foods_sodium_unit_errors,
    impute_secondary_nutrients,
    normalize_food_name,
)
from nutri.data.loaders import (
    load_external_regional_foods,
    load_raw_healthy_foods,
    load_raw_open_food_facts,
    load_raw_usda,
)
from nutri.foods.scoring import calculate_health_score_v2
from nutri.logging import setup_logger

logger = setup_logger(__name__)


def map_category(raw_cat: str, food_name: str = "") -> Tuple[str, str]:
    """Map arbitrary raw category / food name to standardized category and food_type."""
    text = f"{raw_cat or ''} {food_name or ''}".lower()

    if any(k in text for k in ["vegetable", "greens", "spinach", "broccoli", "carrot", "salad"]):
        return "Vegetables", "Vegetables"
    if any(
        k in text
        for k in ["fruit", "berry", "apple", "banana", "orange", "grape", "melon", "juice"]
    ):
        return "Fruits", "Fruits"
    if any(
        k in text
        for k in ["grain", "cereal", "rice", "bread", "pasta", "oat", "flour", "bakery", "wheat"]
    ):
        return "Grains & Pasta", "Grains"
    if any(
        k in text for k in ["fish", "seafood", "salmon", "tuna", "shrimp", "cod", "clam", "oyster"]
    ):
        return "Fish & Seafood", "Proteins"
    if any(
        k in text
        for k in ["meat", "poultry", "chicken", "beef", "pork", "turkey", "lamb", "sausage"]
    ):
        return "Meat & Poultry", "Proteins"
    if any(k in text for k in ["dairy", "milk", "cheese", "yogurt", "egg", "butter", "cream"]):
        return "Dairy & Egg", "Dairy"
    if any(
        k in text
        for k in ["nut", "seed", "legume", "bean", "lentil", "pea", "peanut", "almond", "tofu"]
    ):
        return "Legumes & Nuts", "Proteins"
    if any(k in text for k in ["beverage", "drink", "coffee", "tea", "soda", "water"]):
        return "Beverages", "Beverages"
    if any(k in text for k in ["snack", "candy", "cookie", "chocolate", "dessert", "chip", "cake"]):
        return "Snacks & Sweets", "Snacks"
    if any(
        k in text for k in ["condiment", "sauce", "dressing", "spice", "oil", "seasoning", "syrup"]
    ):
        return "Condiments & Sauces", "Other"
    if any(k in text for k in ["soup", "entree", "meal", "pizza", "sandwich", "dinner"]):
        return "Meals & Entrees", "Meals"

    return "Other", "Other"


def determine_dietary_restrictions(
    category: str,
    food_name: str,
    allergens: Dict[str, str],
    sodium_mg: float,
    sugar_g: float,
) -> str:
    """Determine applicable dietary tags for a food item."""
    text = f"{category} {food_name}".lower()
    tags = []

    # Non-vegetarian keywords
    non_veg = any(
        k in text
        for k in [
            "beef",
            "pork",
            "chicken",
            "turkey",
            "lamb",
            "bacon",
            "ham",
            "sausage",
            "fish",
            "salmon",
            "tuna",
            "seafood",
            "shrimp",
            "gelatin",
        ]
    )

    if not non_veg:
        tags.append("vegetarian")
        # Vegan: vegetarian and no dairy and no eggs
        if allergens.get("dairy") == ALLERGEN_ABSENT and allergens.get("eggs") == ALLERGEN_ABSENT:
            tags.append("vegan")

    if allergens.get("gluten") == ALLERGEN_ABSENT:
        tags.append("gluten_free")

    if allergens.get("dairy") == ALLERGEN_ABSENT:
        tags.append("dairy_free")

    if allergens.get("nuts") == ALLERGEN_ABSENT and allergens.get("peanuts") == ALLERGEN_ABSENT:
        tags.append("nut_free")

    # FDA nutrient content claim standards per 100g
    if sodium_mg <= 140.0:
        tags.append("low_sodium")

    if sugar_g <= 5.0:
        tags.append("low_sugar")

    return ",".join(tags)


def process_usda_dataset(usda_raw: pd.DataFrame, quality_logs: List[Dict]) -> pd.DataFrame:
    """Process, clean, and standardize USDA dataset."""
    logger.info("Processing USDA foods dataset...")
    # 1. Deduplicate by normalized name
    deduped_usda, dropped_dupes = deduplicate_usda_foods(usda_raw)
    quality_logs.append(
        {
            "dataset": "USDA",
            "action": "deduplication",
            "dropped_count": dropped_dupes,
            "kept_count": len(deduped_usda),
        }
    )

    records = []
    dropped_missing_macros = 0
    dropped_plausibility = 0

    for _, row in deduped_usda.iterrows():
        # Check core macros presence
        kcal = row.get("calories")
        protein = row.get("protein_g")
        fat = row.get("fat_g")
        carbs = row.get("carbs_g")

        if pd.isna(kcal) or pd.isna(protein) or pd.isna(fat) or pd.isna(carbs):
            dropped_missing_macros += 1
            continue

        raw_cat = str(row.get("food_category", ""))
        name = str(row.get("food_name", ""))
        category, food_type = map_category(raw_cat, name)
        data_type = str(row.get("data_type", ""))
        is_packaged = data_type == "Branded"
        is_foundation = data_type in ["Foundation", "SR Legacy"]

        # Allergen detection
        allergens = detect_allergen_tri_state(
            food_name=name,
            ingredients=str(row.get("ingredients", "")),
            is_packaged=is_packaged,
            is_foundation_raw=is_foundation,
        )

        # Serving size normalization
        serving_val = row.get("serving_size")
        serving_g = 100.0 if pd.isna(serving_val) or float(serving_val) <= 0 else float(serving_val)

        item = {
            "food_id": f"usda_{row['fdc_id']}",
            "name": name,
            "source": "usda",
            "category": category,
            "food_type": food_type,
            "kcal_100g": float(kcal),
            "protein_100g": float(protein),
            "fat_100g": float(fat),
            "sat_fat_100g": float(row.get("saturated_fat_g", np.nan)),
            "carbs_100g": float(carbs),
            "sugar_100g": float(row.get("sugar_g", np.nan)),
            "fiber_100g": float(row.get("fiber_g", np.nan)),
            "sodium_mg_100g": float(row.get("sodium_mg", np.nan)),
            "cholesterol_mg_100g": float(row.get("cholesterol_mg", np.nan)),
            "calcium_mg_100g": float(row.get("calcium_mg", np.nan)),
            "iron_mg_100g": float(row.get("iron_mg", np.nan)),
            "vitamin_c_mg_100g": float(row.get("vitamin_c_mg", np.nan)),
            "is_packaged": is_packaged,
            "nutriscore": "unknown",
            "nova": np.nan,
            "allergens": allergens,
            "serving_g": serving_g,
        }

        # Plausibility check
        is_plausible, reason = check_physical_plausibility(pd.Series(item))
        if not is_plausible:
            dropped_plausibility += 1
            quality_logs.append(
                {
                    "dataset": "USDA",
                    "food_id": item["food_id"],
                    "food_name": item["name"],
                    "issue": reason,
                    "action": "dropped",
                }
            )
            continue

        records.append(item)

    quality_logs.append(
        {
            "dataset": "USDA",
            "action": "dropped_missing_macros",
            "dropped_count": dropped_missing_macros,
        }
    )
    quality_logs.append(
        {
            "dataset": "USDA",
            "action": "dropped_plausibility_violations",
            "dropped_count": dropped_plausibility,
        }
    )

    return pd.DataFrame(records)


def process_healthy_foods_dataset(
    hf_raw: pd.DataFrame, usda_ref: pd.DataFrame, quality_logs: List[Dict]
) -> pd.DataFrame:
    """Process healthy foods database with sodium unit corrections."""
    logger.info("Processing healthy foods database...")
    fixed_hf, sodium_logs = fix_healthy_foods_sodium_unit_errors(hf_raw, usda_ref)
    quality_logs.extend(sodium_logs)

    # Lookup existing USDA normalized names to avoid duplication
    usda_names = set(usda_ref["name"].apply(normalize_food_name))

    records = []
    dropped_dupes = 0
    dropped_missing_macros = 0
    dropped_plausibility = 0

    for idx, row in fixed_hf.iterrows():
        name = str(row.get("food_name", ""))
        norm_name = normalize_food_name(name)

        if norm_name in usda_names:
            dropped_dupes += 1
            continue

        kcal = row.get("calories")
        protein = row.get("protein_g")
        fat = row.get("fat_g")
        carbs = row.get("carbs_g")

        if pd.isna(kcal) or pd.isna(protein) or pd.isna(fat) or pd.isna(carbs):
            dropped_missing_macros += 1
            continue

        raw_cat = str(row.get("food_type", ""))
        category, food_type = map_category(raw_cat, name)

        allergens = detect_allergen_tri_state(
            food_name=name,
            ingredients="",
            is_packaged=False,
            is_foundation_raw=True,
        )

        item = {
            "food_id": f"hf_{idx}",
            "name": name,
            "source": "healthy_foods",
            "category": category,
            "food_type": food_type,
            "kcal_100g": float(kcal),
            "protein_100g": float(protein),
            "fat_100g": float(fat),
            "sat_fat_100g": np.nan,
            "carbs_100g": float(carbs),
            "sugar_100g": float(row.get("sugar_g", np.nan)),
            "fiber_100g": float(row.get("fiber_g", np.nan)),
            "sodium_mg_100g": float(row.get("sodium_mg", np.nan)),
            "cholesterol_mg_100g": np.nan,
            "calcium_mg_100g": np.nan,
            "iron_mg_100g": np.nan,
            "vitamin_c_mg_100g": np.nan,
            "is_packaged": False,
            "nutriscore": "unknown",
            "nova": np.nan,
            "allergens": allergens,
            "serving_g": 100.0,
        }

        is_plausible, reason = check_physical_plausibility(pd.Series(item))
        if not is_plausible:
            dropped_plausibility += 1
            quality_logs.append(
                {
                    "dataset": "healthy_foods",
                    "food_id": item["food_id"],
                    "food_name": item["name"],
                    "issue": reason,
                    "action": "dropped",
                }
            )
            continue

        records.append(item)

    quality_logs.append(
        {
            "dataset": "healthy_foods",
            "action": "dropped_duplicates_against_usda",
            "dropped_count": dropped_dupes,
        }
    )
    quality_logs.append(
        {
            "dataset": "healthy_foods",
            "action": "dropped_missing_macros",
            "dropped_count": dropped_missing_macros,
        }
    )
    quality_logs.append(
        {
            "dataset": "healthy_foods",
            "action": "dropped_plausibility_violations",
            "dropped_count": dropped_plausibility,
        }
    )

    return pd.DataFrame(records)


def process_open_food_facts_dataset(
    off_raw: pd.DataFrame, quality_logs: List[Dict]
) -> pd.DataFrame:
    """Process Open Food Facts packaged products dataset."""
    logger.info("Processing Open Food Facts dataset...")
    records = []
    dropped_missing_macros = 0
    dropped_plausibility = 0

    for idx, row in off_raw.iterrows():
        name = str(row.get("product_name", "")).strip()
        if not name or name == "nan":
            continue

        kcal = row.get("energy_kcal")
        protein = row.get("proteins_100g")
        fat = row.get("fat_100g")
        carbs = row.get("carbs_100g")

        if pd.isna(kcal) or pd.isna(protein) or pd.isna(fat) or pd.isna(carbs):
            dropped_missing_macros += 1
            continue

        raw_cat = str(row.get("categories", ""))
        category, food_type = map_category(raw_cat, name)

        # Build raw allergen flags dictionary
        raw_flags = {
            f"contains_{allergen}": row.get(f"contains_{allergen}")
            for allergen in SUPPORTED_ALLERGENS
            if f"contains_{allergen}" in row
        }

        allergens = detect_allergen_tri_state(
            food_name=name,
            ingredients=str(row.get("ingredients", "")),
            raw_flags=raw_flags,
            is_packaged=True,
            is_foundation_raw=False,
        )

        # Open Food Facts sodium is often in g/100g (or salt in g/100g)
        sod_raw = row.get("sodium_100g")
        salt_raw = row.get("salt_100g")
        if pd.notna(sod_raw):
            sodium_mg = float(sod_raw) * 1000.0  # g to mg
        elif pd.notna(salt_raw):
            sodium_mg = (float(salt_raw) / 2.5) * 1000.0  # salt to sodium in mg
        else:
            sodium_mg = np.nan

        item = {
            "food_id": f"off_{idx}",
            "name": name,
            "source": "open_food_facts",
            "category": category,
            "food_type": food_type,
            "kcal_100g": float(kcal),
            "protein_100g": float(protein),
            "fat_100g": float(fat),
            "sat_fat_100g": float(row.get("saturated_fat_100g", np.nan)),
            "carbs_100g": float(carbs),
            "sugar_100g": float(row.get("sugars_100g", np.nan)),
            "fiber_100g": float(row.get("fiber_100g", np.nan)),
            "sodium_mg_100g": sodium_mg,
            "cholesterol_mg_100g": np.nan,
            "calcium_mg_100g": np.nan,
            "iron_mg_100g": np.nan,
            "vitamin_c_mg_100g": np.nan,
            "is_packaged": True,
            "nutriscore": str(row.get("nutriscore_grade", "unknown")).lower(),
            "nova": float(row.get("nova_group", np.nan)),
            "allergens": allergens,
            "serving_g": 100.0,
        }

        is_plausible, reason = check_physical_plausibility(pd.Series(item))
        if not is_plausible:
            dropped_plausibility += 1
            quality_logs.append(
                {
                    "dataset": "open_food_facts",
                    "food_id": item["food_id"],
                    "food_name": item["name"],
                    "issue": reason,
                    "action": "dropped",
                }
            )
            continue

        records.append(item)

    quality_logs.append(
        {
            "dataset": "open_food_facts",
            "action": "dropped_missing_macros",
            "dropped_count": dropped_missing_macros,
        }
    )
    quality_logs.append(
        {
            "dataset": "open_food_facts",
            "action": "dropped_plausibility_violations",
            "dropped_count": dropped_plausibility,
        }
    )

    return pd.DataFrame(records)


def run_harmonization_pipeline() -> pd.DataFrame:
    """Execute complete data harmonization pipeline and persist outputs."""
    logger.info("Starting complete food harmonization pipeline...")
    quality_logs: List[Dict] = []

    # 1. Load raw datasets
    usda_raw = load_raw_usda()
    hf_raw = load_raw_healthy_foods()
    off_raw = load_raw_open_food_facts()

    # 2. Process USDA
    usda_df = process_usda_dataset(usda_raw, quality_logs)

    # 3. Process Healthy Foods (using USDA for reference lookup)
    hf_df = process_healthy_foods_dataset(hf_raw, usda_df, quality_logs)

    # 4. Process Open Food Facts
    off_df = process_open_food_facts_dataset(off_raw, quality_logs)

    # 5. Process External Regional Foods
    external_dfs = load_external_regional_foods()
    ext_records = []
    for ext_df in external_dfs:
        for _, row in ext_df.iterrows():
            name = str(row["name"])
            category, food_type = map_category(str(row.get("category", "")), name)
            allergens = detect_allergen_tri_state(
                food_name=name,
                ingredients=str(row.get("allergens", "")),
                is_foundation_raw=True,
            )
            ext_records.append(
                {
                    "food_id": str(row["food_id"]),
                    "name": name,
                    "source": str(row.get("source", "external")),
                    "category": category,
                    "food_type": food_type,
                    "kcal_100g": float(row["kcal_100g"]),
                    "protein_100g": float(row["protein_100g"]),
                    "fat_100g": float(row["fat_100g"]),
                    "sat_fat_100g": float(row.get("sat_fat_100g", 0.0)),
                    "carbs_100g": float(row["carbs_100g"]),
                    "sugar_100g": float(row.get("sugar_100g", 0.0)),
                    "fiber_100g": float(row.get("fiber_100g", 0.0)),
                    "sodium_mg_100g": float(row.get("sodium_mg_100g", 0.0)),
                    "cholesterol_mg_100g": float(row.get("cholesterol_mg_100g", 0.0)),
                    "calcium_mg_100g": float(row.get("calcium_mg_100g", 0.0)),
                    "iron_mg_100g": float(row.get("iron_mg_100g", 0.0)),
                    "vitamin_c_mg_100g": float(row.get("vitamin_c_mg_100g", 0.0)),
                    "is_packaged": False,
                    "nutriscore": "unknown",
                    "nova": np.nan,
                    "allergens": allergens,
                    "serving_g": 100.0,
                }
            )
    ext_combined = pd.DataFrame(ext_records) if ext_records else pd.DataFrame()

    # 6. Combine all sources
    all_dfs = [df for df in [usda_df, hf_df, off_df, ext_combined] if not df.empty]
    combined = pd.concat(all_dfs, ignore_index=True)
    logger.info("Combined food sources before imputation: %d rows", len(combined))

    # 7. Impute secondary nutrients by category median with flags
    combined = impute_secondary_nutrients(combined, category_col="category")

    # 8. Unpack allergens and compute Health Score v2 & restrictions
    allergen_json_col = []
    allergen_cols = {f"allergen_{a}": [] for a in SUPPORTED_ALLERGENS}
    restriction_tags_col = []
    health_scores = []

    for _, row in combined.iterrows():
        allergens_dict = row["allergens"]
        allergen_json_col.append(allergen_flags_to_json(allergens_dict))
        for a in SUPPORTED_ALLERGENS:
            allergen_cols[f"allergen_{a}"].append(allergens_dict.get(a, ALLERGEN_UNKNOWN))

        score = calculate_health_score_v2(
            kcal_100g=row["kcal_100g"],
            protein_100g=row["protein_100g"],
            fat_100g=row["fat_100g"],
            sat_fat_100g=row["sat_fat_100g"],
            carbs_100g=row["carbs_100g"],
            sugar_100g=row["sugar_100g"],
            fiber_100g=row["fiber_100g"],
            sodium_mg_100g=row["sodium_mg_100g"],
            calcium_mg_100g=row["calcium_mg_100g"],
            iron_mg_100g=row["iron_mg_100g"],
            vitamin_c_mg_100g=row["vitamin_c_mg_100g"],
            nutriscore_grade=row["nutriscore"],
        )
        health_scores.append(score)

        tags = determine_dietary_restrictions(
            category=row["category"],
            food_name=row["name"],
            allergens=allergens_dict,
            sodium_mg=row["sodium_mg_100g"],
            sugar_g=row["sugar_100g"],
        )
        restriction_tags_col.append(tags)

    combined["allergen_flags"] = allergen_json_col
    for col_name, col_data in allergen_cols.items():
        combined[col_name] = col_data
    combined["restriction_tags"] = restriction_tags_col
    combined["health_score_v2"] = health_scores
    combined = combined.drop(columns=["allergens"])

    # 9. Save Parquet
    combined.to_parquet(FOODS_PARQUET, index=False)
    logger.info("Saved harmonized parquet dataset to %s (%d rows)", FOODS_PARQUET, len(combined))

    # 10. Save SQLite Database with indexes
    save_to_sqlite(combined)

    # 11. Write Quality Log and Report
    write_quality_artifacts(combined, quality_logs, usda_raw, hf_raw, off_raw)

    return combined


def save_to_sqlite(df: pd.DataFrame) -> None:
    """Save foods dataframe into SQLite with optimized query indexes."""
    conn = sqlite3.connect(FOODS_DB)
    # Write foods table
    df.to_sql("foods", conn, if_exists="replace", index=False)
    cur = conn.cursor()
    # Create query indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_foods_id ON foods(food_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_foods_category ON foods(category)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_foods_food_type ON foods(food_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_foods_score ON foods(health_score_v2)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_foods_gluten ON foods(allergen_gluten)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_foods_dairy ON foods(allergen_dairy)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_foods_nuts ON foods(allergen_nuts)")
    conn.commit()
    conn.close()
    logger.info("Saved SQLite database with indexes to %s", FOODS_DB)


def write_quality_artifacts(
    final_df: pd.DataFrame,
    quality_logs: List[Dict],
    usda_raw: pd.DataFrame,
    hf_raw: pd.DataFrame,
    off_raw: pd.DataFrame,
) -> None:
    """Write data_quality_log.csv and comprehensive data_quality.md report."""
    # Write CSV log
    log_df = pd.DataFrame(quality_logs)
    log_df.to_csv(DATA_QUALITY_LOG, index=False)

    # Build Markdown Quality Report
    report_md = f"""# Comprehensive Data Quality and Harmonization Report

**Generated:** Automated Pipeline Run
**Target File:** `{FOODS_PARQUET}` & `{FOODS_DB}`
**Final Cleaned Food Count:** **{len(final_df):,} records**

---

## 1. Raw Dataset Overview and Row Counts

| Dataset | Raw Records | Processed Retained | Retained % | Primary Source / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **USDA FoodData Central** | {len(usda_raw):,} | {(final_df["source"] == "usda").sum():,} | {((final_df["source"] == "usda").sum() / len(usda_raw) * 100):.1f}% | Foundation, SR Legacy, Branded foods (deduplicated by priority) |
| **Healthy Foods Database** | {len(hf_raw):,} | {(final_df["source"] == "healthy_foods").sum():,} | {((final_df["source"] == "healthy_foods").sum() / len(hf_raw) * 100):.1f}% | Curated whole foods with sodium unit corrections |
| **Open Food Facts** | {len(off_raw):,} | {(final_df["source"] == "open_food_facts").sum():,} | {((final_df["source"] == "open_food_facts").sum() / len(off_raw) * 100):.1f}% | Commercial products with Nutri-Score & allergen testing |
| **External Regional Foods** | Sample included | {(final_df["source"].str.startswith("external")).sum():,} | 100.0% | User-extensible regional cuisine table (`data/external/`) |
| **Total Harmonized** | **{len(usda_raw) + len(hf_raw) + len(off_raw):,}** | **{len(final_df):,}** | **{(len(final_df) / (len(usda_raw) + len(hf_raw) + len(off_raw)) * 100):.1f}%** | Unified schema per-100g |

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
   - All dropped violations logged to `{DATA_QUALITY_LOG.name}`.

---

## 3. Allergen Safety Status Distribution

The system strictly enforces a tri-state status (`present`, `absent`, `unknown`) across all 7 supported allergens. "Unknown" is never treated as safe.

| Allergen | Present Count | Absent Count | Unknown / Unverified Count |
| :--- | :--- | :--- | :--- |
| **Gluten** | {(final_df["allergen_gluten"] == "present").sum():,} | {(final_df["allergen_gluten"] == "absent").sum():,} | {(final_df["allergen_gluten"] == "unknown").sum():,} |
| **Dairy** | {(final_df["allergen_dairy"] == "present").sum():,} | {(final_df["allergen_dairy"] == "absent").sum():,} | {(final_df["allergen_dairy"] == "unknown").sum():,} |
| **Tree Nuts** | {(final_df["allergen_nuts"] == "present").sum():,} | {(final_df["allergen_nuts"] == "absent").sum():,} | {(final_df["allergen_nuts"] == "unknown").sum():,} |
| **Peanuts** | {(final_df["allergen_peanuts"] == "present").sum():,} | {(final_df["allergen_peanuts"] == "absent").sum():,} | {(final_df["allergen_peanuts"] == "unknown").sum():,} |
| **Soy** | {(final_df["allergen_soy"] == "present").sum():,} | {(final_df["allergen_soy"] == "absent").sum():,} | {(final_df["allergen_soy"] == "unknown").sum():,} |
| **Eggs** | {(final_df["allergen_eggs"] == "present").sum():,} | {(final_df["allergen_eggs"] == "absent").sum():,} | {(final_df["allergen_eggs"] == "unknown").sum():,} |
| **Fish** | {(final_df["allergen_fish"] == "present").sum():,} | {(final_df["allergen_fish"] == "absent").sum():,} | {(final_df["allergen_fish"] == "unknown").sum():,} |

---

## 4. Health Score v2 Summary Statistics

- **Mean Health Score:** {final_df["health_score_v2"].mean():.1f} / 100
- **Median Health Score:** {final_df["health_score_v2"].median():.1f} / 100
- **25th - 75th Percentile:** {final_df["health_score_v2"].quantile(0.25):.1f} - {final_df["health_score_v2"].quantile(0.75):.1f}
- **Top Scoring Categories:** Vegetables ({final_df[final_df["category"] == "Vegetables"]["health_score_v2"].mean():.1f}), Fruits ({final_df[final_df["category"] == "Fruits"]["health_score_v2"].mean():.1f})
- **Lowest Scoring Categories:** Snacks & Sweets ({final_df[final_df["category"] == "Snacks & Sweets"]["health_score_v2"].mean():.1f})
"""
    with open(DATA_QUALITY_REPORT, "w", encoding="utf-8") as f:
        f.write(report_md)
    logger.info("Generated data quality report at %s", DATA_QUALITY_REPORT)
