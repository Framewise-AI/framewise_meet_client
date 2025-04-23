"""
Handler for participant exit events in Framewise Meet client.

This module defines the ExitHandler, which wraps incoming exit messages
into strongly-typed ExitMessage models. It integrates with the App's
event dispatcher to allow applications to register handlers for when
participants leave a meeting.

Usage example:
    @app.on_exit()
    def handle_user_exit(message: ExitMessage):
        print(f"User exited: {message.content.participant_name}")
"""

from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.inbound import ExitMessage

class ExitHandler(EventHandler[ExitMessage]):
    """
    Handler for meeting exit events.
    
    Attributes:
        event_type: The event string 'on_exit'.
        message_class: The Pydantic model class ExitMessage.
    
    When a participant exits, this handler ensures the raw data is converted
    to an ExitMessage instance before invoking registered callbacks.
    """
    event_type = "on_exit"
    message_class = ExitMessage
