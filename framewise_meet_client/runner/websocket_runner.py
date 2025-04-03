import asyncio
import json
import logging
from typing import Dict, Any, Optional

# Import models from inbound module
from ..models.inbound import (
    BaseMessage, 
    ConnectionRejectedMessage,
    CustomUIElementResponse,
    TranscriptMessage,
    JoinMessage,
    ExitMessage,
    MCQSelectionMessage,
    InvokeMessage,
    # Add any other message types needed
)
from ..exceptions import InvalidMessageTypeError
from ..events import (
    INVOKE_EVENT, 
    TRANSCRIPT_EVENT, 
    JOIN_EVENT, 
    EXIT_EVENT, 
    CUSTOM_UI_EVENT,
    CONNECTION_REJECTED_EVENT
)

logger = logging.getLogger(__name__)

class WebSocketRunner:
    """Handles WebSocket communication and message processing."""

    def __init__(self, connection, event_dispatcher, auto_reconnect=True, reconnect_delay=5):
        """Initialize the runner.
        
        Args:
            connection: WebSocket connection object
            event_dispatcher: Event dispatcher for handling messages
            auto_reconnect: Whether to automatically reconnect on disconnect
            reconnect_delay: Delay between reconnection attempts in seconds
        """
        self.connection = connection
        self.event_dispatcher = event_dispatcher
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.app = None
        
        # Set up message class mapping for strict type conversion
        self._message_classes = {
            "transcript": TranscriptMessage,
            "on_join": JoinMessage,
            "on_exit": ExitMessage,
            "custom_ui_element_response": CustomUIElementResponse,
            "mcq_selection": MCQSelectionMessage,
            "connection_rejected": ConnectionRejectedMessage
        }

    def _convert_message(self, message_type: str, data: Dict[str, Any]) -> Optional[BaseMessage]:
        """Convert a raw message dictionary to the appropriate message type.
        
        Args:
            message_type: The type of message
            data: Raw message data
            
        Returns:
            A strongly-typed message object or None if conversion fails
        """
        message_class = self._message_classes.get(message_type)
        
        if message_class is None:
            logger.warning(f"No message class found for type {message_type}")
            return None
        
        try:
            converted = message_class.model_validate(data)
            logger.debug(f"Successfully converted {message_type} to {message_class.__name__}")
            return converted
        except Exception as e:
            logger.warning(f"Failed to convert {message_type} to {message_class.__name__}: {e}")
            
            # Special handling for specific message types that might have format issues
            try:
                # For on_join messages with a different structure
                if message_type == "on_join" and "content" in data and "user_joined" in data["content"]:
                    logger.debug("Trying alternative structure for join message")
                    return JoinMessage(type="on_join", content={"user_joined": data["content"]["user_joined"]})
                
                # For connection_rejected messages
                elif message_type == "connection_rejected":
                    logger.debug("Handling connection_rejected message")
                    return ConnectionRejectedMessage(
                        type="connection_rejected",
                        content={"reason": data.get("content", {}).get("reason", "Unknown reason")}
                    )
                    
                # Create a simple fallback for other messages
                return None
            except Exception as inner_e:
                logger.error(f"Failed to create alternative message: {inner_e}")
                return None

    async def _handle_message(self, data: Dict[str, Any]):
        """Process an incoming websocket message."""
        if "type" not in data:
            logger.warning("Received message without type field")
            return
            
        message_type = data["type"]
        logger.info(data)  # Log the raw message for debugging
        
        # Special handling for connection_rejected messages
        if message_type == "connection_rejected":
            try:
                rejected_message = self._convert_message(message_type, data)
                if rejected_message:
                    reason = getattr(rejected_message.content, "reason", "Unknown reason")
                    logger.warning(f"Connection rejected: {reason}")
                    await self.event_dispatcher.dispatch("connection_rejected", rejected_message)
                else:
                    # Fallback if we couldn't convert the message
                    reason = data.get("content", {}).get("reason", "Unknown reason")
                    logger.warning(f"Connection rejected (raw): {reason}")
                    
                # Stop the connection if rejected
                self.app.running = False
                return
            except Exception as e:
                logger.error(f"Failed to process connection rejection: {e}")
                # Still try to stop the app
                self.app.running = False
                return
        
        # Convert message to proper type
        converted = self._convert_message(message_type, data)
        
        # If conversion failed, log and return
        if converted is None:
            logger.error(f"Failed to convert message of type {message_type}")
            return
            
        try:
            # Dispatch the converted message to event handlers
            await self.event_dispatcher.dispatch(message_type, converted)
            
            # Handle special events
            if message_type == "transcript" and hasattr(converted, 'content') and hasattr(converted.content, 'is_final'):
                # Check if this is a final transcript
                if converted.content.is_final:
                    logger.debug("Final transcript detected, triggering invoke event")
                    await self.event_dispatcher.dispatch(INVOKE_EVENT, converted)
            
            # Handle UI subtypes for custom UI elements
            elif message_type == "custom_ui_element_response" and isinstance(converted, CustomUIElementResponse):
                try:
                    ui_subtype = converted.content.type
                    if ui_subtype:
                        logger.debug(f"Dispatching to UI subtype: {ui_subtype}")
                        await self.event_dispatcher.dispatch(ui_subtype, converted)
                except Exception as e:
                    logger.error(f"Error dispatching UI subtype: {e}")
                    # Don't let UI handling errors stop the main processing
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _receive_loop(self):
        """Main loop for receiving and processing messages."""
        while self.app and self.app.running:
            try:
                message = await self.connection.receive()
                if message:
                    data = json.loads(message)
                    await self._handle_message(data)
            except json.JSONDecodeError:
                logger.error("Failed to decode message as JSON")
            except InvalidMessageTypeError as e:
                logger.error(f"Invalid message: {str(e)}")
            except Exception as e:
                logger.error(f"Error in receive loop: {str(e)}")
                
                if not self.auto_reconnect:
                    logger.info("Auto-reconnect disabled, stopping")
                    self.app.running = False
                    break
                
                logger.info(f"Attempting to reconnect in {self.reconnect_delay} seconds")
                await asyncio.sleep(self.reconnect_delay)
                
                try:
                    await self.connection.reconnect()
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {str(reconnect_error)}")
                    self.app.running = False
                    break

    def run(self, app):
        """Run the WebSocket client.
        
        Args:
            app: The application instance
        """
        self.app = app
        app.running = True
        
        # Create and run the event loop
        loop = asyncio.get_event_loop()
        app.loop = loop
        
        try:
            app._main_task = loop.create_task(self._receive_loop())
            loop.run_until_complete(app._main_task)
        except asyncio.CancelledError:
            logger.info("WebSocket connection canceled")
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {str(e)}")
        finally:
            app.running = False
            logger.info("WebSocket connection closed")

    async def close(self):
        """Close the WebSocket connection gracefully."""
        if self.connection:
            await self.connection.close()
            logger.info("WebSocket connection closed")
