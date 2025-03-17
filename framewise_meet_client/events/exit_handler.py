from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.messages import ExitMessage

class ExitHandler(EventHandler[ExitMessage]):
    """Handler for exit events."""
    
    event_type = "on_exit"
    message_class = ExitMessage
