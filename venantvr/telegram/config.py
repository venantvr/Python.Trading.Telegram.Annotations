"""Configuration centralisée pour le module telegram."""

import logging
import os
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """Configure le système de logging pour l'application.
    
    Args:
        level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Réduire le bruit des bibliothèques tierces
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


class Config:
    """Configuration de l'application."""
    
    # Timeouts
    API_TIMEOUT: int = 35
    SEND_TIMEOUT: int = 10
    POLL_TIMEOUT: int = 30
    
    # Retry settings
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 0.3
    
    # Queue settings
    MAX_QUEUE_SIZE: int = 1000
    
    # Validation
    MAX_MESSAGE_LENGTH: int = 4096
    MAX_CALLBACK_DATA_LENGTH: int = 64