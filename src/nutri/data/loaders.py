"""Data loaders and schema validation for raw nutrition datasets."""

from pathlib import Path
from typing import Any, List, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from nutri.config import (
    RAW_ALLERGENS_CSV,
    RAW_DIET_CSV,
    RAW_DIETARY_CSV,
    RAW_HEALTHY_CSV,
    RAW_OBESITY_CSV,
    RAW_OFF_CSV,
    RAW_USDA_CSV,
)
from nutri.logging import setup_logger

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Schemas for Raw Datasets
# ---------------------------------------------------------------------------


class RawObesityRow(BaseModel):
    """Schema for raw obesity dataset rows."""

    Gender: str
    Age: float
    Height: float
    Weight: float
    family_history_with_overweight: str
    FAVC: str
    FCVC: float
    NCP: float
    CAEC: str
    SMOKE: str
    CH2O: float
    SCC: str
    FAF: float
    TUE: float
    CALC: str
    MTRANS: str
    NObeyesdad: str


class RawDietRow(BaseModel):
    """Schema for raw diet recommendations dataset rows."""

    model_config = ConfigDict(populate_by_name=True)

    Patient_ID: str
    Age: int
    Gender: str
    Weight_kg: float
    Height_cm: float
    BMI: float
    Disease_Type: Optional[str] = None
    Severity: Optional[str] = None
    Physical_Activity_Level: str
    Daily_Caloric_Intake: float
    Cholesterol_mg_dL: Optional[float] = Field(default=None, alias="Cholesterol_mg/dL")
    Blood_Pressure_mmHg: Optional[Any] = None
    Glucose_mg_dL: Optional[float] = Field(default=None, alias="Glucose_mg/dL")
    Dietary_Restrictions: Optional[str] = None
    Allergies: Optional[str] = None
    Preferred_Cuisine: Optional[str] = None
    Weekly_Exercise_Hours: Optional[float] = None
    Adherence_to_Diet_Plan: Optional[Any] = None
    Dietary_Nutrient_Imbalance_Score: Optional[float] = None
    Diet_Recommendation: str


class ExternalRegionalFoodRow(BaseModel):
    """Schema for user-provided regional food datasets in data/external/."""

    food_id: str
    name: str
    category: str
    food_type: str
    kcal_100g: float
    protein_100g: float
    fat_100g: float
    sat_fat_100g: Optional[float] = 0.0
    carbs_100g: float
    sugar_100g: Optional[float] = 0.0
    fiber_100g: Optional[float] = 0.0
    sodium_mg_100g: Optional[float] = 0.0
    cholesterol_mg_100g: Optional[float] = 0.0
    calcium_mg_100g: Optional[float] = 0.0
    iron_mg_100g: Optional[float] = 0.0
    vitamin_c_mg_100g: Optional[float] = 0.0
    allergens: Optional[str] = ""
    dietary_tags: Optional[str] = ""


# ---------------------------------------------------------------------------
# Loader Functions with Schema Validation
# ---------------------------------------------------------------------------


def validate_dataframe_schema(df: pd.DataFrame, schema_cls: Any, sample_size: int = 50) -> bool:
    """Validate sample of dataframe records against a Pydantic schema."""
    sample = df.head(sample_size).to_dict(orient="records")
    for idx, row in enumerate(sample):
        try:
            # Handle NaN values as None for optional Pydantic fields
            cleaned_row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
            schema_cls(**cleaned_row)
        except ValidationError as e:
            logger.error("Schema validation failed at sample row %d: %s", idx, e)
            raise e
    return True


def load_raw_obesity(path: Optional[Path] = None) -> pd.DataFrame:
    """Load raw obesity dataset and validate expected columns."""
    filepath = path or RAW_OBESITY_CSV
    if not filepath.exists():
        raise FileNotFoundError(f"Obesity dataset not found at {filepath}")
    df = pd.read_csv(filepath)
    required_cols = [
        "Gender",
        "Age",
        "Height",
        "Weight",
        "family_history_with_overweight",
        "FAVC",
        "FCVC",
        "NCP",
        "CAEC",
        "SMOKE",
        "CH2O",
        "SCC",
        "FAF",
        "TUE",
        "CALC",
        "MTRANS",
        "NObeyesdad",
    ]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in obesity dataset: {missing}")
    validate_dataframe_schema(df, RawObesityRow)
    logger.info("Loaded raw obesity dataset: %d rows, %d cols", len(df), df.shape[1])
    return df


