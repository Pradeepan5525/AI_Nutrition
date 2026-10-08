"""Command-line script to train, calibrate, evaluate, and persist obesity risk models."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nutri.logging import setup_logger
from nutri.models.train_risk import train_and_persist_risk_model

logger = setup_logger("train")


def main() -> None:
    """Execute model training pipeline."""
    logger.info("Executing obesity risk ML training pipeline...")
    metrics = train_and_persist_risk_model()
    logger.info("Training complete!")
    logger.info(
        "Synthetic Test Split Accuracy: %.2f%% | Macro-F1: %.4f",
        metrics["synthetic_test_evaluation"]["accuracy"] * 100,
        metrics["synthetic_test_evaluation"]["macro_f1"],
    )
    logger.info(
        "Likely Original Holdout Accuracy: %.2f%% | Macro-F1: %.4f",
        metrics["likely_original_holdout_evaluation"]["accuracy"] * 100,
        metrics["likely_original_holdout_evaluation"]["macro_f1"],
    )


if __name__ == "__main__":
    main()
