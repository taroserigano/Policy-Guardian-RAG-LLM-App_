"""
Logging configuration for the application.
Provides structured logging with safe redaction of sensitive data.
"""
import logging
import sys
from typing import Any


class SafeFormatter(logging.Formatter):
    """
    Custom formatter that redacts sensitive information.
    Never log full document text, API keys, or user passwords.
    """
    
    SENSITIVE_KEYS = ["api_key", "password", "token", "secret", "authorization"]
    
    def format(self, record: logging.LogRecord) -> str:
        # Redact sensitive data from extra fields
        if hasattr(record, "extra"):
            for key in self.SENSITIVE_KEYS:
                if key in record.extra:
                    record.extra[key] = "***REDACTED***"
        
        return super().format(record)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure application logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = SafeFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Usually __name__ of the calling module
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
