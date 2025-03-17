import asyncio
import logging
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)

class EventDispatcher:
    """Manages event handlers and dispatches events."""
    
    def __init__(self):
        """Initialize the event dispatcher."""
        self.handlers = {}
    
    def register_handler(self, event_type: str):
        """Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
        
        Returns:
            Decorator function
        """
        def decorator(func):
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(func)
            logger.debug(f"Registered handler {func.__name__} for {event_type} events")
            return func
        return decorator
    
    async def dispatch(self, event_type: str, data: Dict[str, Any]) -> None:
        """Dispatch an event to all registered handlers.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type not in self.handlers:
            logger.debug(f"No handlers registered for event type: {event_type}")
            return
        
        handler_count = len(self.handlers[event_type])
        logger.debug(f"Dispatching {event_type} event to {handler_count} handler(s)")
        
        for handler in self.handlers[event_type]:
            try:
                logger.debug(f"Calling handler {handler.__name__} for {event_type} event")
                result = handler(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in {event_type} handler {handler.__name__}: {str(e)}", exc_info=True)
