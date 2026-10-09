"""Authentication router providing registration, login, and profile persistence."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.deps import get_current_user, require_clinician
from api.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserRegisterRequest,
    UserResponse,
)
from nutri.auth.security import create_access_token
from nutri.auth.user_db import get_user_db

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register_user(payload: UserRegisterRequest) -> TokenResponse:
    """Create a new user account, return account details and a signed JWT."""
    db = get_user_db()
    if db.get_user_by_username(payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{payload.username}' is already registered.",
        )
    if db.get_user_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email address '{payload.email}' is already registered.",
        )

    user = db.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        initial_profile=payload.initial_profile,
    )

    token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"], "role": user["role"]}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT access token",
)
def login_user(payload: UserLoginRequest) -> TokenResponse:
    """Validate credentials and return a signed JWT access token."""
    db = get_user_db()
    user = db.authenticate_user(payload.username_or_email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"], "role": user["role"]}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user),
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 Password Flow token endpoint (for Swagger UI Authorize)",
)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    """OAuth2 standard form-encoded authentication endpoint."""
    db = get_user_db()
    user = db.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"], "role": user["role"]}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve current authenticated user profile",
)
def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Return the profile, saved metabolic metrics, and roles for the logged-in user."""
    return UserResponse(**current_user)


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update saved nutritional and metabolic profile for current user",
)
def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Persist updated anthropometric, clinical, and dietary parameters to user account."""
    db = get_user_db()
    updated = db.update_user_profile(current_user["id"], payload.profile)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile.",
        )
    return UserResponse(**updated)


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all registered system users (Clinicians only)",
)
def list_system_users(
    _: Dict[str, Any] = Depends(require_clinician),
) -> List[UserResponse]:
    """Clinician-only administrative overview of registered patient accounts."""
    db = get_user_db()
    users = db.list_users()
    return [UserResponse(**u) for u in users]
