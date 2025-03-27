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

