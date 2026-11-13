"""Structured application logging setup."""
import logging
import sys
from backend.app.config.settings import settings


def setup_logging() -> logging.Logger:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )

    logger = logging.getLogger("crashsense.backend")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()

