from typing import Any, Callable, Dict, Generic, TypeVar, Union, Optional, Type
from ..models.inbound import BaseMessage
import logging
from ..exceptions import InvalidMessageTypeError

logger = logging.getLogger(__name__)

# TypeVar for the message type
T = TypeVar("T", bound=BaseMessage)

class EventHandler(Generic[T]):
    """Base class for all event handlers."""
    
    event_type: str = None
    message_class = None
    
    def __init__(self):
        """Initialize the event handler."""
        if self.event_type is None:
            raise ValueError(f"Event type not specified for {self.__class__.__name__}")
        
    def register(self, handler_func: Callable[[T], Any]) -> Callable[[T], Any]:
        """Register a handler function with this event type.
        
        Args:
            handler_func: Function that takes a strongly-typed message object
        
        Returns:
            Wrapped function that handles strongly-typed message objects
        """
        def wrapped_handler(data: T) -> Any:
            # Verify the data is of the expected type
            if not isinstance(data, self.message_class):
                raise InvalidMessageTypeError(f"Expected {self.message_class.__name__}, got {type(data).__name__}")
            
            # Call the handler with the typed data
            return handler_func(data)
        
        return wrapped_handler


def register_event_handler(app, event_type: str, handler_func: Callable):
    """Register a handler function for the given event type.

    Args:
        app: App instance
        event_type: Event type string
        handler_func: Function to handle the event

    Returns:
        The original handler function for chaining
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
