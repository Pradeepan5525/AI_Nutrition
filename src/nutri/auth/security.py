"""Cryptographic security utilities for Argon2/PBKDF2 hashing, JWT access tokens, and refresh tokens."""

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from nutri.database.engine import SECRET_KEY

# Configuration defaults
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS = int(os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
PBKDF2_ROUNDS = 100000

argon2_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str, scheme: str = "argon2") -> str:
    """Hash a plaintext password using Argon2id (default) or salted PBKDF2-HMAC-SHA256."""
    if scheme == "pbkdf2":
        salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ROUNDS,
        )
        return f"pbkdf2:sha256:{PBKDF2_ROUNDS}${salt}${key.hex()}"

    # Default: Argon2id
    return argon2_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify plaintext password against Argon2, PBKDF2, or Bcrypt stored hashes."""
    if not hashed_password or not password:
        return False

    # Argon2
    if hashed_password.startswith("$argon2"):
        try:
            return argon2_hasher.verify(hashed_password, password)
        except (VerifyMismatchError, VerificationError):
            return False
        except Exception:
            return False

    # PBKDF2
    if hashed_password.startswith("pbkdf2:"):
        try:
            parts = hashed_password.split("$")
            if len(parts) != 3:
                return False
            header, salt, stored_hash = parts
            _, _, rounds_str = header.split(":")
            rounds = int(rounds_str)

            computed = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                rounds,
            ).hex()

            return hmac.compare_digest(computed, stored_hash)
        except Exception:
            return False

    # Bcrypt fallback
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password rules: at least 8 characters, letters and numbers."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, ""


EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$")


def validate_email_format(email: str) -> bool:
    """Validate that the email has a standard valid structure."""
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token with 15-30 min default lifetime."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def generate_refresh_token() -> str:
    """Generate a high-entropy cryptographically secure refresh token string."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Create a SHA-256 hash of the refresh token for safe storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
