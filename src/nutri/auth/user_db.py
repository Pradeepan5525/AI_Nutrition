"""SQLite user persistence manager with profile storage and demo seeding."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from nutri.auth.security import hash_password, verify_password
from nutri.config import DATA_PROCESSED_DIR


class UserDB:
    """Manages user registration, authentication, and clinical profile storage."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = DATA_PROCESSED_DIR / "foods.db"
        else:
            self.db_path = Path(db_path)

        self._init_db()
        self._seed_demo_users()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Provide a managed sqlite3 connection that always closes cleanly."""
        conn = sqlite3.connect(str(self.db_path), timeout=20.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create the users table if it does not already exist."""
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT NOT NULL DEFAULT 'patient',
                    saved_profile_json TEXT,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.commit()

    def _seed_demo_users(self) -> None:
        """Seed default demo accounts for effortless evaluation."""
        if not self.get_user_by_username("demo_user"):
            default_patient_profile = {
                "age": 32,
                "gender": "male",
                "weight_kg": 76.5,
                "height_cm": 178.0,
                "activity_level": "moderately_active",
                "goal": "lose_weight",
                "use_asian_bmi": False,
                "conditions": ["hypertension"],
                "allergens": ["peanuts"],
                "dietary_preference": "omnivore",
            }
            self.create_user(
                username="demo_user",
                email="patient@example.com",
                password="demo123",
                full_name="Alex Carter (Patient)",
                role="patient",
                initial_profile=default_patient_profile,
            )

        if not self.get_user_by_username("clinician_demo"):
            default_clinician_profile = {
                "specialty": "Clinical Dietetics & Metabolic Health",
                "license_number": "RDN-882190",
            }
            self.create_user(
                username="clinician_demo",
                email="dr.chen@clinic.org",
                password="admin123",
                full_name="Dr. Sarah Chen, MD",
                role="clinician",
                initial_profile=default_clinician_profile,
            )

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "patient",
        initial_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new user with salted hashed password."""
        now = datetime.now(timezone.utc).isoformat()
        pwd_hash = hash_password(password)
        profile_json = json.dumps(initial_profile) if initial_profile else "{}"

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name, role, saved_profile_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username.strip(),
                    email.strip().lower(),
                    pwd_hash,
                    full_name,
                    role,
                    profile_json,
                    now,
                ),
            )
            conn.commit()
            user_id = cursor.lastrowid

        return self.get_user_by_id(user_id)  # type: ignore

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve user by database ID."""
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                return None
            return self._format_user_row(row)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by username (case-insensitive)."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username.strip(),)
            ).fetchone()
            if not row:
                return None
            return self._format_user_row(row)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by email address (case-insensitive)."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
            ).fetchone()
            if not row:
                return None
            return self._format_user_row(row)

    def authenticate_user(self, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by username or email and verify password."""
        user = self.get_user_by_username(username_or_email)
        if not user:
            user = self.get_user_by_email(username_or_email)
        if not user:
            return None

        # Fetch raw password hash for verification
        with self._connection() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?", (user["id"],)
            ).fetchone()
            if not row or not verify_password(password, row["password_hash"]):
                return None

            # Update last_login
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user["id"]))
            conn.commit()

        user["last_login"] = now
        return user

    def update_user_profile(
        self, user_id: int, profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update the saved profile JSON for a user."""
        profile_json = json.dumps(profile)
        with self._connection() as conn:
            conn.execute(
                "UPDATE users SET saved_profile_json = ? WHERE id = ?",
                (profile_json, user_id),
            )
            conn.commit()
        return self.get_user_by_id(user_id)

    def list_users(self) -> List[Dict[str, Any]]:
        """List all registered users (excluding password hashes)."""
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
            return [self._format_user_row(r) for r in rows]

    def _format_user_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        profile = {}
        if row["saved_profile_json"]:
            try:
                profile = json.loads(row["saved_profile_json"])
            except Exception:
                profile = {}

        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "full_name": row["full_name"],
            "role": row["role"],
            "saved_profile": profile,
            "created_at": row["created_at"],
            "last_login": row["last_login"],
        }


# Singleton instance
_user_db_instance: Optional[UserDB] = None


def get_user_db() -> UserDB:
    """Retrieve singleton UserDB instance."""
    global _user_db_instance
    if _user_db_instance is None:
        _user_db_instance = UserDB()
    return _user_db_instance
