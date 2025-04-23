"""
Handler for participant join events in Framewise Meet client.

This module defines the JoinHandler, which wraps incoming join messages
into strongly-typed JoinMessage models. It integrates with the App's
event dispatcher to allow applications to register handlers for when
participants join a meeting.

Usage example:
    @app.on_join()
    def handle_user_join(message: JoinMessage):
        print(f"User joined: {message.content.participant_name}")
"""

from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.inbound import JoinMessage

class JoinHandler(EventHandler[JoinMessage]):
    """
    Handler for meeting join events.
    
    Attributes:
        event_type: The event string 'on_join'.
        message_class: The Pydantic model class JoinMessage.
    
    When a participant joins, this handler ensures the raw data is converted
    to a JoinMessage instance before invoking registered callbacks.
    """
    event_type = "on_join"
    message_class = JoinMessage
