"""Feature engineering, schema definition, and preprocessing for obesity risk model."""

from typing import Dict, List

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Explicit list of permitted input features (STRICTLY EXCLUDING Height, Weight, BMI)
NUMERIC_FEATURES: List[str] = [
    "Age",
    "FCVC",  # Frequency of vegetable consumption (1 to 3)
    "NCP",  # Number of main meals (1 to 4)
    "CH2O",  # Daily water intake (1 to 3)
    "FAF",  # Physical activity frequency (0 to 3)
    "TUE",  # Time using technology/screen devices (0 to 2)
]

CATEGORICAL_FEATURES: List[str] = [
    "Gender",
    "family_history_with_overweight",
    "FAVC",  # Frequent consumption of high-caloric food (yes/no)
    "CAEC",  # Consumption of food between meals / snacking (no/Sometimes/Frequently/Always)
    "SMOKE",  # Smoking habit (yes/no)
    "SCC",  # Calories monitoring (yes/no)
    "CALC",  # Alcohol consumption (no/Sometimes/Frequently/Always)
    "MTRANS",  # Transportation used (Automobile, Bike, Motorbike, Public_Transportation, Walking)
]

ALL_FEATURE_COLUMNS: List[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Target mappings
SEVEN_CLASS_NAMES: List[str] = [
    "Insufficient_Weight",
    "Normal_Weight",
    "Overweight_Level_I",
    "Overweight_Level_II",
    "Obesity_Type_I",
    "Obesity_Type_II",
    "Obesity_Type_III",
]

FOUR_TIER_MAPPING: Dict[str, str] = {
    "Insufficient_Weight": "Underweight",
    "Normal_Weight": "Healthy",
    "Overweight_Level_I": "Overweight",
    "Overweight_Level_II": "Overweight",
    "Obesity_Type_I": "Obese",
    "Obesity_Type_II": "Obese",
    "Obesity_Type_III": "Obese",
}

FOUR_TIER_NAMES: List[str] = ["Underweight", "Healthy", "Overweight", "Obese"]


def extract_likely_original_mask(df: pd.DataFrame) -> pd.Series:
    """Identify rows that are likely genuine human survey responses.

    Criteria (Section 3.1):
    Rows where Age and all five ordinal survey columns (FCVC, NCP, CH2O, FAF, TUE)
    are whole numbers (non-fractional integers), which synthetic SMOTE interpolates.
    """
    is_int = df["Age"] % 1 == 0
    ordinal_cols = ["FCVC", "NCP", "CH2O", "FAF", "TUE"]
    for col in ordinal_cols:
        is_int = is_int & (df[col] % 1 == 0)
    return is_int


def build_preprocessor() -> ColumnTransformer:
    """Construct standard scikit-learn ColumnTransformer for obesity features."""
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor


def validate_risk_features(data: Dict[str, any]) -> pd.DataFrame:
    """Validate and clean user input dictionary into single-row DataFrame.

    Checks value boundaries and normalizes categories.
    """
    row = {}
    lower_data = {str(k).lower(): v for k, v in data.items()}

    # Numeric checks
    for col in NUMERIC_FEATURES:
        k = col.lower()
        if k not in lower_data and col not in data:
            raise ValueError(f"Missing required numeric feature: {col}")
        val = float(lower_data.get(k, data.get(col)))
        row[col] = val

    # Boundary plausibility
    if not (10.0 <= row["Age"] <= 100.0):
        raise ValueError(f"Age out of plausible range [10, 100]: {row['Age']}")
    if not (1.0 <= row["FCVC"] <= 3.0):
        row["FCVC"] = max(1.0, min(3.0, row["FCVC"]))
    if not (1.0 <= row["NCP"] <= 4.0):
        row["NCP"] = max(1.0, min(4.0, row["NCP"]))
    if not (1.0 <= row["CH2O"] <= 3.0):
        row["CH2O"] = max(1.0, min(3.0, row["CH2O"]))
    if not (0.0 <= row["FAF"] <= 3.0):
        row["FAF"] = max(0.0, min(3.0, row["FAF"]))
    if not (0.0 <= row["TUE"] <= 2.0):
        row["TUE"] = max(0.0, min(2.0, row["TUE"]))

    # Categorical checks
    mtrans_map = {
        "automobile": "Automobile",
        "bike": "Bike",
        "motorbike": "Motorbike",
        "public_transportation": "Public_Transportation",
        "walking": "Walking",
    }

    for col in CATEGORICAL_FEATURES:
        k = col.lower()
        if k not in lower_data and col not in data:
            raise ValueError(f"Missing required categorical feature: {col}")
        val_str = str(lower_data.get(k, data.get(col))).strip()

        if col == "Gender":
            row[col] = val_str.capitalize()
        elif col in ["FAVC", "SMOKE", "SCC", "family_history_with_overweight"]:
            row[col] = val_str.lower()
        elif col in ["CAEC", "CALC"]:
            row[col] = "no" if val_str.lower() == "no" else val_str.capitalize()
        elif col == "MTRANS":
            row[col] = mtrans_map.get(val_str.lower(), val_str)
        else:
            row[col] = val_str

    return pd.DataFrame([row])
