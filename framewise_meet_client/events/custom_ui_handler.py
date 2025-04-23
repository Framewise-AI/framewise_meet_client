"""
Handler module for custom UI element events in Framewise Meet client.

This module defines the CustomUIHandler, which processes incoming UI element
response messages, converting them into strongly-typed CustomUIElementResponse
models and dispatching subtype events based on individual element types (e.g., MCQ,
notification, file upload).

Usage example:
    @app.on_custom_ui()
    def handle_ui_event(message: CustomUIElementResponse):
        subtype = handler.get_element_type(message.content)
        # handle based on subtype
"""
import logging
from typing import Dict, Any, Optional
from .base_handler import EventHandler
from ..models.inbound import CustomUIElementResponse
from ..error_handling import extract_message_content_safely

logger = logging.getLogger(__name__)

class CustomUIHandler(EventHandler[CustomUIElementResponse]):
    """
    Handler for custom UI element response events.

    Attributes:
        event_type: The event string 'custom_ui_element_response'.
        message_class: The Pydantic model class CustomUIElementResponse.

    Provides a method to extract the specific UI element subtype from the
    message content and allows applications to register handlers for each
    subtype (e.g., 'mcq_question', 'upload_file').
    """
    event_type = "custom_ui_element_response"
    message_class = CustomUIElementResponse

    def get_element_type(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Extract the UI element subtype from the raw message data.

        Args:
            data: Raw message dictionary or model content attribute.

        Returns:
            The subtype string (e.g., 'mcq_question') or None if not found.
        """
        try:
            return extract_message_content_safely(data, "type")
        except Exception as e:
            logger.error(f"Error extracting UI element type: {e}")
            return None

