import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, TypeVar, Type, Union
from pydantic import BaseModel

from .models.outbound import (
    GeneratedTextMessage,
    GeneratedTextContent,
    CustomUIElementMessage,
    MCQQuestionElement,
    MCQQuestionData,
    NotificationElement,
    NotificationData,
    PlacesAutocompleteElement,
    PlacesAutocompleteData,
    UploadFileElement,
    UploadFileData,
    TextInputElement,
    TextInputData,
    ConsentFormElement,
    ConsentFormData,
    CalendlyElement,
    CalendlyData,
    ErrorResponse,
)

from .errors import ConnectionError

logger = logging.getLogger(__name__)


T = TypeVar("T", bound=BaseModel)


class MessageSender:
    """Manages sending messages to the server."""

    def __init__(self, connection):
        """Initialize the message sender.

        Args:
            connection: WebSocketConnection instance
        """
        self.connection = connection

    async def _send_model(self, model: BaseModel) -> None:
        """Send a Pydantic model to the server.

        Args:
            model: Pydantic model to send
        """
        if not self.connection.connected:
            logger.warning("Cannot send message: Connection is not established")
            return

        try:
            # Convert model to dict and send
            message_dict = model.model_dump()
            await self.connection.send(message_dict)
            logger.debug(f"Message sent: {message_dict.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

    def send_generated_text(
        self,
        text: str,
        is_generation_end: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send generated text to the server."""
        # Create the model with content
        content = GeneratedTextContent(text=text, is_generation_end=is_generation_end)
        message = GeneratedTextMessage(content=content)

        # Send the message
        if loop:
            asyncio.run_coroutine_threadsafe(self._send_model(message), loop)
        else:
            asyncio.create_task(self._send_model(message))

    def send_custom_ui_element(
        self,
        ui_element: Union[MCQQuestionElement, NotificationElement, PlacesAutocompleteElement,
                          UploadFileElement, TextInputElement, ConsentFormElement, CalendlyElement],
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send a custom UI element to the server using proper Pydantic models.

        Args:
            ui_element: A strongly-typed Pydantic model for the UI element
            loop: Event loop to use for coroutine execution (uses current loop if None)
        """
        # Create the message with the element
        message = CustomUIElementMessage(content=ui_element)

        # Send the message
        if loop:
            asyncio.run_coroutine_threadsafe(self._send_model(message), loop)
        else:
            asyncio.create_task(self._send_model(message))

    def send_mcq_question(
        self,
        question_id: str,
        question: str,
        options: List[str],
        image_path: Optional[str] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send an MCQ question as a custom UI element."""
        # Create the model with properly typed data
        mcq_data = MCQQuestionData(
            id=question_id,
            question=question,
            options=options,
            image_path=image_path
        )
        
        # Create the element model
        mcq_element = MCQQuestionElement(type="mcq_question", data=mcq_data)
        
        # Send as custom UI element
        self.send_custom_ui_element(mcq_element, loop)

    def send_notification(
        self,
        notification_id: str,
        text: str,
        level: str = "info",
        duration: int = 8000,
        color: Optional[str] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send a notification as a custom UI element."""
        # Create the model with properly typed data
        notification_data = NotificationData(
            id=notification_id,
            text=text,
            level=level, 
            duration=duration,
            color=color
        )
        
        # Create the element model
        notification_element = NotificationElement(
            type="notification_element", 
            data=notification_data
        )
        
        # Send as custom UI element
        self.send_custom_ui_element(notification_element, loop)

    def send_places_autocomplete(
        self,
        element_id: str,
        text: str,
        placeholder: str = "Enter location",
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send a places autocomplete field as a custom UI element."""
        # Create the model with properly typed data
        places_data = PlacesAutocompleteData(
            id=element_id,
            text=text,
            placeholder=placeholder
        )
        
        # Create the element model
        places_element = PlacesAutocompleteElement(
            type="places_autocomplete", 
            data=places_data
        )
        
        # Send as custom UI element
        self.send_custom_ui_element(places_element, loop)

    def send_upload_file(
        self,
        element_id: str,
        text: str,
        allowed_types: Optional[List[str]] = None,
        max_size_mb: Optional[int] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send a file upload element as a custom UI element."""
        # Create the model with properly typed data
        upload_data = UploadFileData(
            id=element_id,
            text=text,
            allowed_types=allowed_types,
            maxSizeMB=max_size_mb
        )
        
        # Create the element model
        upload_element = UploadFileElement(
            type="upload_file", 
            data=upload_data
        )
        
        # Send as custom UI element
        self.send_custom_ui_element(upload_element, loop)

    def send_text_input(
        self,
        element_id: str,
        prompt: str,
        placeholder: str = "",
        multiline: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send a text input element as a custom UI element."""
        # Create the model with properly typed data
        text_input_data = TextInputData(
            id=element_id,
            prompt=prompt,
            placeholder=placeholder,
            multiline=multiline
        )
        
        # Create the element model
        text_input_element = TextInputElement(
            type="textinput", 
            data=text_input_data
        )
        
        # Send as custom UI element
        self.send_custom_ui_element(text_input_element, loop)

    def send_consent_form(
        self,
        element_id: str,
        text: str,
        checkbox_label: str = "I agree",
        submit_label: str = "Submit",
        required: bool = True,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send a consent form element as a custom UI element."""
        # Create the model with properly typed data
        consent_form_data = ConsentFormData(
            id=element_id,
            text=text,
            checkboxLabel=checkbox_label,
            submitLabel=submit_label,
            required=required
        )
        
        # Create the element model
        consent_form_element = ConsentFormElement(
            type="consent_form", 
            data=consent_form_data
        )
        
        # Send as custom UI element
        self.send_custom_ui_element(consent_form_element, loop)

    def send_calendly(
        self,
        element_id: str,
        url: str,
        title: str = "Schedule a meeting",
        subtitle: Optional[str] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send a Calendly scheduling element as a custom UI element."""
        # Create the model with properly typed data
        calendly_data = CalendlyData(
            id=element_id,
            url=url,
            title=title,
            subtitle=subtitle
        )
        
        # Create the element model
        calendly_element = CalendlyElement(
            type="calendly", 
            data=calendly_data
        )
        
        # Send as custom UI element
        self.send_custom_ui_element(calendly_element, loop)

    def send_error(
        self,
        error_message: str,
        error_code: Optional[str] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Send an error message to the server."""
        # Create the error message
        message = ErrorResponse(error=error_message, error_code=error_code)

        # Send the message
        if loop:
            asyncio.run_coroutine_threadsafe(self._send_model(message), loop)
        else:
            asyncio.create_task(self._send_model(message))
