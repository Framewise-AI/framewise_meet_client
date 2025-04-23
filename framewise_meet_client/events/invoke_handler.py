"""
Handler module for 'invoke' events in Framewise Meet client.

This module defines the InvokeHandler, which processes function invocation messages
(received when server requests a function call) by converting raw data
into strongly-typed InvokeMessage models. It integrates with the App's
event dispatcher so applications can register handlers for function calls.

Usage example:
    @app.on_invoke()
    def handle_invoke(message: InvokeMessage):
        function_name = message.content.function_name
        args = message.content.arguments
        # execute function or dispatch accordingly
"""

from typing import Dict, Any, Callable
from .base_handler import EventHandler
from ..models.inbound import InvokeMessage

class InvokeHandler(EventHandler[InvokeMessage]):
    """
    Handler for function invocation events ('invoke').

    Attributes:
        event_type: The event string 'invoke'.
        message_class: The Pydantic model class InvokeMessage.

    This handler converts raw invocation data into an InvokeMessage instance
    before invoking registered callbacks that implement the requested function logic.
    """
    event_type = "invoke"
    message_class = InvokeMessage
