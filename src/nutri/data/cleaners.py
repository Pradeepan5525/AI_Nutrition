"""Cleaning, normalization, and plausibility verification for food data."""

import re
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from nutri.config import PLAUSIBILITY_LIMITS
from nutri.logging import setup_logger

logger = setup_logger(__name__)


def normalize_food_name(name: str) -> str:
    """Normalize food name string for deduplication and matching."""
    if not isinstance(name, str) or not name.strip():
        return ""
    # Lowercase
    clean = name.lower().strip()
    # Replace non-alphanumeric (except commas and spaces) with spaces
    clean = re.sub(r"[^a-z0-9\s,]", "", clean)
    # Collapse whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def check_physical_plausibility(
    row: pd.Series,
) -> Tuple[bool, Optional[str]]:
    """Validate physical plausibility on a per-100g basis.

    Rules:
    - Calories between 0 and 900 kcal/100g.
    - Macros sum (protein + fat + carbs) <= 105g/100g.
    - Saturated fat <= total fat (with 0.5g tolerance for measurement precision).
    - Sugar <= total carbs (with 1.0g tolerance for measurement precision).
    - No negative values.
    """
    kcal = row.get("kcal_100g", 0.0)
    protein = row.get("protein_100g", 0.0)
    fat = row.get("fat_100g", 0.0)
    carbs = row.get("carbs_100g", 0.0)
    sat_fat = row.get("sat_fat_100g", 0.0)
    sugar = row.get("sugar_100g", 0.0)
    sodium = row.get("sodium_mg_100g", 0.0)

    # Negative check
    for val, name in [
        (kcal, "kcal"),
        (protein, "protein"),
        (fat, "fat"),
        (carbs, "carbs"),
        (sat_fat, "sat_fat"),
        (sugar, "sugar"),
        (sodium, "sodium"),
    ]:
        if pd.notna(val) and val < 0.0:
            return False, f"Negative value for {name}: {val}"

    # Calorie range
    if pd.notna(kcal):
        if kcal < PLAUSIBILITY_LIMITS["min_kcal"] or kcal > PLAUSIBILITY_LIMITS["max_kcal"]:
            return False, f"Calories out of range [0, 900]: {kcal}"

    # Macros sum
    if pd.notna(protein) and pd.notna(fat) and pd.notna(carbs):
        macro_sum = protein + fat + carbs
        if macro_sum > PLAUSIBILITY_LIMITS["max_macros_sum_g"]:
            return False, f"Macros sum exceeds 105g/100g: {macro_sum:.1f}g"

    # Saturated fat <= fat
    if pd.notna(sat_fat) and pd.notna(fat):
        if sat_fat > fat + 0.5:
            return False, f"Saturated fat ({sat_fat:.1f}g) exceeds total fat ({fat:.1f}g)"

    # Sugar <= carbs
    if pd.notna(sugar) and pd.notna(carbs):
        if sugar > carbs + 1.0:
            return False, f"Sugar ({sugar:.1f}g) exceeds total carbohydrates ({carbs:.1f}g)"

    # Sodium absurd values check (> 50,000 mg/100g = 50% pure salt)
    if pd.notna(sodium) and sodium > 50000.0:
        return False, f"Sodium implausibly high: {sodium:.0f} mg/100g"

    return True, None


