"""FastAPI authentication and authorization dependencies."""

from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from nutri.auth.security import decode_access_token
from nutri.auth.user_db import get_user_db
from nutri.auth.user_service import format_user_dict
from nutri.database.engine import SessionLocal
from nutri.database.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[Dict[str, Any]]:
    """Retrieve current user from JWT token if provided; otherwise return None."""
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    identifier = str(payload["sub"])
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter((User.username == identifier) | (User.email == identifier.lower()))
            .first()
        )
        if user and user.is_active:
            return format_user_dict(user)
    finally:
        db.close()

    # Fallback to UserDB
    legacy_db = get_user_db()
    return legacy_db.get_user_by_username(identifier) or legacy_db.get_user_by_email(identifier)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """Require a valid JWT token and return the authenticated user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    identifier = str(payload["sub"])
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter((User.username == identifier) | (User.email == identifier.lower()))
            .first()
        )
        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return format_user_dict(user)
    finally:
        db.close()

    # Fallback to UserDB
    legacy_db = get_user_db()
    legacy_user = legacy_db.get_user_by_username(identifier) or legacy_db.get_user_by_email(identifier)
    if not legacy_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return legacy_user


def require_clinician(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Ensure the authenticated user has a clinician or admin role."""
    if user.get("role") not in ("clinician", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinician role required to access this resource.",
        )
    return user
