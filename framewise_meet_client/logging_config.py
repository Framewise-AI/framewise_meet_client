"""
Logging configuration utility for the Framewise Meet client.

This module provides a helper function to standardize logging setup across
applications built with the Framewise Meet Client. It supports console and
file output, custom log levels, and flexible formatting.

Usage example:
    from framewise_meet_client.logging_config import configure_logging
    configure_logging(level="DEBUG", log_file="app.log")
"""

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
    """
    Configure the root logger for the application.

    This function resets any existing handlers on the root logger and applies
    new handlers based on the provided parameters. It supports logging to
    stdout and optionally to a file with the same format.

    Args:
        level: Log level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_str: Format string for log messages.
        log_file: Optional file path to write logs to. If None, file logging is disabled.
        log_to_console: Whether to add a console (stdout) handler.

    Raises:
        ValueError: If the provided log level string is invalid.
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
