import asyncio
import logging
import json
from typing import List, Dict, Any, Optional

from .models.messages import (
    MCQQuestionSendData, 
    CustomUIElementSendData,
    GeneratedTextContent
)

from .errors import ConnectionError

logger = logging.getLogger(__name__)

class MessageSender:
    """Manages sending messages to the server."""
    
    def __init__(self, connection):
        """Initialize the message sender.
        
        Args:
            connection: WebSocketConnection instance
        """
        self.connection = connection
    
    async def _send_message(self, message: Dict[str, Any]) -> None:
        """Send a message over the WebSocket connection.
        
        Args:
            message: Message data to send
        
        Raises:
            ConnectionError: If the connection is not established
        """
        if not self.connection or not self.connection.connected:
            raise ConnectionError("Not connected to server")
        
        try:
            await self.connection.send_json(message)
            logger.debug(f"Sent message: {json.dumps(message)[:100]}...")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise ConnectionError(f"Failed to send message: {str(e)}")
    
    def send_generated_text(self, text: str, is_generation_end: bool = False, loop: asyncio.AbstractEventLoop = None) -> None:
        """Send generated text to the server.
        
        Args:
            text: The generated text
            is_generation_end: Whether this is the end of generation
            loop: Event loop to use for coroutine execution (uses current loop if None)
        """
        message = {
            "type": "generated_text",
            "content": {
                "text": text,
                "is_generation_end": is_generation_end
            }
        }
        
        if loop:
            asyncio.run_coroutine_threadsafe(self._send_message(message), loop)
        else:
            asyncio.create_task(self._send_message(message))
    
    def send_custom_ui_element(self, ui_type: str, data: Dict[str, Any], loop: asyncio.AbstractEventLoop = None) -> None:
        """Send a custom UI element to the server.
        
        Args:
            ui_type: Type of UI element (e.g., 'mcq_question')
            data: Element-specific data
            loop: Event loop to use for coroutine execution (uses current loop if None)
        """
        message = {
            "type": "custom_ui_element",
            "content": {
                "type": ui_type,
                "data": data
            }
        }
        
        if loop:
            asyncio.run_coroutine_threadsafe(self._send_message(message), loop)
        else:
            asyncio.create_task(self._send_message(message))
    
    def send_mcq_question(self, question_id: str, question: str, options: List[str],
                         loop: asyncio.AbstractEventLoop = None, image_path: Optional[str] = None) -> None:
        """Send an MCQ question as a custom UI element.
        
        Args:
            question_id: Unique identifier for the question
            question: The question text
            options: List of answer options
            loop: Event loop to use for coroutine execution (uses current loop if None)
            image_path: Optional path to an image to display with the question
        """
        data = {
            "id": question_id,
            "question": question,
            "options": options
        }
        
        if image_path:
            data["image_path"] = image_path
            
        self.send_custom_ui_element("mcq_question", data, loop)
    
    def send_notification(self, message: str, level: str = "info", duration: int = 8000,
                         loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """Send a notification to all users in the meeting.
        
        Args:
            message: The notification message to display
            level: The notification level (info, warning, error, success)
            duration: How long the notification should display (in milliseconds)
            loop: Event loop to run the coroutine in
        """
        data = {
            "message": message,
            "level": level,
            "duration": duration
        }
        
        self.send_custom_ui_element("notification_element", data, loop)

