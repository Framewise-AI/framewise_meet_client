"""
Event dispatching core for Framewise Meet client.

This module defines the EventDispatcher class, which manages the registration
and invocation of event handlers for different message types. Handlers can be
registered for specific event strings, and dispatched data is routed to
all matching handlers, including support for async handlers.

Key features:
- Registering handlers for event types
- Dispatching BaseMessage instances to handlers
- Synchronous and asynchronous handler support

Usage example:
    dispatcher = EventDispatcher()
    dispatcher.register('transcript', handle_transcript)
    await dispatcher.dispatch('transcript', TranscriptMessage(...))
"""

import asyncio
from typing import Any, Callable, Dict, List, Union
import logging
import traceback
from ..models.inbound import BaseMessage
from ..exceptions import InvalidMessageTypeError

logger = logging.getLogger(__name__)

class EventDispatcher:
    """Dispatches events to registered handlers."""
    
    def __init__(self):
        """Initialize the event dispatcher."""
        self._handlers: Dict[str, List[Callable[[BaseMessage], Any]]] = {}
    
    def register(self, event_type: str, handler: Callable[[BaseMessage], Any]) -> None:
        """Register a handler for an event type.
        
        Args:
            event_type: The event type to register the handler for
            handler: The handler function to register
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type {event_type}")
    
    async def dispatch(self, event_type: str, data: BaseMessage) -> None:
        """Dispatch an event to all registered handlers.
        
        Args:
            event_type: The event type to dispatch
            data: The message data to pass to the handlers
        """
        if not isinstance(data, BaseMessage):
            raise InvalidMessageTypeError(expected_type="BaseMessage", actual_type=type(data).__name__)
            
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            logger.debug(f"No handlers registered for event type {event_type}")
            return
            
        logger.debug(f"Dispatching event {event_type} to {len(handlers)} handlers")
        
        for handler in handlers:
            try:
                result = handler(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in handler for event {event_type}: {e}")
