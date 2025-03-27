from typing import Dict, Any, Callable
from .base_handler import EventHandler
# Update import to use inbound module
from ..models.inbound import ConnectionRejectedMessage


class ConnectionRejectedHandler(EventHandler[ConnectionRejectedMessage]):
    """Handler for connection rejection events."""

    event_type = "connection_rejected"
    message_class = ConnectionRejectedMessage