def fix_healthy_foods_sodium_unit_errors(
    hf_df: pd.DataFrame, usda_ref_df: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, List[Dict]]:
    """Detect and fix or drop unit errors in healthy foods sodium_mg.

    Identifies foods where sodium_mg is below 5mg but known to be reported in grams
    (e.g., Almond butter at 0.996g = 996mg), or implausible salt bombs.
    """
    fixed_df = hf_df.copy()
    logs: List[Dict] = []

    # Map USDA foods by normalized name for quick lookup
    usda_lookup = {}
    if usda_ref_df is not None and not usda_ref_df.empty:
        for _, row in usda_ref_df.iterrows():
            norm = normalize_food_name(str(row.get("food_name", "")))
            if norm and norm not in usda_lookup:
                usda_lookup[norm] = row.get("sodium_mg", np.nan)

    for idx, row in fixed_df.iterrows():
        sod = row.get("sodium_mg")
        name = str(row.get("food_name", ""))

        if pd.isna(sod):
            continue

        # Absurd extreme high sodium (e.g. 1,000,000 mg)
        if sod > 50000.0:
            logs.append(
                {
                    "food_name": name,
                    "source": "healthy_foods",
                    "issue": "extreme_high_sodium",
                    "original_val": sod,
                    "action": "set_nan_for_imputation",
                    "fixed_val": np.nan,
                }
            )
            fixed_df.at[idx, "sodium_mg"] = np.nan
            continue

        # Fractional sodium below 5.0 for processed or savory foods
        if 0.0 < sod < 5.0 and (sod % 1.0 != 0.0):
            # Check if likely in grams (e.g., 0.996 g -> 996 mg)
            # Nut butters, cheese, cooked foods
            converted = sod * 1000.0
            if converted <= 3000.0:
                logs.append(
                    {
                        "food_name": name,
                        "source": "healthy_foods",
                        "issue": "sodium_in_grams_unit_error",
                        "original_val": sod,
                        "action": "multiplied_by_1000",
                        "fixed_val": converted,
                    }
                )
                fixed_df.at[idx, "sodium_mg"] = converted
            else:
                logs.append(
                    {
                        "food_name": name,
                        "source": "healthy_foods",
                        "issue": "suspicious_low_fractional_sodium",
                        "original_val": sod,
                        "action": "set_nan_for_imputation",
                        "fixed_val": np.nan,
                    }
                )
                fixed_df.at[idx, "sodium_mg"] = np.nan

    logger.info("Processed healthy foods sodium unit check: %d corrections logged", len(logs))
    return fixed_df, logs


def impute_secondary_nutrients(df: pd.DataFrame, category_col: str = "category") -> pd.DataFrame:
    """Impute secondary nutrients using category medians with explicit tracking flags.

    Core macros (kcal, protein, fat, carbs) must NEVER be imputed blindly;
    rows missing core macros are dropped beforehand.
    """
    df = df.copy()
    secondary_cols = [
        "sat_fat_100g",
        "sugar_100g",
        "fiber_100g",
        "sodium_mg_100g",
        "cholesterol_mg_100g",
        "calcium_mg_100g",
        "iron_mg_100g",
        "vitamin_c_mg_100g",
    ]

    for col in secondary_cols:
        if col not in df.columns:
            df[col] = np.nan

        imputed_flag_col = f"{col.replace('_100g', '')}_imputed"
        df[imputed_flag_col] = df[col].isna()

        # Calculate category median, fallback to global median, fallback to 0.0
        cat_medians = df.groupby(category_col)[col].transform("median")
        global_median = df[col].median()
        if pd.isna(global_median):
            global_median = 0.0

        fill_series = cat_medians.fillna(global_median).fillna(0.0)
        df[col] = df[col].fillna(fill_series)

        # Round to 2 decimal places
        df[col] = df[col].round(2)

    return df


def deduplicate_usda_foods(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Deduplicate USDA foods by normalized name, prioritizing Foundation > SR Legacy > Branded."""
    df = df.copy()
    df["norm_name"] = df["food_name"].apply(normalize_food_name)

    # Score completeness of secondary nutrients
    secondary = [
        "saturated_fat_g",
        "sugar_g",
        "fiber_g",
        "sodium_mg",
        "calcium_mg",
        "iron_mg",
        "vitamin_c_mg",
        "cholesterol_mg",
    ]
    df["completeness"] = df[secondary].notna().sum(axis=1)

    # Priority mapping: Foundation (3) > SR Legacy (2) > Branded (1) > Other (0)
    type_priority = {"Foundation": 3, "SR Legacy": 2, "Branded": 1}
    df["type_priority"] = df["data_type"].map(type_priority).fillna(0)

    # Sort descending by priority, then completeness, then fdc_id
    df_sorted = df.sort_values(
        by=["type_priority", "completeness", "fdc_id"],
        ascending=[False, False, True],
    )

    before_count = len(df)
    deduped = df_sorted.drop_duplicates(subset=["norm_name"], keep="first")
    dropped_count = before_count - len(deduped)

    # Drop temporary sorting columns
    deduped = deduped.drop(columns=["norm_name", "completeness", "type_priority"])
    logger.info(
        "USDA deduplication: dropped %d duplicate records, kept %d", dropped_count, len(deduped)
    )
    return deduped, dropped_count
