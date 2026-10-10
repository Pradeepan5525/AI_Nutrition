"""Integration tests for the FastAPI REST API endpoints."""

from fastapi.testclient import TestClient

from api.main import app
from nutri.auth.security import create_access_token

client = TestClient(app)
_token = create_access_token({"sub": "demo_user", "user_id": 1, "role": "patient"})
client.headers.update({"Authorization": f"Bearer {_token}"})


def test_health_endpoint():
    """Verify system health, database connection, and model loading status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["database_connected"] is True
    assert data["total_foods_indexed"] > 30000


def test_version_endpoint():
    """Verify API version metadata."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"
    assert "LightGBM" in data["model_architecture"]


def test_assess_endpoint_standard_user():
    """Verify anthropometric and metabolic assessment for healthy adult."""
    payload = {
        "age": 28,
        "sex": "female",
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "activity_level": "moderate",
        "goal": "maintenance",
        "is_asian": False,
        "is_pregnant": False,
        "is_lactating": False,
        "has_ed_history": False,
        "condition_flags": [],
    }
    response = client.post("/assess", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert 21.0 <= data["bmi"] <= 23.0
    assert data["bmi_category"] == "Normal weight"
    assert data["bmr_kcal"] > 1200
    assert data["tdee_kcal"] > data["bmr_kcal"]
    assert data["safety_gate"]["cleared"] is True
    assert "disclaimer" in data


def test_assess_endpoint_clinical_conditions_and_safety_gate():
    """Verify safety gate flags and clinical constraints for multi-condition profile."""
    payload = {
        "age": 78,  # Senior > 75 triggers safety gate
        "sex": "male",
        "height_cm": 175.0,
        "weight_kg": 95.0,
        "activity_level": "sedentary",
        "goal": "weight_loss",
        "is_asian": False,
        "is_pregnant": False,
        "is_lactating": False,
        "has_ed_history": False,
        "condition_flags": ["hypertension", "diabetes"],
    }
    response = client.post("/assess", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Safety gate should flag senior age
    assert data["safety_gate"]["cleared"] is False
    assert any("Senior" in f for f in data["safety_gate"]["flags"])

    # Clinical rules should reflect AHA and ADA limits
    constraints = data["clinical_constraints"]
    assert constraints["max_sodium_mg"] <= 1500.0  # AHA DASH
    assert (
        constraints["max_sugar_g"] <= round((data["target_kcal"] * 0.05 / 4.0), 1) + 0.1
    )  # ADA 5%
    assert len(constraints["audit_trail"]) >= 2


def test_assess_endpoint_validation_error():
    """Verify invalid payloads are rejected with 422."""
    payload = {
        "age": -5,  # Invalid age
        "sex": "other",  # Invalid enum
        "height_cm": 350.0,  # Out of range
        "weight_kg": 10.0,  # Below minimum
        "activity_level": "super_active",  # Invalid
    }
    response = client.post("/assess", json=payload)
    assert response.status_code == 422


def test_risk_screening_endpoint():
    """Verify lifestyle obesity risk screening and SHAP explanation."""
    payload = {
        "age": 24.0,
        "gender": "Female",
        "family_history_with_overweight": "yes",
        "favc": "yes",
        "fcvc": 2.0,
        "ncp": 3.0,
        "caec": "Sometimes",
        "smoke": "no",
        "ch2o": 2.0,
        "scc": "no",
        "faf": 1.0,
        "tue": 1.0,
        "calc": "Sometimes",
        "mtrans": "Public_Transportation",
    }
    response = client.post("/risk", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["predicted_category"] in ["Underweight", "Healthy", "Overweight", "Obese"]
    assert len(data["probabilities"]) == 4
    assert round(sum(data["probabilities"].values()), 1) == 1.0
    assert len(data["top_risk_factors"]) >= 1
    assert "disclaimer" in data


def test_foods_search_and_pagination():
    """Verify search filtering, allergen exclusion, and pagination."""
    response = client.get("/foods/search?q=apple&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_matches"] > 0
    assert len(data["results"]) <= 10
    assert any("apple" in item["name"].lower() for item in data["results"])


def test_foods_swaps_endpoint():
    """Verify healthier swaps endpoint returns superior alternatives."""
    # Find a food to test swaps on
    search_res = client.get("/foods/search?q=chips&page_size=5")
    search_data = search_res.json()
    assert search_data["total_matches"] > 0
    test_food_id = search_data["results"][0]["food_id"]

    response = client.get(f"/foods/{test_food_id}/swaps?max_swaps=3")
    assert response.status_code == 200
    data = response.json()
    assert "original_food" in data
    assert "swaps" in data
    for swap in data["swaps"]:
        assert swap["health_score_v2"] > data["original_food"]["health_score_v2"]


def test_foods_swaps_not_found():
    """Verify 404 for unknown food ID."""
    response = client.get("/foods/non_existent_id_9999/swaps")
    assert response.status_code == 404


def test_meal_plan_optimizer_endpoint():
    """Verify meal plan optimization endpoint solves and aggregates grocery list."""
    payload = {
        "target_kcal": 2000.0,
        "protein_target_g": 110.0,
        "max_sodium_mg": 2300.0,
        "max_sat_fat_g": 22.0,
        "max_sugar_g": 50.0,
        "user_allergies": ["peanuts"],
        "dietary_restrictions": [],
        "strict_allergens": True,
        "days": 1,
    }
    response = client.post("/plan", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["days_requested"] == 1
    assert len(data["daily_plans"]) == 1
    assert "grocery_list" in data
    assert data["solver_time_sec"] > 0.0

    # Verify calories within ±8%
    day1_kcal = data["daily_plans"][0]["daily_totals"]["kcal"]
    assert 1840.0 <= day1_kcal <= 2160.0


def test_report_pdf_generation_endpoint():
    """Verify PDF report streaming endpoint."""
    payload = {
        "client_info": {
            "age": 32,
            "sex": "male",
            "height_cm": 180.0,
            "weight_kg": 78.0,
            "bmi": 24.1,
            "bmi_category": "Normal",
            "bmr": 1780.0,
            "tdee": 2450.0,
        },
        "target_nutrition": {
            "target_kcal": 2100.0,
            "protein_g": 140.0,
            "carbs_g": 220.0,
            "fat_g": 70.0,
            "fiber_g": 30.0,
            "sugar_g": 45.0,
            "water_ml": 2800.0,
        },
        "safety_gate": {
            "cleared": True,
            "flags": [],
        },
        "clinical_rules": {
            "active_rules": ["General Health Maintenance"],
        },
    }
    response = client.post("/report", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        "attachment; filename=clinical_nutrition_report.pdf"
        in response.headers["content-disposition"]
    )
    assert len(response.content) > 1000
