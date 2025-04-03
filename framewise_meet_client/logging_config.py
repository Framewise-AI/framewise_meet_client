"""Logging configuration for the Framewise Meet client."""

import logging
import sys
from typing import Dict, Any, Optional

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def configure_logging(
    level: str = "INFO",
    format_str: str = DEFAULT_LOG_FORMAT,
    log_file: Optional[str] = None,
    log_to_console: bool = True
) -> None:
    """Configure logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Log format string
        log_file: Optional file path to write logs to
        log_to_console: Whether to log to console
    """
    # Convert level string to logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure root logger
    root_logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log the configuration
    logging.info(f"Logging configured with level={level}, file={log_file or 'None'}")
