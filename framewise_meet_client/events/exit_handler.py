from typing import Dict, Any, Callable
from .base_handler import EventHandler
# Update import to use inbound module
from ..models.inbound import ExitMessage


class ExitHandler(EventHandler[ExitMessage]):
    """Handler for exit events."""

    event_type = "on_exit"
    message_class = ExitMessage
