"""
Handler for connection rejection events in Framewise Meet client.

This module defines the ConnectionRejectedHandler, which processes messages
indicating that the server has rejected the client's connection attempt.
It wraps raw data into a ConnectionRejectedMessage model and dispatches events
for custom handling of authentication failures.

Usage example:
    @app.on_connection_rejected()
    def handle_rejection(message: ConnectionRejectedMessage):
        print(f"Connection rejected: {message.content.reason}")
"""

from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.inbound import ConnectionRejectedMessage

class ConnectionRejectedHandler(EventHandler[ConnectionRejectedMessage]):
    """
    Handler for processing connection rejection events.
    
    Attributes:
        event_type: The event string 'connection_rejected'.
        message_class: The Pydantic model class ConnectionRejectedMessage.
    
    When the server rejects a connection (e.g., invalid API key),
    this handler ensures the raw data is converted to a ConnectionRejectedMessage
    before invoking registered callbacks.
    """
    event_type = "connection_rejected"
    message_class = ConnectionRejectedMessage
