import logging
import sys
from typing import Optional

def configure_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Configure logging for the application.
    
    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
    """
    # Get the numeric level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    # Create handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Set more restrictive levels for some verbose libraries
    logging.getLogger('websockets').setLevel(max(numeric_level, logging.INFO))
    logging.getLogger('asyncio').setLevel(max(numeric_level, logging.INFO))
    
    logging.info(f"Logging configured with level {level}")
    
    return logging.getLogger()
