from typing import Dict, Any, Callable
from .base_handler import EventHandler
# Update import to use inbound module
from ..models.inbound import InvokeMessage


class InvokeHandler(EventHandler[InvokeMessage]):
    """Handler for invoke events."""

    event_type = "invoke"
    message_class = InvokeMessage
