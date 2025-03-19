import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Type, TypeVar, cast, Union
from enum import Enum

from .connection import WebSocketConnection
from .event_handler import EventDispatcher
from .errors import AppNotRunningError, ConnectionError, AuthenticationError
from .messaging import MessageSender
from .models.messages import (
    JoinMessage, ExitMessage, TranscriptMessage, 
    CustomUIElementMessage, MCQSelectionMessage,
    ConnectionRejectedMessage,
    MessagePayload, BaseMessage
)
import datetime
from .events import (
    TRANSCRIPT_EVENT, JOIN_EVENT, EXIT_EVENT, 
    CUSTOM_UI_EVENT, INVOKE_EVENT,
    CONNECTION_REJECTED_EVENT,
    register_event_handler
)

import requests
from .auth import authenticate_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EventType(Enum):
    TRANSCRIPT = TRANSCRIPT_EVENT
    JOIN = JOIN_EVENT
    EXIT = EXIT_EVENT
    CUSTOM_UI_RESPONSE = CUSTOM_UI_EVENT
    INVOKE = INVOKE_EVENT
    CONNECTION_REJECTED = CONNECTION_REJECTED_EVENT
    
T = TypeVar('T', bound=BaseMessage)

class App:
    """WebSocket client app with decorator-based event handlers."""
    
    _event_aliases = {
        "join": JOIN_EVENT,
        "exit": EXIT_EVENT,
        "transcript": TRANSCRIPT_EVENT,
        "custom_ui_response": CUSTOM_UI_EVENT,
        "custom_ui": CUSTOM_UI_EVENT,
        "invoke": INVOKE_EVENT,
        "connection_rejected": CONNECTION_REJECTED_EVENT
    }

    _message_type_mapping = {
        JOIN_EVENT: JoinMessage,
        EXIT_EVENT: ExitMessage,
        TRANSCRIPT_EVENT: TranscriptMessage,
        CUSTOM_UI_EVENT: CustomUIElementMessage,
        INVOKE_EVENT: TranscriptMessage,
        CONNECTION_REJECTED_EVENT: ConnectionRejectedMessage
    }
    
    def __init__(self, api_key: Optional[str] = None, host: str = "localhost", port: int = 8000):
        """Initialize the app with connection details.
        
        Args:
            meeting_id: ID of the meeting to join
            api_key: Optional API key for authentication
            host: Server hostname
            port: Server port
        """
        self.meeting_id = None
        self.host = host
        self.port = port
        self.api_key = api_key
        self.auth_status = None
        self.connection = None
        self.event_dispatcher = EventDispatcher()
        self.message_sender = None
        self.running = False
        self.loop = None
        self._main_task = None


    def join_meeting(self,meeting_id):
        self.meeting_id = meeting_id
        self.connection = WebSocketConnection(self.host, self.port, meeting_id, self.api_key)
        self.message_sender = MessageSender(self.connection)

        for name in dir(self.message_sender):
            if not name.startswith('_') and callable(getattr(self.message_sender, name)):
                logging.info("set {name} in {message_sender}")
                setattr(self, name, getattr(self.message_sender, name))
        
    
    def on(self, event_type: str):
        """Decorator to register an event handler for a specific message type.
        
        Resolves event aliases to standard event types.
        
        Args:
            event_type: Type of event to handle (e.g., "transcript", "join")
                        Or a UI element type (e.g., "mcq_question", "info_card")
        
        Returns:
            Decorator function
        """

        resolved_event_type = self._event_aliases.get(event_type, event_type)
        
        if resolved_event_type != event_type:
            logger.debug(f"Resolved event alias '{event_type}' to standard event type '{resolved_event_type}'")
        
        def decorator(func):
            if event_type not in self._event_aliases:
                logger.debug(f"Registering direct handler for UI element type: {event_type}")
                def wrapper(data):
                    if "parsed_message" in data:
                        return func(data["parsed_message"])
                    else:
                        return func(data)
                
                self.event_dispatcher.register_handler(event_type)(wrapper)
                return func
            
            logger.debug(f"Registering handler for event type '{resolved_event_type}': {func.__name__}")
            return register_event_handler(self, resolved_event_type, func)
        
        return decorator

    def __getattr__(self, name):
        """Dynamically create event handler methods.
        
        This allows methods like on_transcript, on_join, etc. to be generated dynamically.
        """
        if name.startswith('on_'):
            event_name = name[3:]
            
            if event_name in self._event_aliases:
                event_type_value = self._event_aliases[event_name]
                
                def handler_method(func=None):
                    return self._on_event(event_type_value, func, name)
                return handler_method
                
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def _on_event(self, event_type: Union[str, EventType], func: Callable[[BaseMessage], Any] = None, shorthand_name: str = None):
        """Helper function to reduce code duplication in event registration."""
        event_type_value = event_type.value if isinstance(event_type, EventType) else event_type
        if func is None:
            return self.on(event_type_value)
        logger.debug(f"Using {shorthand_name} shorthand for {func.__name__}")
        return self.on(event_type_value)(func)
    
    def invoke(self, func: Callable[[TranscriptMessage], Any] = None):
        """Alias for on_invoke for convenience.
        
        Args:
            func: Function that takes a TranscriptMessage and processes the event
        """
        return self.on_invoke(func)
    
    def run(self, auto_reconnect: bool = True, reconnect_delay: int = 5, log_level: str = None) -> None:
        """Run the application (blocking).
        
        Args:
            auto_reconnect: Whether to automatically reconnect on disconnect
            reconnect_delay: Delay between reconnection attempts in seconds
            log_level: Optional log level to set (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if log_level:
            numeric_level = getattr(logging, log_level.upper(), None)
            if isinstance(numeric_level, int):
                logging.getLogger().setLevel(numeric_level)
                logger.info(f"Log level set to {log_level.upper()}")
            else:
                logger.warning(f"Invalid log level: {log_level}")

        if self.api_key:
            try:
                logger.info("Authenticating API key...")
                self.auth_status = authenticate_api_key(self.api_key)
                if not self.auth_status:
                    logger.error("API key authentication failed")
                    raise AuthenticationError("API key authentication failed")
                logger.info("API key authentication successful")
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                raise AuthenticationError(f"Authentication failed: {str(e)}")
        else:
            logger.warning("No API key provided. Some features may be limited.")
        
        self._register_default_handlers()
        
        from .runner import AppRunner
        
        runner = AppRunner(
            self.connection,
            self.event_dispatcher,
            auto_reconnect,
            reconnect_delay
        )
        runner.run(self)
    
    def _register_default_handlers(self):
        """Register default handlers for important system events if not already registered."""
        if CONNECTION_REJECTED_EVENT not in self.event_dispatcher.handlers:
            @self.on_connection_rejected
            def default_connection_rejected_handler(message: ConnectionRejectedMessage):
                reason = message.content.reason
                meeting_id = message.content.meeting_id
                logger.error(f"Connection rejected for meeting {meeting_id}: {reason}")
                self.running = False
    
    def stop(self) -> None:
        """Stop the application."""
        if not self.running:
            return
            
        self.running = False
        logger.info("Application stopping...")

    def create_meeting(self, meeting_id: str, start_time=None, end_time=None):
        """Create a meeting with the given parameters.
        
        Args:
            meeting_id: Unique identifier for the meeting
            start_time: Start time of the meeting as datetime object (defaults to current time)
            end_time: End time of the meeting as datetime object (defaults to 1 hour from start)
        """
        
        if not self.api_key:
            raise AuthenticationError("API key is required to create a meeting")
            
        if start_time is None:
            start_time = datetime.datetime.utcnow()
        
        if end_time is None:
            end_time = start_time + datetime.timedelta(hours=1000)
            
        start_time_utc = start_time.isoformat() + 'Z'
        end_time_utc = end_time.isoformat() + 'Z'

        url = 'https://backend.framewise.ai/api/py/setup-meeting'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        payload = {
            'meeting_id': meeting_id,
            'api_key': self.api_key,
            'start_time_utc': start_time_utc,
            'end_time_utc': end_time_utc
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        meeting_data = response.json()
        
        logger.info(f"Meeting created with ID: {meeting_id}")
        return meeting_data


    def on_ui_type(self, ui_type: str):
        """Register a handler for a specific UI element type.
        
        Args:
            ui_type: UI element type to handle (e.g., 'mcq_question', 'info_card')
            
        Returns:
            Decorator function
        """
        logger.debug(f"Creating handler for UI element type: {ui_type}")
        return self.on(ui_type)

    def on_connection_rejected(self, func: Callable[[ConnectionRejectedMessage], Any] = None):
        """Register a handler for connection rejection events.
        
        Args:
            func: Function that takes a ConnectionRejectedMessage and processes it
        """
        return self._on_event(EventType.CONNECTION_REJECTED, func, "on_connection_rejected")

