import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Type, TypeVar, cast, Union
from enum import Enum

from .connection import WebSocketConnection
from .event_handler import EventDispatcher
from .errors import AppNotRunningError, ConnectionError, AuthenticationError
from .messaging import MessageSender
from pydantic import BaseModel
# Import inbound messages
from .models.inbound import (
    BaseMessage,
    JoinMessage,
    ExitMessage,
    TranscriptMessage,
    InvokeMessage,
    MCQSelectionMessage,
    CustomUIElementResponse,
    ConnectionRejectedMessage,
    TranscriptContent,
    JoinEvent,
    ExitEvent,
    MCQSelectionEvent,
    ConnectionRejectedEvent,
    CustomUIContent,
    # Add any other imports needed
)
# Import outbound messages
from .models.outbound import (
    GeneratedTextMessage,
    MCQMessage,
    CustomUIElement as OutboundCustomUIMessage,
    CustomUIElementMessage,
    ErrorResponse,
    GeneratedTextContent,
    MCQContent,
    CustomUIContent as OutboundCustomUIContent,
    MultipleChoiceQuestion,
    MCQOption,
    ButtonElement,
    InputElement,
    MCQQuestionData,
    MCQQuestionElement,
    NotificationData,
    NotificationElement,
)
import datetime
from .events import (
    TRANSCRIPT_EVENT,
    JOIN_EVENT,
    EXIT_EVENT,
    CUSTOM_UI_EVENT,
    INVOKE_EVENT,
    CONNECTION_REJECTED_EVENT,
    MCQ_QUESTION_EVENT,
    PLACES_AUTOCOMPLETE_EVENT,
    UPLOAD_FILE_EVENT,
    TEXTINPUT_EVENT,
    CONSENT_FORM_EVENT,
    CALENDLY_EVENT,
    register_event_handler,
)
from .exceptions import InvalidMessageTypeError

import requests
from .auth import authenticate_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EventType(Enum):
    TRANSCRIPT = TRANSCRIPT_EVENT
    JOIN = JOIN_EVENT
    EXIT = EXIT_EVENT
    CUSTOM_UI_RESPONSE = CUSTOM_UI_EVENT
    INVOKE = INVOKE_EVENT
    CONNECTION_REJECTED = CONNECTION_REJECTED_EVENT


T = TypeVar("T", bound=BaseMessage)


