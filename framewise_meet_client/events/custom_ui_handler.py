from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.messages import CustomUIElementMessage

class CustomUIHandler(EventHandler[CustomUIElementMessage]):
    """Handler for custom UI element response events."""
    
    event_type = "custom_ui_element_response"
    message_class = CustomUIElementMessage
