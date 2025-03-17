from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.messages import ConnectionRejectedMessage

class ConnectionRejectedHandler(EventHandler[ConnectionRejectedMessage]):
    """Handler for connection rejected events."""
    
    event_type = "connection_rejected"
    message_class = ConnectionRejectedMessage
