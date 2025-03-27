from typing import Dict, Any, Optional
import logging
from .base_handler import EventHandler
from ..models.outbound import CustomUIElementMessage as CustomUIElementResponse
from ..error_handling import extract_message_content_safely

logger = logging.getLogger(__name__)

class CustomUIHandler(EventHandler[CustomUIElementResponse]):
    """Handler for custom UI events."""

    event_type = "custom_ui_element_response"
    message_class = CustomUIElementResponse

    def get_element_type(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract the UI element type from the data if available."""
        try:
            # Use the safe extraction utility
            return extract_message_content_safely(data, "type")
        except Exception as e:
            logger.error(f"Error extracting UI element type: {e}")
            return None

# Move function to error_handling.py or a separate validation module
def extract_element_type(data):
    """
    Extract the UI element type from the custom UI element data.
    
    Args:
        data: The data containing the custom UI element information.
        
    Returns:
        The element type string or None if it can't be determined.
    """
    # Add validation checks that raise ValueError
    if data is None:
        raise ValueError("Data cannot be None")
    
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    if not data:
        raise ValueError("Data dictionary cannot be empty")
        
    if "content" not in data:
        raise ValueError("Missing 'content' field in data")
        
    content = data.get("content")
    
    if not isinstance(content, dict):
        return None
        
    return content.get("type")