class App:
    """
    WebSocket client application with decorator-based event handling.
    
    The App class serves as the primary interface for developers building applications
    with the Framewise Meet Client. It provides:
    
    1. A simple decorator-based API for registering event handlers
    2. Methods for sending different types of messages to the Framewise backend
    3. Connection management with automatic reconnection capabilities
    4. Type-safe event handling with proper validation
    
    Event handlers can be registered using either the generic on() method or 
    specific convenience methods like on_transcript(), on_join(), etc.
    
    Example:
        ```python
        app = App(api_key="your_api_key")
        
        @app.on_transcript()
        def handle_transcript(message):
            print(f"Received transcript: {message.content.text}")
            
        app.join_meeting("meeting-id")
        app.run()
        ```
    """

    _event_aliases = {
        "join": JOIN_EVENT,
        "exit": EXIT_EVENT,
        "transcript": TRANSCRIPT_EVENT,
        "custom_ui_response": CUSTOM_UI_EVENT,
        "custom_ui": CUSTOM_UI_EVENT,
        "invoke": INVOKE_EVENT,
        "connection_rejected": CONNECTION_REJECTED_EVENT,
        "mcq_question": MCQ_QUESTION_EVENT,
        "places_autocomplete": PLACES_AUTOCOMPLETE_EVENT,
        "upload_file": UPLOAD_FILE_EVENT,
        "textinput": TEXTINPUT_EVENT,
        "consent_form": CONSENT_FORM_EVENT,
        "calendly": CALENDLY_EVENT,
    }

    _message_type_mapping = {
        JOIN_EVENT: JoinMessage,
        EXIT_EVENT: ExitMessage,
        TRANSCRIPT_EVENT: TranscriptMessage,
        CUSTOM_UI_EVENT: CustomUIElementResponse,
        INVOKE_EVENT: TranscriptMessage,  # Note: InvokeMessage is just TranscriptMessage with is_final=True
        CONNECTION_REJECTED_EVENT: ConnectionRejectedMessage,
    }

    def __init__(
        self, api_key: Optional[str] = None, host: str = "localhost", port: int = 8000
    ):
        """
        Initialize the Framewise Meet client application with connection parameters.
        
        Args:
            api_key: Optional API key for authentication with the Framewise API.
                   Required for creating meetings and accessing protected features.
            host: Server hostname or IP address where the Framewise API is running.
                 Defaults to "localhost" for local development.
            port: Server port number. Defaults to 8000.
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

    def join_meeting(self, meeting_id):
        """
        Connect to a specific meeting using the provided meeting ID.
        
        This method initializes the WebSocket connection to the Framewise backend
        and connects the app to a specific meeting. It also sets up the MessageSender
        and dynamically binds its methods to the App instance to provide message
        sending capabilities.
        
        Args:
            meeting_id: Unique identifier for the meeting to join.
                       This ID must correspond to an existing meeting in the Framewise system.
                       
        Note:
            This method must be called before running the application.
        """
        self.meeting_id = meeting_id
        self.connection = WebSocketConnection(
            self.host, self.port, meeting_id, self.api_key
        )
        self.message_sender = MessageSender(self.connection)

        for name in dir(self.message_sender):
            if not name.startswith("_") and callable(
                getattr(self.message_sender, name)
            ):
                logging.info(f"Set {name} in message_sender")
                setattr(self, name, getattr(self.message_sender, name))

    def on(self, event_type: str) -> Callable[[Callable[[BaseMessage], Any]], Callable[[BaseMessage], Any]]:
        """
        Register a handler for a specific event type.
        
        This is the core event registration method that all other event handling
        methods use internally. It handles event type aliasing and ensures type safety
        for message handlers.
        
        Args:
            event_type: The event type to register for (e.g., "transcript", "join", "exit").
                      Can be either a direct event type or an alias defined in _event_aliases.
            
        Returns:
            A decorator function that registers the decorated function as a handler
            for the specified event type.
            
        Example:
            ```python
            @app.on("transcript")
            def handle_transcript(message):
                print(f"Received transcript: {message.content.text}")
            ```
        """
        # Check if this is an alias and get the main event type
        resolved_event_type = self._event_aliases.get(event_type, event_type)
        
        if resolved_event_type != event_type:
            logger.debug(f"Resolved event alias '{event_type}' to standard event type '{resolved_event_type}'")
        
        # Get the correct message type for this event
        message_class = self._message_type_mapping.get(resolved_event_type)
        
        def decorator(func: Callable[[BaseMessage], Any]) -> Callable[[BaseMessage], Any]:
            if self.event_dispatcher is None:
                self.event_dispatcher = EventDispatcher()
                
            # Create a wrapper that ensures type safety
            def type_safe_handler(message: BaseMessage) -> Any:
                # Verify we got the correct message type
                if message_class and not isinstance(message, message_class):
                    logger.error(f"Expected {message_class.__name__}, got {type(message).__name__}")
                    return None
                
                return func(message)
                
            # Register the handler with the specified event type
            self.event_dispatcher.register(resolved_event_type, type_safe_handler)
            logger.debug(f"Registered handler {func.__name__} for event type {resolved_event_type}")
            return func
            
        return decorator

    def __getattr__(self, name):
        """
        Dynamically create event handler registration methods.
        
        This magic method allows methods like on_transcript(), on_join(), etc. to be
        generated dynamically when accessed, providing a more intuitive API for
        registering event handlers.
        
        Args:
            name: The attribute name being accessed.
            
        Returns:
            A method that registers event handlers if the name follows the pattern
            "on_<event_type>", otherwise raises AttributeError.
            
        Raises:
            AttributeError: If the requested attribute doesn't follow the pattern
                          "on_<event_type>" or if the event type is not recognized.
        """
        if name.startswith("on_"):
            event_name = name[3:]

            if event_name in self._event_aliases:
                event_type_value = self._event_aliases[event_name]

                def handler_method(func=None):
                    return self._on_event(event_type_value, func, name)

                return handler_method

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def _on_event(
        self,
        event_type: Union[str, EventType],
        func: Callable[[BaseModel], Any] = None,
        shorthand_name: str = None,
    ):
        """
        Helper function to reduce code duplication in event registration.
        
        This internal method is used by the dynamically generated event handler
        registration methods to provide a consistent way to register handlers.
        
        Args:
            event_type: The type of event to register for, either as a string or an EventType enum.
            func: The function to register as a handler, or None if using as a decorator.
            shorthand_name: The name of the shorthand method being used (for logging).
            
        Returns:
            Either the registered function or a decorator function that will register
            a function when applied.
        """
        event_type_value = (
            event_type.value if isinstance(event_type, EventType) else event_type
        )
        if func is None:
            return self.on(event_type_value)
        logger.debug(f"Using {shorthand_name} shorthand for {func.__name__}")
        return self.on(event_type_value)(func)

    def invoke(self, func: Callable[[TranscriptMessage], Any] = None):
        """
        Register a handler for invoke events (final transcripts).
        
        Invoke events are triggered when a final transcript is received. This is a
        convenience method alias for on_invoke() and provides a clearer API for
        registering handlers that process complete user utterances.
        
        Args:
            func: Function that takes a TranscriptMessage and processes the event.
                 If None, returns a decorator function.
                 
        Returns:
            Either the registered function or a decorator function.
            
        Example:
            ```python
            @app.invoke
            def process_final_transcript(message):
                transcript = message.content.text
                print(f"Processing final transcript: {transcript}")
            ```
        """
        return self.on_invoke(func)

    def run(
        self,
        auto_reconnect: bool = True,
        reconnect_delay: int = 5,
        log_level: str = None,
    ) -> None:
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
            self.connection, self.event_dispatcher, auto_reconnect, reconnect_delay
        )
        runner.run(self)

    # Update the default connection rejected handler with better error handling
    def _register_default_handlers(self):
        """Register default handlers for important system events if not already registered."""
        if CONNECTION_REJECTED_EVENT not in self.event_dispatcher._handlers:

            @self.on_connection_rejected
            def default_connection_rejected_handler(message: ConnectionRejectedMessage):
                reason = message.content.reason if hasattr(message, 'content') and hasattr(message.content, 'reason') else "Unknown reason"
                logger.error(f"Connection rejected: {reason}")
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

        
        

        url = "https://backend.framewise.ai/api/py/setup-meeting"
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        payload = {
            "meeting_id": meeting_id,
            "api_key": self.api_key,
        }

        if start_time is not None:
            start_time_utc = start_time.isoformat() + "Z"
            payload['start_time_utc'] = start_time_utc

        if end_time is not None:
            end_time_utc = end_time.isoformat() + "Z"
            payload['end_time_utc'] = end_time_utc

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        meeting_data = response.json()

        logger.info(f"Meeting created with ID: {meeting_id}")
        return meeting_data

    def on_ui_type(self, ui_type: str) -> Callable[[Callable[[CustomUIElementMessage], Any]], Callable[[CustomUIElementMessage], Any]]:
        """Register a handler for a specific UI element type.

        Args:

        Returns:
            Decorator function
        """
        logger.debug(f"Creating handler for UI element type: {ui_type}")
        return self.on(ui_type)

    def on_connection_rejected(
        self, func: Callable[[ConnectionRejectedMessage], Any] = None
    ):
        """Register a handler for connection rejection events.

        Args:
            func: Function that takes a ConnectionRejectedMessage and processes it
        """
        return self._on_event(
            EventType.CONNECTION_REJECTED, func, "on_connection_rejected"
        )

    # Add convenience methods for UI element response handlers
    def on_custom_ui_element_response(self, func=None):
        """Register a handler for custom UI element response events.

        Args:
            func: Function that takes a CustomUIElementMessage and processes it.
                  If None, returns a decorator.

        Returns:
            Either the registered function or a decorator function
        """
        return self.on(CUSTOM_UI_EVENT)(func) if func else self.on(CUSTOM_UI_EVENT)

    def on_mcq_question_response(self, func=None):
        """Register a handler for MCQ question response events.

        Args:
            func: Function that takes a CustomUIElementMessage with MCQ data and processes it.
                  If None, returns a decorator.

        Returns:
            Either the registered function or a decorator function
        """
        return (
            self.on(MCQ_QUESTION_EVENT)(func) if func else self.on(MCQ_QUESTION_EVENT)
        )

    def on_places_autocomplete_response(self, func=None):
        """Register a handler for places autocomplete response events.

        Args:
            func: Function that takes a CustomUIElementMessage with places autocomplete data and processes it.
                  If None, returns a decorator.

        Returns:
            Either the registered function or a decorator function
        """
        return (
            self.on(PLACES_AUTOCOMPLETE_EVENT)(func)
            if func
            else self.on(PLACES_AUTOCOMPLETE_EVENT)
        )

    def on_upload_file_response(self, func=None):
        """Register a handler for file upload response events.

        Args:
            func: Function that takes a CustomUIElementMessage with file upload data and processes it.
                  If None, returns a decorator.

        Returns:
            Either the registered function or a decorator function
        """
        return self.on(UPLOAD_FILE_EVENT)(func) if func else self.on(UPLOAD_FILE_EVENT)

    def on_textinput_response(self, func=None):
        """Register a handler for text input response events.

        Args:
            func: Function that takes a CustomUIElementMessage with text input data and processes it.
                  If None, returns a decorator.

        Returns:
            Either the registered function or a decorator function
        """
        return self.on(TEXTINPUT_EVENT)(func) if func else self.on(TEXTINPUT_EVENT)

    def on_consent_form_response(self, func=None):
        """Register a handler for consent form response events.

        Args:
            func: Function that takes a CustomUIElementMessage with consent form data and processes it.
                  If None, returns a decorator.

        Returns:
            Either the registered function or a decorator function
        """
        return (
            self.on(CONSENT_FORM_EVENT)(func) if func else self.on(CONSENT_FORM_EVENT)
        )

    def on_calendly_response(self, func=None):
        """Register a handler for Calendly scheduling response events.

        Args:
            func: Function that takes a CustomUIElementMessage with Calendly data and processes it.
                  If None, returns a decorator.

        Returns:
            Either the registered function or a decorator function
        """
        return self.on(CALENDLY_EVENT)(func) if func else self.on(CALENDLY_EVENT)

    def on_ui_element_response(self, element_type: str = None):
        """Register a handler for UI element responses.
        
        Args:
            element_type: Optional specific UI element type to handle
                          (mcq_question, places_autocomplete, etc.)
        """
        event_type = "custom_ui_element_response"
        
        def decorator(func):
            # If a specific element type is provided
            if (element_type):
                # Create wrapper that checks the element type
                async def wrapper(message: CustomUIElementResponse):
                    if not isinstance(message, CustomUIElementResponse):
                        logger.error(f"Expected CustomUIElementResponse, got {type(message).__name__}")
                        return
                        
                    try:
                        if message.content.type == element_type:
                            return await func(message)
                    except Exception as e:
                        logger.error(f"Error handling {element_type} response: {str(e)}")
                
                # Register element-specific handler
                logger.debug(f"Registering handler for UI element type: {element_type}")
                self.event_dispatcher.register(event_type, wrapper)
            else:
                # Register general handler for all UI responses
                def type_safe_wrapper(message: CustomUIElementResponse):
                    if not isinstance(message, CustomUIElementResponse):
                        logger.error(f"Expected CustomUIElementResponse, got {type(message).__name__}")
                        return
                    
                    try:
                        return func(message)
                    except Exception as e:
                        logger.error(f"Error handling custom UI response: {str(e)}")
                
                self.event_dispatcher.register(event_type, type_safe_wrapper)
                
            return func
            
        return decorator
        
    # Convenience methods for specific UI element responses
    
    def on_mcq_response(self):
        """Register a handler specifically for MCQ question responses."""
        def mcq_decorator(func):
            async def mcq_wrapper(message: CustomUIElementResponse):
                try:
                    if isinstance(message, CustomUIElementResponse) and message.content.type == "mcq_question":
                        data = message.content.data
                        # Access fields safely
                        selected_option = getattr(data, "selectedOption", None)
                        if selected_option is None and isinstance(data, dict):
                            selected_option = data.get("selectedOption")
                            
                        selected_index = getattr(data, "selectedIndex", None)
                        if selected_index is None and isinstance(data, dict):
                            selected_index = data.get("selectedIndex")
                            
                        # Pass the processed message to the handler
                        return await func(message)
                except Exception as e:
                    logger.error(f"Error handling MCQ question: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
            self.event_dispatcher.register("mcq_question", mcq_wrapper)
            return func
        
        return mcq_decorator
        
    def on_places_autocomplete_response(self):
        """Register a handler specifically for places autocomplete responses."""
        return self.on_ui_element_response("places_autocomplete")
    
    def on_file_upload_response(self):
        """Register a handler specifically for file upload responses."""
        return self.on_ui_element_response("upload_file")
    
    def on_text_input_response(self):
        """Register a handler specifically for text input responses."""
        return self.on_ui_element_response("textinput")
    
    def on_consent_form_response(self):
        """Register a handler specifically for consent form responses."""
        return self.on_ui_element_response("consent_form")
    
    def on_calendly_response(self):
        """Register a handler specifically for Calendly scheduling responses."""
        return self.on_ui_element_response("calendly")
