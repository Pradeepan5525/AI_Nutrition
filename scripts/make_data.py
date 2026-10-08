"""Command line script to execute complete data preparation and harmonization."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nutri.config import FOODS_DB, FOODS_PARQUET
from nutri.data.harmonizer import run_harmonization_pipeline
from nutri.logging import setup_logger

logger = setup_logger("make_data")


def main() -> None:
    """Run data ingestion, harmonization, and persistence."""
    logger.info("Starting data pipeline execution...")
    df = run_harmonization_pipeline()
    logger.info("Successfully produced harmonized foods table: %d rows", len(df))
    logger.info("Parquet: %s (exists: %s)", FOODS_PARQUET, FOODS_PARQUET.exists())
    logger.info("SQLite:  %s (exists: %s)", FOODS_DB, FOODS_DB.exists())


if __name__ == "__main__":
    main()