def load_raw_diet_recommendations(path: Optional[Path] = None) -> pd.DataFrame:
    """Load raw diet recommendations dataset and validate columns."""
    filepath = path or RAW_DIET_CSV
    if not filepath.exists():
        raise FileNotFoundError(f"Diet recommendations dataset not found at {filepath}")
    df = pd.read_csv(filepath)
    required_cols = [
        "Patient_ID",
        "Age",
        "Gender",
        "Weight_kg",
        "Height_cm",
        "BMI",
        "Daily_Caloric_Intake",
        "Diet_Recommendation",
    ]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in diet recommendations: {missing}")
    validate_dataframe_schema(df, RawDietRow)
    logger.info("Loaded raw diet recommendations dataset: %d rows, %d cols", len(df), df.shape[1])
    return df


def load_raw_usda(path: Optional[Path] = None) -> pd.DataFrame:
    """Load comprehensive USDA foods dataset."""
    filepath = path or RAW_USDA_CSV
    if not filepath.exists():
        raise FileNotFoundError(f"USDA dataset not found at {filepath}")
    df = pd.read_csv(filepath, low_memory=False)
    required_cols = ["fdc_id", "food_name", "calories", "protein_g", "fat_g", "carbs_g"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in USDA dataset: {missing}")
    logger.info("Loaded USDA foods dataset: %d rows, %d cols", len(df), df.shape[1])
    return df


def load_raw_healthy_foods(path: Optional[Path] = None) -> pd.DataFrame:
    """Load healthy foods database."""
    filepath = path or RAW_HEALTHY_CSV
    if not filepath.exists():
        raise FileNotFoundError(f"Healthy foods dataset not found at {filepath}")
    df = pd.read_csv(filepath)
    required_cols = ["food_name", "calories", "protein_g", "fat_g", "carbs_g"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in Healthy Foods dataset: {missing}")
    logger.info("Loaded healthy foods dataset: %d rows, %d cols", len(df), df.shape[1])
    return df


def load_raw_open_food_facts(path: Optional[Path] = None) -> pd.DataFrame:
    """Load Open Food Facts health scores & allergens dataset."""
    filepath = path or RAW_OFF_CSV
    if not filepath.exists():
        raise FileNotFoundError(f"Open Food Facts dataset not found at {filepath}")
    df = pd.read_csv(filepath, low_memory=False)
    required_cols = ["product_name", "energy_kcal", "proteins_100g", "fat_100g", "carbs_100g"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in OFF dataset: {missing}")
    logger.info("Loaded Open Food Facts dataset: %d rows, %d cols", len(df), df.shape[1])
    return df


def load_raw_dietary_restrictions(path: Optional[Path] = None) -> pd.DataFrame:
    """Load foods dietary restrictions dataset."""
    filepath = path or RAW_DIETARY_CSV
    if not filepath.exists():
        raise FileNotFoundError(f"Dietary restrictions dataset not found at {filepath}")
    df = pd.read_csv(filepath)
    logger.info("Loaded dietary restrictions dataset: %d rows", len(df))
    return df


def load_raw_allergens(path: Optional[Path] = None) -> pd.DataFrame:
    """Load foods allergens dataset."""
    filepath = path or RAW_ALLERGENS_CSV
    if not filepath.exists():
        raise FileNotFoundError(f"Allergens dataset not found at {filepath}")
    df = pd.read_csv(filepath)
    logger.info("Loaded allergens dataset: %d rows", len(df))
    return df


def load_external_regional_foods(dir_path: Optional[Path] = None) -> List[pd.DataFrame]:
    """Scan data/external/ directory and load any regional food CSV files.

    Validates schema against ExternalRegionalFoodRow.
    """
    directory = dir_path or (RAW_USDA_CSV.parent.parent / "external")
    dfs: List[pd.DataFrame] = []
    if not directory.exists():
        return dfs

    for file_path in directory.glob("*.csv"):
        try:
            df = pd.read_csv(file_path)
            validate_dataframe_schema(df, ExternalRegionalFoodRow, sample_size=min(10, len(df)))
            df["source"] = f"external_{file_path.stem}"
            dfs.append(df)
            logger.info("Loaded regional foods from %s (%d rows)", file_path.name, len(df))
        except Exception as e:
            logger.warning(
                "Skipping external file %s due to schema mismatch: %s", file_path.name, e
            )
    return dfs
