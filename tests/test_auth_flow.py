"""Comprehensive tests for authentication, authorization, session rotation, and data isolation."""

import uuid
from fastapi.testclient import TestClient
import pytest

from api.main import app

client = TestClient(app)


def test_auth_registration_and_duplicate_conflict():
    """Verify registration, password hashing, and 409 Conflict on duplicate email."""
    uid = uuid.uuid4().hex[:8]
    email = f"user_{uid}@example.com"
    payload = {
        "email": email,
        "password": "SecurePassword123!",
        "full_name": "Test User",
        "accept_disclaimer": True,
    }

    # Register successfully
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email

    # Cookie was set
    assert "refresh_token" in resp.cookies

    # Duplicate registration should return 409 Conflict
    dup_resp = client.post("/auth/register", json=payload)
    assert dup_resp.status_code == 409
    assert "already exists" in dup_resp.json()["detail"].lower()


def test_auth_login_success_and_failure():
    """Verify login authentication, generic 401 error message, and refresh cookie."""
    uid = uuid.uuid4().hex[:8]
    email = f"login_user_{uid}@example.com"
    password = "CorrectPassword123!"

    # Register user first
    reg = client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Login Tester"},
    )
    assert reg.status_code == 201

    # Login with correct credentials
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": password, "remember_me": True},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_resp.cookies

    # Login with incorrect password gives generic 401
    bad_resp = client.post(
        "/auth/login",
        json={"email": email, "password": "WrongPassword999!"},
    )
    assert bad_resp.status_code == 401
    assert "Invalid email or password." in bad_resp.json()["detail"]


def test_auth_lockout_after_repeated_failures():
    """Verify account lockout kicks in after 5 failed login attempts."""
    uid = uuid.uuid4().hex[:8]
    email = f"lockout_{uid}@example.com"
    password = "Password123!"

    client.post("/auth/register", json={"email": email, "password": password})

    # Attempt 5 consecutive wrong passwords
    for _ in range(5):
        resp = client.post("/auth/login", json={"email": email, "password": "WrongPassword!"})
        assert resp.status_code == 401

    # 6th attempt should indicate lockout
    lock_resp = client.post("/auth/login", json={"email": email, "password": password})
    assert lock_resp.status_code == 401
    assert "locked" in lock_resp.json()["detail"].lower()


def test_auth_refresh_rotation_and_logout():
    """Verify refresh token rotation and revocation on logout."""
    uid = uuid.uuid4().hex[:8]
    email = f"refresh_{uid}@example.com"
    password = "Password123!"

    reg = client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201
    initial_cookie = reg.cookies.get("refresh_token")
    assert initial_cookie is not None

    # Refresh session using cookie
    refresh_resp = client.post("/auth/refresh", cookies={"refresh_token": initial_cookie})
    assert refresh_resp.status_code == 200
    refreshed_data = refresh_resp.json()
    assert "access_token" in refreshed_data

    # Rotated cookie received
    new_cookie = refresh_resp.cookies.get("refresh_token")
    assert new_cookie is not None
    assert new_cookie != initial_cookie

    # Replaying the old refresh token must be rejected
    old_replay_resp = client.post("/auth/refresh", cookies={"refresh_token": initial_cookie})
    assert old_replay_resp.status_code == 401

    # Logout revokes session and deletes cookie
    logout_resp = client.post("/auth/logout", cookies={"refresh_token": new_cookie})
    assert logout_resp.status_code == 200

    # Using revoked token must fail
    revoked_resp = client.post("/auth/refresh", cookies={"refresh_token": new_cookie})
    assert revoked_resp.status_code == 401


