import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, TypeVar, Type

from .models.outbound import (
    BaseResponse,
    GeneratedTextMessage,
    GeneratedTextContent,
    CustomUIElementMessage,
    MCQQuestionElement,
    MCQQuestionData,
    NotificationElement,
    NotificationData,
    ErrorResponse,
)

from .errors import ConnectionError

logger = logging.getLogger(__name__)

# Type variable for BaseResponse subclasses
T = TypeVar('T', bound=BaseResponse)


class MessageSender:
    """Manages sending messages to the server."""

    def __init__(self, connection):
        """Initialize the message sender.

        Args:
            connection: WebSocketConnection instance
        """
        self.connection = connection
    
    def _prepare_message(self, message_class: Type[T], **kwargs) -> T:
        """Prepare a message with standard fields.
        
        Args:
            message_class: The message class to instantiate
            **kwargs: Additional fields for the message
            
        Returns:
            An instance of the message class
        """
        return message_class(
            **kwargs
        )

    async def _send_message(self, message: Any) -> None:
        """Send a message over the WebSocket connection.

        Args:
            message: Message object to send (will be converted to dict)

        Raises:
            ConnectionError: If the message cannot be sent
        """
        try:
            # Convert Pydantic model to dict if it's a model
            if hasattr(message, "model_dump"):
                message_dict = message.model_dump()
            else:
                message_dict = message

            await self.connection.send_json(message_dict)
            logger.debug(f"Sent message: {json.dumps(message_dict)[:100]}...")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise ConnectionError(f"Failed to send message: {str(e)}")

    def send_generated_text(
        self,
        text: str,
        is_generation_end: bool = False,
        loop: asyncio.AbstractEventLoop = None,
    ) -> None:
        """Send generated text to the server.

        Args:
            text: The generated text
            is_generation_end: Whether this is the end of generation
            loop: Event loop to use for coroutine execution (uses current loop if None)
        """
        content = GeneratedTextContent(text=text, is_generation_end=is_generation_end)
        message = self._prepare_message(GeneratedTextMessage, content=content)

        if loop:
            asyncio.run_coroutine_threadsafe(self._send_message(message), loop)
        else:
            asyncio.create_task(self._send_message(message))

    def send_custom_ui_element(
        self, ui_type: str, data: Dict[str, Any], loop: asyncio.AbstractEventLoop = None
    ) -> None:
        """Send a custom UI element to the server.

        Args:
            ui_type: Type of UI element
            data: Data specific to the UI element
            loop: Event loop to use for coroutine execution (uses current loop if None)
        """
        # Create a generic custom UI element
        custom_element = {"type": ui_type, "data": data}
        message = self._prepare_message(CustomUIElementMessage, content=custom_element)

        if loop:
            asyncio.run_coroutine_threadsafe(self._send_message(message), loop)
        else:
            asyncio.create_task(self._send_message(message))

    def send_mcq_question(
        self,
        question_id: str,
        question: str,
        options: List[str],
        loop: asyncio.AbstractEventLoop = None,
        image_path: Optional[str] = None,
    ) -> None:
        """Send an MCQ question as a custom UI element.

        Args:
            question_id: Unique identifier for the question
            question: The question text
            options: List of option texts
            loop: Event loop to run the coroutine in
            image_path: Optional path to an image to display with the question
        """
        # Create a proper MCQ question element
        mcq_data = MCQQuestionData(
            id=question_id, question=question, options=options, image_path=image_path
        )
        mcq_element = MCQQuestionElement(type="mcq_question", data=mcq_data)
        message = self._prepare_message(CustomUIElementMessage, content=mcq_element)

        if loop:
            asyncio.run_coroutine_threadsafe(self._send_message(message), loop)
        else:
            asyncio.create_task(self._send_message(message))

    def send_notification(
        self,
        message: str,
        level: str = "info",
        duration: int = 8000,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send a notification to be displayed in the UI.

        Args:
            message: The notification message
            level: Notification level (info, warning, error, success)
            duration: Duration to show the notification in milliseconds
            loop: Event loop to run the coroutine in
        """
        notification_data = NotificationData(
            message=message, level=level, duration=duration
        )
        notification_element = NotificationElement(
            type="notification_element", data=notification_data
        )
        msg = self._prepare_message(CustomUIElementMessage, content=notification_element)

        if loop:
            asyncio.run_coroutine_threadsafe(self._send_message(msg), loop)
        else:
            asyncio.create_task(self._send_message(msg))
            
    def send_error(
        self,
        error_message: str,
        error_code: Optional[str] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send an error message to the server.
        
        Args:
            error_message: The error message
            error_code: Optional error code
            loop: Event loop to run the coroutine in
        """
        message = self._prepare_message(ErrorResponse, error=error_message, error_code=error_code)
        
        if loop:
            asyncio.run_coroutine_threadsafe(self._send_message(message), loop)
        else:
            asyncio.create_task(self._send_message(message))
