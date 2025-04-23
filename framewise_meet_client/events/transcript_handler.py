"""
Handler for speech transcript events in Framewise Meet client.

This module defines the TranscriptHandler, which processes incoming speech-to-text
messages, converting them into strongly-typed TranscriptMessage models. It integrates
with the App's event dispatcher to allow applications to register handlers for
real-time and final transcript updates.

Usage example:
    @app.on_transcript()
    def handle_transcript(message: TranscriptMessage):
        print(f"Transcript: {message.content.text}")
"""

from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.inbound import TranscriptMessage

class TranscriptHandler(EventHandler[TranscriptMessage]):
    """
    Handler for speech transcript messages.
    
    Attributes:
        event_type: The event string 'transcript'.
        message_class: The Pydantic model class TranscriptMessage.
    
    This handler converts raw transcript data into a TranscriptMessage instance,
    including interim and final transcript segments, before invoking registered callbacks.
    """
    event_type = "transcript"
    message_class = TranscriptMessage
