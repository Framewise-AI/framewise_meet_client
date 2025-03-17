from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.messages import JoinMessage

class JoinHandler(EventHandler[JoinMessage]):
    """Handler for join events."""
    
    event_type = "on_join"
    message_class = JoinMessage
