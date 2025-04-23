"""
Factory functions for creating and configuring App instances.

This module provides helper functions to construct App objects using
various sources of configuration: explicit parameters, environment
variables, or JSON configuration files.

Usage:
    from framewise_meet_client.app_factory import create_app, create_app_from_env

    # Create with explicit parameters
    app = create_app(api_key="your_key", host="backend.framewise.ai", port=443)

    # Create using environment variables
    app = create_app_from_env()
"""

import logging
from typing import Optional, Dict, Any
import os

from .app import App
from .config import ClientConfig
from .logging_config import configure_logging

logger = logging.getLogger(__name__)

def create_app(api_key: Optional[str] = None, config: Optional[ClientConfig] = None, 
              **kwargs) -> App:
    """
    Create and configure an App instance.

    Args:
        api_key: API key for authentication with Framewise backend.
        config: Optional ClientConfig object containing host, port, etc.
        **kwargs: Additional configuration overrides for the ClientConfig fields.

    Returns:
        An initialized App object with logging, connection, and event settings applied.
    """
    # Create default config if none provided
    if config is None:
        config = ClientConfig()
    
    # Override config with any provided kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    # Configure logging first
    configure_logging(level=config.log_level)
    
    # Create the app
    app = App(api_key=api_key, host=config.host, port=config.port)
    
    # Configure additional app settings
    app.auto_reconnect = config.auto_reconnect
    app.reconnect_delay = config.reconnect_delay
    
    logger.info(f"Created app with host={config.host}, port={config.port}")
    return app

def create_app_from_env() -> App:
    """
    Create an App instance using configuration from environment variables.

    Environment variables:
        FRAMEWISE_API_KEY: API key
        FRAMEWISE_HOST: Hostname
        FRAMEWISE_PORT: Port number
        FRAMEWISE_LOG_LEVEL: Logging level
        FRAMEWISE_AUTO_RECONNECT: Auto-reconnect flag
        FRAMEWISE_RECONNECT_DELAY: Delay between reconnects
        FRAMEWISE_CONNECTION_TIMEOUT: Connection timeout

    Returns:
        An initialized App instance.
    """
    config = ClientConfig.from_env()
    return create_app(
        api_key=os.environ.get("FRAMEWISE_API_KEY"),
        config=config
    )

def create_app_from_config_file(file_path: str, api_key: Optional[str] = None) -> App:
    """
    Create an App instance using configuration loaded from a JSON file.

    Args:
        file_path: Path to the JSON file containing ClientConfig settings.
        api_key: Optional API key to override any file-based setting.

    Returns:
        An initialized App instance with settings from the file and provided api_key.
    """
    config = ClientConfig.from_json_file(file_path)
    return create_app(api_key=api_key, config=config)
