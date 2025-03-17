import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Type, TypeVar, cast, Union

from .connection import WebSocketConnection
from .event_handler import EventDispatcher
from .errors import AppNotRunningError, ConnectionError, AuthenticationError
from .messaging import MessageSender
from .models.messages import (
    JoinMessage, ExitMessage, TranscriptMessage, 
    CustomUIElementMessage, MCQSelectionMessage,
    ConnectionRejectedMessage,  # Add this import
    MessagePayload, BaseMessage
)
import datetime
from .events import (
    TRANSCRIPT_EVENT, JOIN_EVENT, EXIT_EVENT, 
    CUSTOM_UI_EVENT, INVOKE_EVENT,
    CONNECTION_REJECTED_EVENT,  # Add this import
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

# Type variable for handler functions with specific message types
T = TypeVar('T', bound=BaseMessage)

class App:
    """WebSocket client app with decorator-based event handlers."""
    
    # Mapping of event type aliases to standard event types
    _event_aliases = {
        "join": JOIN_EVENT,
        "exit": EXIT_EVENT,
        "transcript": TRANSCRIPT_EVENT,
        "custom_ui_element_response": CUSTOM_UI_EVENT,
        "custom_ui": CUSTOM_UI_EVENT,
        "invoke": INVOKE_EVENT,
        "connection_rejected": CONNECTION_REJECTED_EVENT  # Update this line
        # Subtypes are handled directly, not through aliases
    }
    
    # Message type mapping for backward compatibility
    _message_type_mapping = {
        JOIN_EVENT: JoinMessage,
        EXIT_EVENT: ExitMessage,
        TRANSCRIPT_EVENT: TranscriptMessage,
        CUSTOM_UI_EVENT: CustomUIElementMessage,
        INVOKE_EVENT: TranscriptMessage,
        CONNECTION_REJECTED_EVENT: ConnectionRejectedMessage  # Add this line
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
    
    def on(self, event_type: str):
        """Decorator to register an event handler for a specific message type.
        
        Resolves event aliases to standard event types.
        
        Args:
            event_type: Type of event to handle (e.g., "transcript", "join")
                        Or a UI element type (e.g., "mcq_question", "info_card")
        
        Returns:
            Decorator function
        """
        # Regular event handling through aliases
        resolved_event_type = self._event_aliases.get(event_type, event_type)
        
        if resolved_event_type != event_type:
            logger.debug(f"Resolved event alias '{event_type}' to standard event type '{resolved_event_type}'")
        
        def decorator(func):
            # For UI element types (not in our standard aliases), register a direct handler
            if event_type not in self._event_aliases:
                logger.debug(f"Registering direct handler for UI element type: {event_type}")
                
                # Create wrapper that passes the parsed message directly when available
                def wrapper(data):
                    if "parsed_message" in data:
                        # Pass the CustomUIElementMessage object directly to the handler
                        return func(data["parsed_message"])
                    else:
                        # Fallback to raw data
                        return func(data)
                
                # Register the wrapper directly at the subtype level
                self.event_dispatcher.register_handler(event_type)(wrapper)
                return func
            
            # Otherwise use standard event registration
            logger.debug(f"Registering handler for event type '{resolved_event_type}': {func.__name__}")
            return register_event_handler(self, resolved_event_type, func)
        
        return decorator
    
    # Typed convenience methods that forward to the on() method
    def on_transcript(self, func: Callable[[TranscriptMessage], Any] = None):
        """Register a handler for transcript events."""
        if func is None:
            # Used with parentheses like @app.on_transcript()
            return self.on(TRANSCRIPT_EVENT)
        # Used without parentheses like @app.on_transcript
        logger.debug(f"Using on_transcript shorthand for {func.__name__}")
        return self.on(TRANSCRIPT_EVENT)(func)
    
    def on_join(self, func: Callable[[JoinMessage], Any] = None):
        """Register a handler for user join events."""
        if func is None:
            return self.on(JOIN_EVENT)
        logger.debug(f"Using on_join shorthand for {func.__name__}")
        return self.on(JOIN_EVENT)(func)
    
    def on_exit(self, func: Callable[[ExitMessage], Any] = None):
        """Register a handler for user exit events."""
        if func is None:
            return self.on(EXIT_EVENT)
        logger.debug(f"Using on_exit shorthand for {func.__name__}")
        return self.on(EXIT_EVENT)(func)
    
    def on_custom_ui_response(self, func: Callable[[CustomUIElementMessage], Any] = None):
        """Register a handler for custom UI element response events."""
        if func is None:
            return self.on(CUSTOM_UI_EVENT)
        logger.debug(f"Using on_custom_ui_response shorthand for {func.__name__}")
        return self.on(CUSTOM_UI_EVENT)(func)
    
    def on_invoke(self, func: Callable[[TranscriptMessage], Any] = None):
        """Register a handler for invoke events (triggered by final transcripts).
        
        Args:
            func: Function that takes a TranscriptMessage and processes the event
        """
        if func is None:
            return self.on(INVOKE_EVENT)
        logger.debug(f"Using on_invoke shorthand for {func.__name__}")
        return self.on(INVOKE_EVENT)(func)
    
    def invoke(self, func: Callable[[TranscriptMessage], Any] = None):
        """Alias for on_invoke for convenience.
        
        Args:
            func: Function that takes a TranscriptMessage and processes the event
        """
        return self.on_invoke(func)
    
    def send_generated_text(self, text: str, is_generation_end: bool = False) -> None:
        """Send generated text to the server.
        
        Args:
            text: The generated text
            is_generation_end: Whether this is the end of generation
        """
        if not self.loop:
            raise AppNotRunningError("App is not running")
        
        logger.debug(f"Sending generated text (end={is_generation_end}): {text[:50]}{'...' if len(text) > 50 else ''}")
        self.message_sender.send_generated_text(text, is_generation_end, self.loop)
    
    def send_custom_ui_element(self, ui_type: str, data: Dict[str, Any]) -> None:
        """Send a custom UI element to the server.
        
        Args:
            ui_type: Type of UI element (e.g., 'mcq_question')
            data: Element-specific data
        """
        if not self.loop:
            raise AppNotRunningError("App is not running")
        
        logger.debug(f"Sending custom UI element of type '{ui_type}'")
        self.message_sender.send_custom_ui_element(ui_type, data, self.loop)
    
    def send_mcq_question(self, question_id: str, question: str, options: List[str]) -> None:
        """Send an MCQ question as a custom UI element.
        
        Args:
            question_id: Unique identifier for the question
            question: The question text
            options: List of answer options
        """
        if not self.loop:
            raise AppNotRunningError("App is not running")
        
        logger.debug(f"Sending MCQ question '{question_id}': {question}")
        self.message_sender.send_mcq_question(question_id, question, options, self.loop)
    
    def run(self, auto_reconnect: bool = True, reconnect_delay: int = 5, log_level: str = None) -> None:
        """Run the application (blocking).
        
        Args:
            auto_reconnect: Whether to automatically reconnect on disconnect
            reconnect_delay: Delay between reconnection attempts in seconds
            log_level: Optional log level to set (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Set log level if provided
        if log_level:
            numeric_level = getattr(logging, log_level.upper(), None)
            if isinstance(numeric_level, int):
                logging.getLogger().setLevel(numeric_level)
                logger.info(f"Log level set to {log_level.upper()}")
            else:
                logger.warning(f"Invalid log level: {log_level}")
        
        # Authenticate API key if provided
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
        
        # Register default handlers for important system events if not already registered
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
        # Register a default connection_rejected handler if none exists
        if CONNECTION_REJECTED_EVENT not in self.event_dispatcher.handlers:
            @self.on_connection_rejected
            def default_connection_rejected_handler(message: ConnectionRejectedMessage):
                reason = message.content.reason
                meeting_id = message.content.meeting_id
                logger.error(f"Connection rejected for meeting {meeting_id}: {reason}")
                # Stop reconnection attempts for this rejected connection
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
            
        # Set default times if not provided
        if start_time is None:
            start_time = datetime.datetime.utcnow()
        
        if end_time is None:
            end_time = start_time + datetime.timedelta(hours=1000)
            
        # Convert datetime objects to ISO format strings
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

    def send_notification(self, message: str, level: str = "info", duration: int = 8000) -> None:
        """Send a notification to all users in the meeting.
        
        Args:
            message: The notification message to display
            level: The notification level (info, warning, error, success)
            duration: How long the notification should display (in milliseconds)
        """
        if not self.loop:
            raise AppNotRunningError("App is not running")
        
        if not self.message_sender:
            logger.warning("Cannot send notification: No active connection")
            return
        
        logger.debug(f"Sending notification: {message}")
        self.message_sender.send_notification(message, level, duration, self.loop)

    def on_connection_rejected(self, func: Callable[[ConnectionRejectedMessage], Any] = None):
        """Register a handler for connection rejection events.
        
        Args:
            func: Function that takes a ConnectionRejectedMessage and processes it
        """
        if func is None:
            return self.on(CONNECTION_REJECTED_EVENT)
        logger.debug(f"Using on_connection_rejected shorthand for {func.__name__}")
        return self.on(CONNECTION_REJECTED_EVENT)(func)