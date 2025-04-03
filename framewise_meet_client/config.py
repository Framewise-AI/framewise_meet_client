"""Configuration management for Framewise Meet client."""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClientConfig:
    """Configuration for the Framewise Meet client."""
    
    host: str = "localhost"
    port: int = 8000
    log_level: str = "INFO"
    auto_reconnect: bool = True
    reconnect_delay: int = 5
    connection_timeout: int = 30
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ClientConfig':
        """Create a configuration instance from a dictionary."""
        return cls(
            host=config_dict.get("host", cls.host),
            port=config_dict.get("port", cls.port),
            log_level=config_dict.get("log_level", cls.log_level),
            auto_reconnect=config_dict.get("auto_reconnect", cls.auto_reconnect),
            reconnect_delay=config_dict.get("reconnect_delay", cls.reconnect_delay),
            connection_timeout=config_dict.get("connection_timeout", cls.connection_timeout)
        )
    
    @classmethod
    def from_json_file(cls, file_path: str) -> 'ClientConfig':
        """Load configuration from a JSON file."""
        try:
            with open(file_path, 'r') as config_file:
                config_dict = json.load(config_file)
                return cls.from_dict(config_dict)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {file_path}: {e}")
            return cls()
    
    @classmethod
    def from_env(cls) -> 'ClientConfig':
        """Load configuration from environment variables."""
        return cls(
            host=os.environ.get("FRAMEWISE_HOST", cls.host),
            port=int(os.environ.get("FRAMEWISE_PORT", cls.port)),
            log_level=os.environ.get("FRAMEWISE_LOG_LEVEL", cls.log_level),
            auto_reconnect=os.environ.get("FRAMEWISE_AUTO_RECONNECT", cls.auto_reconnect) in ("True", "true", "1"),
            reconnect_delay=int(os.environ.get("FRAMEWISE_RECONNECT_DELAY", cls.reconnect_delay)),
            connection_timeout=int(os.environ.get("FRAMEWISE_CONNECTION_TIMEOUT", cls.connection_timeout))
        )
