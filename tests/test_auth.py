"""Unit and integration tests for authentication, JWT issuance, and user management."""

import tempfile
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from nutri.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from nutri.auth.user_db import UserDB

client = TestClient(app)


def test_password_hashing_and_verification():
    """Verify that password hashing is salted, non-deterministic, and verifies correctly."""
    pwd = "SecretPassword123!"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)

    # Hashes must differ due to random salt
    assert hash1 != hash2
    assert hash1.startswith("$argon2") or hash1.startswith("pbkdf2:sha256:100000$")

    # Correct password verifies
    assert verify_password(pwd, hash1) is True
    assert verify_password(pwd, hash2) is True

    # Incorrect password fails
    assert verify_password("WrongPassword", hash1) is False
    assert verify_password("", hash1) is False
    assert verify_password(pwd, "invalid_hash_string") is False


def test_jwt_token_creation_and_decoding():
    """Verify JWT token encoding, decoding, and expiration rejection."""
    payload = {"sub": "test_patient", "role": "patient", "user_id": 42}
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "test_patient"
    assert decoded["role"] == "patient"
    assert decoded["user_id"] == 42
    assert "exp" in decoded

    # Expired token
    expired_token = create_access_token(payload, expires_delta=timedelta(seconds=-10))
    assert decode_access_token(expired_token) is None

    # Tampered token
    tampered_token = token[:-4] + "xxxx"
    assert decode_access_token(tampered_token) is None


def test_user_db_in_isolated_sqlite():
    """Verify UserDB CRUD and demo seeding in a clean temporary database."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_users.db"
        user_db = UserDB(db_path=db_path)

        # Demo users seeded
        demo_patient = user_db.get_user_by_username("demo_user")
        assert demo_patient is not None
        assert demo_patient["role"] == "patient"
        assert demo_patient["email"] == "patient@example.com"
        assert demo_patient["saved_profile"]["weight_kg"] == 76.5

        demo_clinician = user_db.get_user_by_username("clinician_demo")
        assert demo_clinician is not None
        assert demo_clinician["role"] == "clinician"

        # Authentication of seeded users
        auth_ok = user_db.authenticate_user("demo_user", "demo123")
        assert auth_ok is not None
        assert auth_ok["username"] == "demo_user"

        auth_bad = user_db.authenticate_user("demo_user", "wrong_pass")
        assert auth_bad is None

        # Authenticate by email
        auth_email = user_db.authenticate_user("patient@example.com", "demo123")
        assert auth_email is not None

        # Create new user
        new_user = user_db.create_user(
            username="john_doe",
            email="john@example.com",
            password="mySecurePassword123",
            full_name="John Doe",
            role="patient",
        )
        assert new_user["id"] is not None
        assert new_user["username"] == "john_doe"

        # Profile update
        user_db.update_user_profile(new_user["id"], {"daily_calorie_target": 2100})
        updated = user_db.get_user_by_id(new_user["id"])
        assert updated is not None
        assert updated["saved_profile"]["daily_calorie_target"] == 2100


def test_api_auth_register_and_duplicate_handling():
    """Verify user registration endpoint via FastAPI test client."""
    import uuid

    unique_user = f"user_{uuid.uuid4().hex[:8]}_test"
    payload = {
        "username": unique_user,
        "email": f"{unique_user}@clinical-test.org",
        "password": "Password123!",
        "full_name": "Test User",
        "role": "patient",
        "initial_profile": {"weight_kg": 70.0, "height_cm": 175.0},
    }

    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == unique_user
    assert data["user"]["saved_profile"]["weight_kg"] == 70.0

    # Duplicate username should be rejected with 400
    dup_resp = client.post("/api/v1/auth/register", json=payload)
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["detail"]


def test_api_auth_login_json_and_oauth2():
    """Verify JSON login and standard OAuth2 form login."""
    # JSON login with seeded demo account
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "demo_user", "password": "demo123"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # OAuth2 Form login (used by Swagger UI Authorize button)
    form_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "demo_user", "password": "demo123"},
    )
    assert form_resp.status_code == 200
    assert "access_token" in form_resp.json()

    # Invalid login
    bad_resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "demo_user", "password": "wrongpassword"},
    )
    assert bad_resp.status_code == 401

    # Protected endpoint /me
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "demo_user"

    # Protected endpoint without token
    unauth_resp = client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401


def test_api_auth_profile_update_and_role_permissions():
    """Verify profile updating and clinician role-based permissions."""
    # Login as patient
    patient_token = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "demo_user", "password": "demo123"},
    ).json()["access_token"]

    # Update profile
    new_profile = {"age": 35, "weight_kg": 75.0, "goal": "muscle_gain"}
    up_resp = client.put(
        "/api/v1/auth/profile",
        json={"profile": new_profile},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["saved_profile"]["goal"] == "muscle_gain"

    # Patient accessing clinician-only endpoint /api/v1/auth/users should get 403
    users_forbidden = client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert users_forbidden.status_code == 403

    # Login as clinician
    clinician_token = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "clinician_demo", "password": "admin123"},
    ).json()["access_token"]

    # Clinician accessing /api/v1/auth/users should succeed with 200
    users_allowed = client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert users_allowed.status_code == 200
    users_list = users_allowed.json()
    assert isinstance(users_list, list)
    assert len(users_list) >= 2