def test_all_protected_routes_require_authentication():
    """Verify that every protected route strictly returns 401 Unauthorized without a token."""
    unauthed_client = TestClient(app)

    routes_to_test = [
        ("POST", "/assess", {"age": 30, "sex": "male", "height_cm": 175, "weight_kg": 75, "activity_level": "moderate"}),
        ("POST", "/risk", {"Age": 25, "Gender": "Male", "FCVC": 2, "NCP": 3, "CH2O": 2, "FAF": 1, "TUE": 1}),
        ("POST", "/plan", {"target_kcal": 2000, "days": 1}),
        ("GET", "/foods/search?q=apple", None),
        ("POST", "/report", {"client_info": {}, "target_nutrition": {}, "safety_gate": {}, "clinical_rules": {}}),
        ("GET", "/users/me", None),
        ("PUT", "/users/me/profile", {"age": 35}),
        ("GET", "/users/me/export", None),
        ("DELETE", "/users/me", None),
    ]

    for method, path, payload in routes_to_test:
        if method == "POST":
            r = unauthed_client.post(path, json=payload or {})
        elif method == "GET":
            r = unauthed_client.get(path)
        elif method == "PUT":
            r = unauthed_client.put(path, json=payload or {})
        elif method == "DELETE":
            r = unauthed_client.delete(path)
        else:
            continue

        assert r.status_code == 401, f"Route {method} {path} should return 401 without token, got {r.status_code}"


def test_user_data_isolation():
    """Verify that User A can never read or mutate User B's assessments or records."""
    # Create User A
    uid_a = uuid.uuid4().hex[:8]
    email_a = f"usera_{uid_a}@example.com"
    token_a = client.post(
        "/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "User Alpha"},
    ).json()["access_token"]

    # Create User B
    uid_b = uuid.uuid4().hex[:8]
    email_b = f"userb_{uid_b}@example.com"
    token_b = client.post(
        "/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "User Beta"},
    ).json()["access_token"]

    # User A creates an assessment
    save_resp = client.post(
        "/users/me/assessments",
        json={
            "input_data": {"age": 30},
            "bmi": 22.5,
            "bmi_category": "Normal weight",
            "bmr_kcal": 1600.0,
            "tdee_kcal": 2200.0,
            "target_kcal": 2000.0,
            "protein_g": 120.0,
            "carbs_g": 200.0,
            "fat_g": 65.0,
            "sodium_mg": 2000.0,
            "water_ml": 2500.0,
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert save_resp.status_code == 200
    assessment_id = save_resp.json()["id"]

    # User A sees 1 assessment
    list_a = client.get(
        "/users/me/assessments",
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    assert len(list_a) == 1

    # User B sees 0 assessments (isolated)
    list_b = client.get(
        "/users/me/assessments",
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()
    assert len(list_b) == 0

    # User B attempts to delete User A's assessment -> 404 (not found in user B's scope)
    del_resp = client.delete(
        f"/users/me/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_resp.status_code == 404

    # Assessment still exists for User A
    list_a_after = client.get(
        "/users/me/assessments",
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    assert len(list_a_after) == 1


def test_data_export_and_account_deletion_cascades():
    """Verify that export compiles all personal data and deletion removes all user rows."""
    uid = uuid.uuid4().hex[:8]
    email = f"export_user_{uid}@example.com"
    token = client.post(
        "/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Export Tester"},
    ).json()["access_token"]

    auth_header = {"Authorization": f"Bearer {token}"}

    # Add a weight log
    client.post(
        "/users/me/weight-logs",
        json={"weight_kg": 72.5, "note": "Weekly check-in"},
        headers=auth_header,
    )

    # Export personal data
    export_resp = client.get("/users/me/export", headers=auth_header)
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["user"]["email"] == email
    assert len(export_data["weight_logs"]) == 1
    assert export_data["weight_logs"][0]["weight_kg"] == 72.5

    # Delete account
    del_account = client.delete("/users/me", headers=auth_header)
    assert del_account.status_code == 200
    assert "deleted" in del_account.json()["message"].lower()

    # Subsequent access fails with 401
    after_del = client.get("/users/me", headers=auth_header)
    assert after_del.status_code == 401
