from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.messages import TranscriptMessage

class TranscriptHandler(EventHandler[TranscriptMessage]):
    """Handler for transcript events."""
    
    event_type = "transcript"
    message_class = TranscriptMessage
