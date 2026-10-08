"""BMI calculation and category classification with WHO and Asian cut-offs."""

from typing import Dict, Tuple


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate Body Mass Index (BMI).

    Formula: weight (kg) / [height (m)]^2
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Weight and height must be strictly positive numbers.")
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m**2)
    return round(bmi, 2)


def get_bmi_category(bmi: float, use_asian_cutoffs: bool = False) -> Dict[str, str]:
    """Classify BMI into clinical categories.

    Standard WHO Adult Cut-offs:
    - Underweight: < 18.5
    - Normal weight: 18.5 - 24.9
    - Overweight: 25.0 - 29.9
    - Obesity Class I: 30.0 - 34.9
    - Obesity Class II: 35.0 - 39.9
    - Obesity Class III: >= 40.0

    Asian Population Cut-offs (WHO Expert Consultation 2004):
    - Underweight: < 18.5
    - Normal weight: 18.5 - 22.9
    - Overweight: 23.0 - 27.4
    - Obese: >= 27.5
    """
    if use_asian_cutoffs:
        if bmi < 18.5:
            cat = "Underweight"
            desc = "Below healthy weight threshold for Asian populations"
        elif bmi <= 22.9:
            cat = "Normal weight"
            desc = "Optimal health and weight range for Asian populations"
        elif bmi <= 27.4:
            cat = "Overweight"
            desc = "Increased risk of comorbidities (Asian criteria)"
        else:
            cat = "Obese"
            desc = "High risk of cardiovascular and metabolic comorbidities"
    else:
        if bmi < 18.5:
            cat = "Underweight"
            desc = "Below standard healthy adult weight range"
        elif bmi <= 24.9:
            cat = "Normal weight"
            desc = "Healthy adult weight range"
        elif bmi <= 29.9:
            cat = "Overweight"
            desc = "Above healthy weight range (pre-obesity)"
        elif bmi <= 34.9:
            cat = "Obesity Class I"
            desc = "Moderate obesity risk"
        elif bmi <= 39.9:
            cat = "Obesity Class II"
            desc = "Severe obesity risk"
        else:
            cat = "Obesity Class III"
            desc = "Very severe / morbid obesity risk"

    return {
        "category": cat,
        "description": desc,
        "criteria": "Asian-specific (WHO 2004)" if use_asian_cutoffs else "Standard WHO",
    }


def calculate_ideal_weight_range(
    height_cm: float, use_asian_cutoffs: bool = False
) -> Tuple[float, float]:
    """Calculate healthy body weight range based on normal BMI cutoffs.

    Returns:
        (min_weight_kg, max_weight_kg) rounded to 1 decimal place.
    """
    if height_cm <= 0:
        raise ValueError("Height must be strictly positive.")
    height_m = height_cm / 100.0
    min_bmi = 18.5
    max_bmi = 22.9 if use_asian_cutoffs else 24.9
    min_weight = min_bmi * (height_m**2)
    max_weight = max_bmi * (height_m**2)
    return round(min_weight, 1), round(max_weight, 1)
