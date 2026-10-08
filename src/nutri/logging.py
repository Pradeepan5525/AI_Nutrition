"""Logging configuration for Nutrition Intelligence System."""

import logging
import sys


def setup_logger(name: str = "nutri", level: int = logging.INFO) -> logging.Logger:
    """Set up and return a structured logger.

    Args:
        name: Logger name.
        level: Logging level.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger
