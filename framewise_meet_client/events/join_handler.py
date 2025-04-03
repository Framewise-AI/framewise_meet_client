from typing import Dict, Any, Callable
from .base_handler import EventHandler
# Update import to use inbound module
from ..models.inbound import JoinMessage


class JoinHandler(EventHandler[JoinMessage]):
    """Handler for join events."""

    event_type = "on_join"
    message_class = JoinMessage
