from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.messages import TranscriptMessage

class InvokeHandler(EventHandler[TranscriptMessage]):
    """Handler for invoke events (triggered by final transcripts)."""
    
    event_type = "invoke"
    message_class = TranscriptMessage
