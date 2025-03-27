from typing import Dict, Any, Callable
from .base_handler import EventHandler
# Update import to use inbound module
from ..models.inbound import TranscriptMessage


class TranscriptHandler(EventHandler[TranscriptMessage]):
    """Handler for transcript events."""

    event_type = "transcript"
    message_class = TranscriptMessage
