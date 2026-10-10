"""Authentication router providing registration, login, refresh rotation, logout, and profile persistence."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.deps import get_current_user, require_clinician
from api.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserRegisterRequest,
    UserResponse,
)
from nutri.auth.security import create_access_token
from nutri.auth.user_service import (
    authenticate_user_full,
    create_user_refresh_token,
    format_user_dict,
    register_user_full,
    revoke_refresh_token,
    update_profile_for_user,
    verify_and_rotate_refresh_token,
)
from nutri.database.engine import get_db
from nutri.database.models import User

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    request: Request,
    response: Response,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Create a new user account with argon2 password hashing and issuance of access and refresh tokens."""
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")
    full_name = payload.get("full_name")
    username = payload.get("username")
    role = payload.get("role", "patient")
    initial_profile = payload.get("initial_profile")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")

    # Check for legacy username-first requests
    if username and db.query(User).filter(User.username.ilike(username.strip())).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' is already registered.",
        )

    user, err = register_user_full(
        db=db,
        email=email,
        password=password,
        full_name=full_name,
        username=username,
        role=role,
        initial_profile=initial_profile,
    )

    if err:
        if err.startswith("CONFLICT:"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err.replace("CONFLICT:", ""))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    # Issue JWT access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )

    # Issue refresh token and set cookie
    refresh_token = create_user_refresh_token(db, user.id, remember_me=False)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production
        max_age=7 * 24 * 3600,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**format_user_dict(user)),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT access token and refresh cookie",
)
def login(
    request: Request,
    response: Response,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Validate credentials, support lockout after repeated failures, issue access token and refresh cookie."""
    identifier = payload.get("email") or payload.get("username_or_email") or payload.get("username", "")
    password = payload.get("password", "")
    remember_me = bool(payload.get("remember_me", False))

    if not identifier or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, err = authenticate_user_full(db, str(identifier), str(password))
    if err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password." if "locked" not in err.lower() else err,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )

    # Issue refresh token with cookie
    days = 30 if remember_me else 7
    refresh_token = create_user_refresh_token(db, user.id, remember_me=remember_me)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=days * 24 * 3600,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**format_user_dict(user)),
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 Password Flow token endpoint (for Swagger UI Authorize)",
)
def login_oauth2(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """OAuth2 standard form-encoded authentication endpoint."""
    user, err = authenticate_user_full(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )
    refresh_token = create_user_refresh_token(db, user.id)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=7 * 24 * 3600,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**format_user_dict(user)),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotate refresh token and issue new access token")
def refresh_token_endpoint(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Exchange valid refresh cookie for new access token and rotated refresh cookie."""
    token_val = refresh_token
    if not token_val:
        # Fallback to authorization or body header if cookie missing
        auth_header = request.headers.get("X-Refresh-Token")
        if auth_header:
            token_val = auth_header

    if not token_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required in cookie.",
        )

    user, new_refresh_token = verify_and_rotate_refresh_token(db, token_val)
    if not user or not new_refresh_token:
        response.delete_cookie(key="refresh_token", path="/")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired, please sign in again.",
        )

    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=7 * 24 * 3600,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**format_user_dict(user)),
    )


@router.post("/logout", summary="Revoke session and clear refresh cookie")
def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Revoke active refresh token and remove cookie."""
    if refresh_token:
        revoke_refresh_token(db, refresh_token)
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse, summary="Retrieve current authenticated user profile")
def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Return profile and metadata for currently authenticated user."""
    return UserResponse(**current_user)


@router.put("/profile", response_model=UserResponse, summary="Update saved profile for current user")
def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update profile parameters."""
    updated = update_profile_for_user(db, current_user["id"], payload.profile)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update profile.")
    return UserResponse(**updated)


@router.get("/users", response_model=List[UserResponse], summary="List all registered system users (Clinicians only)")
def list_system_users(
    _: Dict[str, Any] = Depends(require_clinician),
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    """Clinician-only administrative overview."""
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserResponse(**format_user_dict(u)) for u in users]
