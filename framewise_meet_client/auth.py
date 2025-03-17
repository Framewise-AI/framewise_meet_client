import logging
import requests
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

def authenticate_api_key(api_key: str) -> bool:
    """Authenticate an API key.
    
    This implementation validates the API key against a remote server.
    
    Args:
        api_key: The API key to authenticate
        
    Returns:
        True if authentication succeeded, False otherwise
    """
    if not api_key:
        logger.warning("Empty API key provided")
        return False
    
    logger.debug("Authenticating API key...")
    
    url = 'https://backend.framewise.ai/api/py/validate-api-key'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        'api_key': api_key
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get('is_valid', False)
    except requests.RequestException as e:
        logger.error(f"Error during API key authentication: {e}")
        return False