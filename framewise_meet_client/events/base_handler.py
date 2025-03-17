import logging
from typing import Dict, Any, Callable, TypeVar, Generic, Type, Union

from ..models.messages import BaseMessage
from pydantic import ValidationError

T = TypeVar('T', bound=BaseMessage)

logger = logging.getLogger(__name__)

class EventHandler(Generic[T]):
    """Base class for event handlers."""
    
    event_type: str = ""
    message_class: Type[BaseMessage] = None
    
    def __init__(self, dispatcher):
        """Initialize the event handler.
        
        Args:
            dispatcher: Event dispatcher instance
        """
        self.dispatcher = dispatcher
    
    def register(self, handler_func: Callable[[T], Any]) -> Callable[[Union[Dict[str, Any], T]], Any]:
        """Register a handler function for this event type.
        
        Args:
            handler_func: Function that takes a strongly-typed message object
            
        Returns:
            The original handler function for chaining
        """
        def wrapper(data):
            # Always convert data to proper message class
            if isinstance(data, dict) and self.message_class is not None:
                try:
                    converted = self.message_class.model_validate(data)
                    return handler_func(converted)
                except Exception as e:
                    logger.error(f"Failed to convert dict to {self.message_class.__name__}: {e}")
                    # Try to create an empty instance as fallback with minimal data
                    try:
                        if "type" in data:
                            minimal_data = {"type": data["type"], "content": {}}
                            if "content" in data and isinstance(data["content"], dict):
                                minimal_data["content"] = data["content"]
                            converted = self.message_class.model_validate(minimal_data)
                            logger.warning(f"Created minimal {self.message_class.__name__} instance")
                            return handler_func(converted)
                    except Exception as inner_e:
                        logger.error(f"Could not create minimal instance: {inner_e}")
                        raise ValueError(f"Cannot handle event: failed to convert to {self.message_class.__name__}")
            elif isinstance(data, self.message_class):
                # Already the correct type
                return handler_func(data)
            else:
                # Unknown data type
                logger.error(f"Unexpected data type for {self.event_type}: {type(data)}")
                raise TypeError(f"Expected {self.message_class.__name__}, got {type(data)}")
        
        logger.info(f"Registered handler for {self.event_type} events using {self.message_class.__name__}")
        self.dispatcher.register_handler(self.event_type)(wrapper)
        return handler_func


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
        logger.warning(f"Unknown event type: {event_type}. Falling back to generic registration.")
        # Fall back to generic registration
        return app.event_dispatcher.register_handler(event_type)(handler_func)
    
    handler_class = EVENT_HANDLERS[event_type]
    handler = handler_class(app.event_dispatcher)
    logger.debug(f"Using {handler_class.__name__} for event type '{event_type}'")
    return handler.register(handler_func)
