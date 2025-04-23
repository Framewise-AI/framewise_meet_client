"""
Base event handler framework for the Framewise Meet client.

This module defines the generic EventHandler class and a helper function
for registering event handlers on the App's event dispatcher. It ensures
that handlers receive strongly-typed message objects.

Functions:
    register_event_handler: Register a handler function based on event type.
"""

from typing import Any, Callable, Dict, Generic, TypeVar, Union, Optional, Type
from ..models.inbound import BaseMessage
import logging
from ..exceptions import InvalidMessageTypeError

logger = logging.getLogger(__name__)

# TypeVar for the message type
T = TypeVar("T", bound=BaseMessage)

class EventHandler(Generic[T]):
    """
    Generic base class for all event handlers.
    
    Provides a type-safe wrapper around handler functions for a specific
    Pydantic message class and event type.
    
    Attributes:
        event_type: The string identifier for the event this handler handles.
        message_class: The Pydantic model class to validate incoming messages.
    """
    
    event_type: str = None
    message_class = None
    
    def __init__(self):
        """Initialize the event handler."""
        if self.event_type is None:
            raise ValueError(f"Event type not specified for {self.__class__.__name__}")
        
    def register(self, handler_func: Callable[[T], Any]) -> Callable[[T], Any]:
        """
        Wrap and register a handler function for this event type.
        
        Args:
            handler_func: Function that accepts a Pydantic message instance of type T.
        
        Returns:
            The wrapped handler function, which performs type checking before calling.
        """
        def wrapped_handler(data: T) -> Any:
            # Verify the data is of the expected type
            if not isinstance(data, self.message_class):
                raise InvalidMessageTypeError(f"Expected {self.message_class.__name__}, got {type(data).__name__}")
            
            # Call the handler with the typed data
            return handler_func(data)
        
        return wrapped_handler


def register_event_handler(app, event_type: str, handler_func: Callable):
    """
    Register a handler function for the given event type on the App instance.

    This helper chooses a specific EventHandler subclass if available,
    otherwise falls back to generic registration.
    
    Args:
        app: The App instance whose dispatcher will be used.
        event_type: String identifier of the event (e.g., 'transcript').
        handler_func: The function to be called when the event occurs.

    Returns:
        The original handler function for chaining decorators.
    """
    from . import EVENT_HANDLERS

    if event_type not in EVENT_HANDLERS:
        logger.warning(
            f"Unknown event type: {event_type}. Falling back to generic registration."
        )
        # Fall back to generic registration
        return app.event_dispatcher.register_handler(event_type)(handler_func)

    handler_class = EVENT_HANDLERS[event_type]
    handler = handler_class(app.event_dispatcher)
    logger.debug(f"Using {handler_class.__name__} for event type '{event_type}'")
    return handler.register(handler_func)
