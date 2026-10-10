"""Create development demo account reading credentials strictly from environment variables.

Usage:
    export DEMO_USER_EMAIL="patient@example.com"
    export DEMO_USER_PASSWORD="YourSecurePassword123!"
    export DEMO_USER_NAME="Alex Carter"
    python scripts/create_demo_user.py
"""

import os
import sys
from dotenv import load_dotenv

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from nutri.auth.user_service import get_user_by_email_or_username, register_user_full
from nutri.database.engine import SessionLocal, init_db
from nutri.database.models import User


def main() -> None:
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production":
        print("ERROR: Demo user creation is forbidden in production environment.")
        sys.exit(1)

    email = os.getenv("DEMO_USER_EMAIL")
    password = os.getenv("DEMO_USER_PASSWORD")
    name = os.getenv("DEMO_USER_NAME", "Demo Patient")

    if not email or not password:
        print("ERROR: DEMO_USER_EMAIL and DEMO_USER_PASSWORD environment variables must be set.")
        print("Example:")
        print("  $env:DEMO_USER_EMAIL = 'patient@example.com'")
        print("  $env:DEMO_USER_PASSWORD = 'DemoPassword123!'")
        sys.exit(1)

    init_db()
    db = SessionLocal()
    try:
        existing = get_user_by_email_or_username(db, email)
        if existing:
            print(f"User with email '{email}' already exists (ID: {existing.id}).")
            return

        initial_profile = {
            "age": 32,
            "gender": "male",
            "weight_kg": 76.5,
            "height_cm": 178.0,
            "activity_level": "moderate",
            "goal": "lose_weight",
            "is_asian": False,
            "conditions": ["hypertension"],
            "allergens": ["peanuts"],
            "dietary_restrictions": ["low_sodium"],
            "preferred_cuisine": "Mediterranean",
            "onboarding_completed": True,
        }

        user, err = register_user_full(
            db=db,
            email=email,
            password=password,
            full_name=name,
            role="patient",
            initial_profile=initial_profile,
        )

        if err:
            print(f"ERROR creating demo user: {err}")
            sys.exit(1)

        print(f"Successfully created demo user '{user.email}' (ID: {user.id}) with clinical profile.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
