"""
Deprecated event handler module for Framewise Meet client.

This module provides an older EventDispatcher class for backward compatibility.
It is recommended to use the `events.dispatcher.EventDispatcher` instead,
which offers a more robust implementation and type-safe event handling.

The legacy EventDispatcher supports:
- Registering handlers for string event types
- Dispatching messages (dict or BaseMessage) to handlers
- Async and sync handler support

Usage:
    from framewise_meet_client.event_handler import EventDispatcher
    dispatcher = EventDispatcher()
    dispatcher.register('transcript', handler_func)
    await dispatcher.dispatch('transcript', message)
"""

import asyncio
from typing import Any, Callable, Dict, List, Union
import logging
from .models.inbound import BaseMessage
from .exceptions import InvalidMessageTypeError

logger = logging.getLogger(__name__)

class EventDispatcher:
    """
    Dispatches events to registered handlers based on event type.
    
    The EventDispatcher is a central component of the Framewise Meet Client's event-driven
    architecture. It maintains a registry of event handlers organized by event type and
    handles the process of dispatching events to the appropriate handlers when events
    are triggered.
    
    Key features:
    - Multiple handlers can be registered for the same event type
    - Supports both synchronous and asynchronous handlers
    - Provides error handling and isolation between handlers
    - Logs detailed debug information during event dispatching
    
    This class is typically used internally by the App class, which provides a
    more user-friendly decorator-based interface for event registration.
    """
    
    def __init__(self):
        """
        Initialize the event dispatcher with an empty handler registry.
        
        The handler registry is a dictionary mapping event types (strings) to
        lists of handler functions.
        """
        self._handlers: Dict[str, List[Callable[[BaseMessage], Any]]] = {}
    
    def register(self, event_type: str, handler: Callable[[BaseMessage], Any]) -> None:
        """
        Register a handler function for a specific event type.
        
        This method adds a handler function to the registry for the specified event type.
        If this is the first handler for this event type, a new list is created.
        
        Args:
            event_type: The event type identifier string to register the handler for.
                       Common event types include "transcript", "join", "exit", etc.
            handler: The handler function to call when events of this type are dispatched.
                    The handler should accept a single argument of type BaseMessage or
                    a subclass appropriate for the event type.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type {event_type}")
    
    # Alias for backward compatibility
    register_handler = register
    
    async def dispatch(self, event_type: str, data: Any) -> None:
        """
        Dispatch an event to all registered handlers for the specified event type.
        
        This method:
        1. Finds all registered handlers for the event type
        2. Calls each handler with the provided data
        3. Awaits any handlers that return coroutines
        4. Catches and logs any exceptions that occur in handlers
        
        The handlers are executed sequentially, but asynchronously when needed,
        which means that long-running handlers won't block the event loop.
        
        Args:
            event_type: The event type identifier string to dispatch.
            data: The message data to pass to the handlers, typically a BaseMessage
                 subclass instance containing the event details.
                 
        Note:
            Handlers are isolated from each other through exception handling, so an
            error in one handler won't prevent other handlers from executing.
        """
        # We need to check if data is a subclass of BaseMessage, not strictly BaseMessage
        from .models.inbound import BaseMessage
        if not isinstance(data, BaseMessage) and not isinstance(data, dict):
            logger.error(f"Cannot dispatch event: expected a BaseMessage subclass or dict, got {type(data).__name__}")
            return
            
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            logger.debug(f"No handlers registered for event type {event_type}")
            return
            
        logger.debug(f"Dispatching event {event_type} to {len(handlers)} handlers")
        
        for handler in handlers:
            try:
                result = handler(data)
                if asyncio.iscoroutine(result):
                    try:
                        await result
                    except Exception as e:
                        logger.error(f"Error in async handler for event {event_type}: {e}")
                        logger.error(traceback.format_exc())
            
            except Exception as e:
                logger.error(f"Error in handler for event {event_type}: {e}")
                import traceback
                logger.error(traceback.format_exc())
