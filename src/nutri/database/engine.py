"""SQLAlchemy engine and session management supporting SQLite and PostgreSQL."""

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from nutri.config import DATA_PROCESSED_DIR

# Load environment variables
load_dotenv()

DEFAULT_SECRET = "clinical-ai-nutrition-super-secret-key-production-grade-2026"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", DEFAULT_SECRET)

if ENVIRONMENT == "production" and (not SECRET_KEY or SECRET_KEY == DEFAULT_SECRET or len(SECRET_KEY) < 32):
    raise RuntimeError(
        "FATAL: Application cannot start in production mode with default or weak JWT_SECRET_KEY. "
        "Please provide a secure 32+ character key in environment variables."
    )

# Fallback SQLite location
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite:///{DATA_PROCESSED_DIR / 'nutrition_app.db'}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

# Configure engine arguments
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """FastAPI dependency yielding a managed database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
