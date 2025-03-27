"""Factory functions for creating App instances with different configurations."""

import logging
from typing import Optional, Dict, Any

from .app import App
from .config import ClientConfig
from .logging_config import configure_logging

logger = logging.getLogger(__name__)

def create_app(api_key: Optional[str] = None, config: Optional[ClientConfig] = None, 
              **kwargs) -> App:
    """Create and configure an App instance.
    
    Args:
        api_key: API key for authentication
        config: Client configuration
        **kwargs: Additional configuration options that override values in config
        
    Returns:
        Configured App instance
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
    """Create app instance with configuration from environment variables."""
    config = ClientConfig.from_env()
    return create_app(
        api_key=os.environ.get("FRAMEWISE_API_KEY"),
        config=config
    )

def create_app_from_config_file(file_path: str, api_key: Optional[str] = None) -> App:
    """Create app instance with configuration from a JSON file."""
    config = ClientConfig.from_json_file(file_path)
    return create_app(api_key=api_key, config=config)
