"""
Runner module for the Framewise Meet client.

This module defines the AppRunner class, which manages the application's
main event loop, including WebSocket connection management, message
conversion, event dispatching, reconnection logic, and graceful shutdown.

Usage example:
    runner = AppRunner(connection, event_dispatcher)
    runner.run(app)
"""
import asyncio
import logging
import signal
from typing import Dict, Any, Type, Optional, Union
from pydantic import BaseModel, ValidationError

from .errors import ConnectionError, AuthenticationError
from .models.inbound import (
    JoinMessage,
    ExitMessage,
    TranscriptMessage,
    CustomUIElementResponse,
    MCQSelectionMessage,
    ConnectionRejectedMessage,
)
from .events import INVOKE_EVENT, CUSTOM_UI_EVENT, EXIT_EVENT

logger = logging.getLogger(__name__)


class AppRunner:
    """
    Manages the application's main event loop with improved reliability.
    
    The AppRunner is responsible for:
    1. Establishing and maintaining WebSocket connections
    2. Processing incoming messages and converting them to appropriate model types
    3. Dispatching events to registered handlers
    4. Managing reconnection attempts when connections fail
    5. Handling graceful shutdown when termination signals are received
    
    It serves as the core runtime component of the Framewise Meet Client,
    orchestrating the flow of messages between the WebSocket connection and
    the event handling system.
    """

    # Message type mapping
    _message_classes = {
        "on_join": JoinMessage,
        "on_exit": ExitMessage,
        "transcript": TranscriptMessage,
        "custom_ui_element_response": CustomUIElementResponse,
        "mcq_selection": MCQSelectionMessage,
        "connection_rejected": ConnectionRejectedMessage,
    }

    def __init__(
        self, connection, event_dispatcher, auto_reconnect=True, reconnect_delay=5
    ):
        """
        Initialize the application runner.

        Args:
            connection: WebSocketConnection instance that manages the underlying
                        WebSocket connection to the Framewise backend.
            event_dispatcher: EventDispatcher instance responsible for routing
                             events to appropriate handlers.
            auto_reconnect: Boolean indicating whether to automatically reconnect
                          on disconnection (default: True).
            reconnect_delay: Delay between reconnection attempts in seconds (default: 5).
        """
        self.connection = connection
        self.event_dispatcher = event_dispatcher
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay

    def _convert_message(
        self, message_type: str, data: Dict[str, Any]
    ) -> Optional[BaseModel]:
        """
        Convert raw message data to the appropriate message object type.

        This method validates and converts incoming JSON data to strongly-typed
        Pydantic model instances based on the message type. This provides
        type safety and validation for all incoming messages.

        Args:
            message_type: Type identifier of the message.
            data: Raw message data dictionary received from WebSocket.

        Returns:
            Converted message object or None if conversion failed due to validation
            errors or if no appropriate message class was found.
            
        Raises:
            ValidationError: If the message data fails validation against the model schema.
                           This is caught internally and logged as a warning.
        """
        message_class = self._message_classes.get(message_type)
        if not message_class:
            return None

        try:
            logger.debug(f"Converting raw data to {message_class.__name__}")
            return message_class.model_validate(data)
        except ValidationError as e:
            logger.warning(f"Validation error converting {message_type}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error converting {message_type}: {e}")
            return None

    async def _listen(self) -> None:
        """
        Listen for incoming messages and dispatch to handlers.
        
        This method runs in a continuous loop while the connection is active,
        receiving messages from the WebSocket connection, converting them to
        appropriate types, and dispatching them to registered event handlers.
        
        Special handling is implemented for:
        - Connection rejection messages that may terminate the connection
        - Final transcript messages that trigger the invoke event
        - Custom UI element responses that may require additional dispatching
          based on element type
        
        Returns:
            None
            
        Raises:
            ConnectionError: If there's an issue with the WebSocket connection.
                           This is caught internally and may trigger reconnection.
        """
        try:
            while self.connection.connected:
                data = await self.connection.receive()

                logger.info(data)
                if "type" not in data:
                    logger.warning("Received message without type field")
                    continue

                message_type = data["type"]

                # Special handling for connection_rejected messages
                if message_type == "connection_rejected":
                    rejected_message = ConnectionRejectedMessage.model_validate(data)
                    logger.warning(
                        f"Connection rejected: {rejected_message.content.reason}"
                    )
                    await self.event_dispatcher.dispatch(
                        "connection_rejected", rejected_message
                    )

                    # Stop the connection if rejected
                    self.app.running = False
                    break

                # Always try to convert every message to its proper type
                converted = None
                message_class = self._message_classes.get(message_type)

                if message_class is not None:
                    try:
                        converted = message_class.model_validate(data)
                        logger.debug(
                            f"Successfully converted to {message_class.__name__}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to convert {message_type} to {message_class.__name__}: {e}"
                        )

                # Dispatch the converted message if available, raw data otherwise
                await self.event_dispatcher.dispatch(message_type, converted or data)

                # Handle special events
                if message_type == "transcript":
                    # Check if this is a final transcript
                    is_final = False
                    if converted and isinstance(converted, TranscriptMessage):
                        is_final = converted.content.is_final
                    elif isinstance(data, dict):
                        try:
                            is_final = data.get("content", {}).get("is_final", False)
                        except:
                            pass

                    if is_final:
                        logger.debug(
                            "Final transcript detected, triggering invoke event"
                        )
                        await self.event_dispatcher.dispatch(
                            INVOKE_EVENT, converted or data
                        )

                # Handle UI subtypes and custom UI element responses
                elif message_type == "custom_ui_element_response":
                    ui_subtype = None
                    if isinstance(data, dict):
                        try:
                            ui_subtype = data.get("content", {}).get("type")
                        except:
                            pass

                    if ui_subtype:
                        logger.debug(f"Dispatching to UI element type: {ui_subtype}")
                        await self.event_dispatcher.dispatch(
                            ui_subtype, converted or data
                        )

        except ConnectionError as e:
            logger.warning(f"Connection error: {str(e)}")

    async def _main_loop(self) -> None:
        """
        Main application event loop.
        
        This method manages the application's main lifecycle, including:
        - Initial connection establishment
        - Listening for incoming messages
        - Handling reconnection attempts when connections fail
        - Cleaning up resources when the application is shutting down
        
        The loop continues running until the application is explicitly stopped
        or a non-recoverable error occurs.
        
        Returns:
            None
        """
        try:
            while self.app.running:
                try:
                    await self.connection.connect()
                    await self._listen()
                except Exception as e:
                    logger.error(f"Connection error: {str(e)}")

                if not self.auto_reconnect or not self.app.running:
                    break

                logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)

        finally:
            # Clean up on exit
            if self.connection.connected:
                await self.connection.disconnect()

    def _handle_signal(self, sig, frame):
        """
        Handle termination signals for graceful shutdown.
        
        This method is registered as a signal handler for SIGINT and SIGTERM
        signals, allowing the application to perform clean shutdown procedures
        when interrupted by the user or the system.
        
        Args:
            sig: Signal number received.
            frame: Current stack frame.
            
        Returns:
            None
        """
        logger.info(f"Received signal {sig}, shutting down...")
        self.app.stop()

    def run(self, app):
        """
        Run the application in a blocking manner.
        
        This method starts the main application loop and sets up signal handlers
        for graceful shutdown. It manages the complete lifecycle of the application,
        from startup to shutdown.
        
        Args:
            app: The application instance to run.
            
        Returns:
            None
        """
        self.app = app

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # Create a new event loop in this thread
        self.app.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.app.loop)

        try:
            self.app.running = True
            self.app._main_task = self.app.loop.create_task(self._main_loop())
            self.app.loop.run_until_complete(self.app._main_task)
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
        finally:
            # Clean up
            self.app.running = False

            # Cancel the main task if it's still running
            if self.app._main_task and not self.app._main_task.done():
                self.app._main_task.cancel()
                try:
                    self.app.loop.run_until_complete(self.app._main_task)
                except asyncio.CancelledError:
                    pass

            # Close the event loop
            self.app.loop.close()
            self.app.loop = None
