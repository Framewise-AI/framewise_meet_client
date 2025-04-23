"""
Configuration management for the Framewise Meet client.

This module provides the ClientConfig dataclass for managing connection and
runtime settings, including host, port, logging level, and reconnection policies.
It supports loading configuration from dictionaries, JSON files, and environment variables.

Usage example:
    # Load from JSON file
    config = ClientConfig.from_json_file('/path/to/config.json')

    # Override defaults via environment
    os.environ['FRAMEWISE_HOST'] = 'backend.framewise.ai'
    config = ClientConfig.from_env()

    # Use config for App creation
    app = create_app(api_key, config=config)
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClientConfig:
    """
    Configuration for the Framewise Meet client application.
    
    Attributes:
        host: Server hostname or IP address where the backend is running.
        port: Server port number (e.g., 8000 or 443).
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        auto_reconnect: Whether to automatically reconnect on disconnect.
        reconnect_delay: Number of seconds to wait before attempting reconnection.
        connection_timeout: Timeout in seconds for initial connection attempts.
    """
    host: str = "localhost"
    port: int = 8000
    log_level: str = "INFO"
    auto_reconnect: bool = True
    reconnect_delay: int = 5
    connection_timeout: int = 30
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ClientConfig':
        """
        Create a configuration instance from a dictionary of values.
        
        Args:
            config_dict: Dictionary containing configuration parameters.
                         Supported keys: host, port, log_level, auto_reconnect,
                         reconnect_delay, connection_timeout.
        Returns:
            ClientConfig: New instance populated from the dictionary.
        """
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
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the JSON configuration file.
        Returns:
            ClientConfig: New instance populated from file.
                         Returns defaults if file is missing or invalid.
        """
        try:
            with open(file_path, 'r') as config_file:
                config_dict = json.load(config_file)
                return cls.from_dict(config_dict)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {file_path}: {e}")
            return cls()
    
    @classmethod
    def from_env(cls) -> 'ClientConfig':
        """
        Load configuration from environment variables.
        
        Reads variables:
          - FRAMEWISE_HOST
          - FRAMEWISE_PORT
          - FRAMEWISE_LOG_LEVEL
          - FRAMEWISE_AUTO_RECONNECT
          - FRAMEWISE_RECONNECT_DELAY
          - FRAMEWISE_CONNECTION_TIMEOUT
        
        Returns:
            ClientConfig: New instance populated from environment, falling back to defaults.
        """
        return cls(
            host=os.environ.get("FRAMEWISE_HOST", cls.host),
            port=int(os.environ.get("FRAMEWISE_PORT", cls.port)),
            log_level=os.environ.get("FRAMEWISE_LOG_LEVEL", cls.log_level),
            auto_reconnect=os.environ.get("FRAMEWISE_AUTO_RECONNECT", str(cls.auto_reconnect)) in ("True", "true", "1"),
            reconnect_delay=int(os.environ.get("FRAMEWISE_RECONNECT_DELAY", cls.reconnect_delay)),
            connection_timeout=int(os.environ.get("FRAMEWISE_CONNECTION_TIMEOUT", cls.connection_timeout))
        )
