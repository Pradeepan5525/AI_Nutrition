"""Configuration and constants for Nutrition Intelligence System."""

from pathlib import Path

# Base Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_INTERIM_DIR = DATA_DIR / "interim"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_EXTERNAL_DIR = DATA_DIR / "external"
REPORTS_DIR = ROOT_DIR / "reports"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
DOCS_DIR = ROOT_DIR / "docs"

# Specific File Paths
FOODS_PARQUET = DATA_PROCESSED_DIR / "foods.parquet"
FOODS_DB = DATA_PROCESSED_DIR / "foods.db"
DATA_QUALITY_LOG = REPORTS_DIR / "data_quality_log.csv"
DATA_QUALITY_REPORT = REPORTS_DIR / "data_quality.md"

RAW_OBESITY_CSV = DATA_RAW_DIR / "ObesityDataSet_raw_and_data_sinthetic.csv"
RAW_DIET_CSV = DATA_RAW_DIR / "diet_recommendations_dataset.csv"
RAW_USDA_CSV = DATA_RAW_DIR / "comprehensive_foods_usda.csv"
RAW_HEALTHY_CSV = DATA_RAW_DIR / "healthy_foods_database.csv"
RAW_OFF_CSV = DATA_RAW_DIR / "foods_health_scores_allergens.csv"
RAW_DIETARY_CSV = DATA_RAW_DIR / "foods_dietary_restrictions.csv"
RAW_ALLERGENS_CSV = DATA_RAW_DIR / "foods_allergens.csv"

# Model Artifacts
MODEL_DIR = ARTIFACTS_DIR / "models"
MODEL_PATH = MODEL_DIR / "obesity_risk_pipeline.joblib"
CALIBRATED_MODEL_PATH = MODEL_DIR / "obesity_risk_calibrated.joblib"
MODEL_METRICS_PATH = MODEL_DIR / "model_metrics.json"

# Global Random Seed
SEED: int = 42

# Nutrition Guidelines Constants
MIN_KCAL_WOMEN: float = 1200.0
MIN_KCAL_MEN: float = 1500.0
MAX_SODIUM_MG: float = 2300.0
HYPERTENSION_SODIUM_MG: float = 1500.0
FIBER_PER_1000_KCAL: float = 14.0

# Supported Allergens
SUPPORTED_ALLERGENS = [
    "gluten",
    "dairy",
    "nuts",
    "peanuts",
    "soy",
    "eggs",
    "fish",
]

# Physical Plausibility Limits per 100g
PLAUSIBILITY_LIMITS = {
    "min_kcal": 0.0,
    "max_kcal": 900.0,
    "max_macros_sum_g": 105.0,  # sum of protein + fat + carbs (accounting for measurement variance)
    "min_nutrient": 0.0,
}
