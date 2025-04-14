import asyncio
import logging
from typing import Dict, Any, Callable, List, Optional, Union
import inspect
from pydantic import BaseModel
from .models.inbound import (
    BaseMessage, 
    TranscriptMessage, 
    JoinMessage, 
    ExitMessage, 
    CustomUIElementResponse,
    ConnectionRejectedMessage
)

logger = logging.getLogger(__name__)

# Dictionary mapping event types to their corresponding model classes
MESSAGE_TYPE_MAPPING = {
    "transcript": TranscriptMessage,
    "join": JoinMessage,
    "exit": ExitMessage,
    "custom_ui": CustomUIElementResponse,
    "custom_ui_element": CustomUIElementResponse,
    "connection_rejected": ConnectionRejectedMessage,
    # Add mappings for other event types as needed
}

class EventDispatcher:
    """Dispatches events to registered handlers."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def register(self, event_type: str, handler: Callable) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: Type of event to handle
            handler: Function to call when event is dispatched
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type}")

    def unregister(self, event_type: str, handler: Callable) -> bool:
        """Unregister a handler for a specific event type.

        Args:
            event_type: Type of event
            handler: Handler function to remove

        Returns:
            True if handler was found and removed, False otherwise
        """
        if event_type not in self._handlers:
            return False
        try:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unregistered handler for {event_type}")
            return True
        except ValueError:
            return False

    async def dispatch(self, event_type: str, message: Union[dict, BaseMessage]) -> None:
        """Dispatch an event to all registered handlers.

        Args:
            event_type: Type of event
            message: Event data (can be a dict or a properly parsed BaseMessage)
        """
        if event_type not in self._handlers:
            logger.debug(f"No handlers registered for {event_type}")
            return

        # Convert message to a proper model if it's a dict
        model_message = message
        if isinstance(message, dict):
            model_class = MESSAGE_TYPE_MAPPING.get(event_type)
            if model_class:
                try:
                    model_message = model_class(**message)
                    logger.debug(f"Converted dict to {model_class.__name__}")
                except Exception as e:
                    logger.error(f"Failed to convert dict to {model_class.__name__}: {str(e)}")
                    # Continue with the original dict if conversion fails
            else:
                logger.warning(f"No model class found for event type: {event_type}")

        handlers = self._handlers[event_type].copy()  # Copy to prevent modification during iteration
        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(model_message)
                else:
                    handler(model_message)
            except Exception as e:
                logger.error(f"Error in handler for {event_type}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
