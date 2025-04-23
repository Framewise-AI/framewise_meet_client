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

from .models.inbound import (
    CustomUIElementResponse,
    CustomUIContent,
    MCQQuestionResponseData,
    PlacesAutocompleteResponseData,
    UploadFileResponseData,
    TextInputResponseData,
    ConsentFormResponseData,
    CalendlyResponseData,
)

from .errors import ConnectionError

logger = logging.getLogger(__name__)


T = TypeVar("T", bound=BaseModel)


class MessageSender:
    """
    Manages sending various types of messages to the Framewise backend server.
    
    The MessageSender provides an abstracted interface for sending strongly-typed
    messages to the Framewise backend through a WebSocket connection. It handles:
    
    1. Pydantic model serialization for type safety
    2. Different types of UI elements (MCQ, notifications, text inputs, etc.)
    3. Generated text responses with streaming support
    4. Error reporting
    
    Each message type has a dedicated method with appropriate parameters,
    making it easy to send correctly formatted messages without needing to
    understand the underlying message format details.
    
    This class is used internally by the App class, which exposes these methods
    directly for convenience.
    """

    def __init__(self, connection):
        """
        Initialize the message sender with a WebSocket connection.
        
        Args:
            connection: WebSocketConnection instance used to send messages
                       to the Framewise backend.
        """
        self.connection = connection

    async def _send_model(self, model: BaseModel) -> None:
        """
        Send a Pydantic model to the server as a serialized message.
        
        This internal method handles the serialization of Pydantic models
        and sends them through the WebSocket connection. It includes error
        handling and logging.
        
        Args:
            model: Pydantic model to serialize and send.
        """
        if not self.connection.connected:
            logger.warning("Cannot send message: Connection is not established")
            return

        try:
            # Convert model to dict and send
            message_dict = model.model_dump()
            await self.connection.send(message_dict)
            logger.debug(message_dict)
            logger.debug(f"Message sent: {message_dict.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

    async def _send_message(self, message: Dict[str, Any]) -> None:
        """
        Send a dictionary message to the server.
        
        This is a lower-level method that sends raw dictionary messages
        through the WebSocket connection. It includes detailed logging
        and error handling.
        
        Args:
            message: The message dictionary to send.

        Raises:
            ConnectionError: If the connection is not established.
        """
        if not self.connection or not self.connection.connected:
            raise ConnectionError("Not connected to server")

        try:
            # Add detailed message format logging
            logger.debug(f"Sending message format: {json.dumps(message, indent=2)}")
            await self.connection.send_json(message)
            logger.debug(f"Sent message: {json.dumps(message)[:100]}...")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise ConnectionError(f"Failed to send message: {str(e)}")

    async def _handle_ui_response(self, response_data: Dict[str, Any]) -> Any:
        """
        Process UI element response data into appropriate typed models.
        
        This method parses raw UI response data into the appropriate
        strongly-typed Pydantic model based on the UI element type.
        
        Args:
            response_data: Raw response data from the server.
            
        Returns:
            Properly typed UI element response data as a Pydantic model,
            or the raw data if parsing fails or the element type is unknown.
        """
        try:
            # Parse the response into the correct model
            response = CustomUIElementResponse.model_validate(response_data)
            
            # Log the response type for debugging
            logger.debug(f"Received UI response for element type: {response.content.type}")
            
            # Return the properly typed data based on the element type
            element_type = response.content.type
            data = response.content.data
            
            if element_type == "mcq_question":
                return MCQQuestionResponseData(**data)
            elif element_type == "places_autocomplete":
                return PlacesAutocompleteResponseData(**data)
            elif element_type == "upload_file":
                return UploadFileResponseData(**data)
            elif element_type == "textinput":
                return TextInputResponseData(**data)
            elif element_type == "consent_form":
                return ConsentFormResponseData(**data)
            elif element_type == "calendly":
                return CalendlyResponseData(**data)
                
            # If we don't recognize the type, return the raw data
            return data
            
        except Exception as e:
            logger.error(f"Error processing UI element response: {str(e)}")
            return response_data

    def send_generated_text(
        self,
        text: str,
        is_generation_end: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """
        Send generated text to the client through the Framewise backend.
        
        This method allows sending text responses to the client, with support
        for streaming generation. When streaming, multiple messages can be sent
        with is_generation_end=False, followed by a final message with
        is_generation_end=True to indicate the end of the generation.
        
        Args:
            text: The text content to send.
            is_generation_end: Boolean flag indicating whether this is the last
                             chunk of a text generation sequence. If True, the
                             client UI will stop displaying a loading indicator.
            loop: Optional event loop to use for sending the message. If None,
                 uses the current event loop.
        
        Example:
            ```python
            # For streaming text generation:
            sender.send_generated_text("Hello, ", is_generation_end=False)
            sender.send_generated_text("how are ", is_generation_end=False)
            sender.send_generated_text("you today?", is_generation_end=True)
            
            # For non-streaming:
            sender.send_generated_text("Hello, how are you today?", is_generation_end=True)
            ```
        """
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
        """
        Send a custom UI element to the client through the Framewise backend.
        
        This is a general-purpose method for sending any supported UI element type.
        It's used internally by the specific UI element methods, but can also be
        used directly with custom Pydantic models for advanced use cases.
        
        Args:
            ui_element: A strongly-typed Pydantic model for the UI element to send.
                      Must be one of the supported UI element types.
            loop: Optional event loop to use for sending the message. If None,
                 uses the current event loop.
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
        """
        Send a multiple-choice question to the client.
        
        This method creates and sends an interactive multiple-choice question
        that the user can respond to. Each question has a unique ID for tracking
        responses, a question text, and a list of options.
        
        Args:
            question_id: Unique identifier for the question, used to match responses.
            question: The question text to display to the user.
            options: List of option strings that the user can select from.
            image_path: Optional URL to an image to display with the question.
            loop: Optional event loop to use for sending the message.
        
        Example:
            ```python
            sender.send_mcq_question(
                question_id="q1",
                question="What's your favorite color?",
                options=["Red", "Green", "Blue", "Yellow"]
            )
            ```
        """
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
        level: str = "success",  # Changed default from "info" to "success"
        duration: int = 8000,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """
        Send a notification message to the client.
        
        This method displays a temporary notification toast in the client UI,
        useful for alerts, confirmations, or status updates.
        
        Args:
            notification_id: Unique identifier for the notification.
            text: The notification message text to display.
            level: The notification severity level, one of:
                  - "success" (green)
                  - "info" (blue)
                  - "warning" (yellow)
                  - "error" (red)
            duration: How long the notification should display in milliseconds.
            loop: Optional event loop to use for sending the message.
            
        Example:
            ```python
            sender.send_notification(
                notification_id="note1",
                text="Your request has been processed successfully!",
                level="success",
                duration=5000  # 5 seconds
            )
            ```
        """
        # Create the model with properly typed data
        notification_data = NotificationData(
            id=notification_id,
            message=text,
            level=level, 
            duration=duration
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
        """
        Send a places autocomplete input field to the client.
        
        This method creates and sends an interactive location input field with
        Google Places Autocomplete functionality. It allows users to easily
        enter and select locations from Google's database.
        
        Args:
            element_id: Unique identifier for the element, used to match responses.
            text: Instructional text to display above the input field.
            placeholder: Placeholder text to show inside the empty input field.
            loop: Optional event loop to use for sending the message.
        
        Example:
            ```python
            sender.send_places_autocomplete(
                element_id="location1",
                text="Please enter your shipping address:",
                placeholder="Start typing your address..."
            )
            ```
        """
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
        """
        Send a file upload interface to the client.
        
        This method creates and sends a file upload component that allows users
        to upload files from their device. The component can be configured to
        restrict file types and maximum file size.
        
        Args:
            element_id: Unique identifier for the element, used to match responses.
            text: Instructional text to display above the upload button.
            allowed_types: Optional list of MIME types or file extensions to accept.
                         Example: ["image/jpeg", "image/png", ".pdf"]
            max_size_mb: Optional maximum file size in megabytes.
            loop: Optional event loop to use for sending the message.
        
        Example:
            ```python
            sender.send_upload_file(
                element_id="resume_upload",
                text="Please upload your resume:",
                allowed_types=[".pdf", ".docx", "application/pdf"],
                max_size_mb=10
            )
            ```
        """
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
        """
        Send a text input field to the client.
        
        This method creates and sends an interactive text input field that allows
        users to enter free-form text responses. It supports both single-line and
        multiline inputs for different use cases.
        
        Args:
            element_id: Unique identifier for the element, used to match responses.
            prompt: The question or prompt text to display above the input field.
            placeholder: Optional placeholder text to show in the empty input field.
            multiline: Whether to create a multiline text area (True) or a single-line
                     input field (False, default).
            loop: Optional event loop to use for sending the message.
        
        Example:
            ```python
            # Single-line input
            sender.send_text_input(
                element_id="name_input",
                prompt="What is your name?",
                placeholder="Enter your full name"
            )
            
            # Multiline input
            sender.send_text_input(
                element_id="feedback",
                prompt="Please provide your feedback:",
                placeholder="Type your comments here...",
                multiline=True
            )
            ```
        """
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
        """
        Send a consent form to the client.
        
        This method creates and sends an interactive consent form that requires
        user agreement before proceeding. It's useful for terms of service acceptance,
        privacy policy acknowledgments, or other consent-based interactions.
        
        Args:
            element_id: Unique identifier for the element, used to match responses.
            text: The consent text to display to the user, can include HTML formatting.
            checkbox_label: Text to display next to the checkbox (default: "I agree").
            submit_label: Text for the submit button (default: "Submit").
            required: Whether checking the box is required to submit (default: True).
            loop: Optional event loop to use for sending the message.
        
        Example:
            ```python
            sender.send_consent_form(
                element_id="privacy_consent",
                text="I agree to the <a href='https://example.com/privacy'>Privacy Policy</a> and consent to the processing of my personal data.",
                checkbox_label="I understand and agree",
                submit_label="Continue"
            )
            ```
        """
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
        """
        Send a Calendly scheduling widget to the client.
        
        This method creates and sends an embedded Calendly scheduling interface
        that allows users to book appointments or meetings directly within the
        conversation flow.
        
        Args:
            element_id: Unique identifier for the element, used to match responses.
            url: The Calendly scheduling link URL.
            title: Title text to display above the scheduling widget (default: "Schedule a meeting").
            subtitle: Optional subtitle or description text to display.
            loop: Optional event loop to use for sending the message.
        
        Example:
            ```python
            sender.send_calendly(
                element_id="consultation_booking",
                url="https://calendly.com/yourname/30min",
                title="Book Your Free Consultation",
                subtitle="Select a time that works for you. The call will last approximately 30 minutes."
            )
            ```
            
        Note:
            The Calendly URL must be from a valid Calendly account and properly formatted.
        """
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
        """
        Send an error message to the server.
        
        This method reports an error condition to the Framewise backend.
        It can be used to signal problems that might require server-side
        attention or debugging.
        
        Args:
            error_message: Description of the error that occurred.
            error_code: Optional error code or identifier to categorize the error.
            loop: Optional event loop to use for sending the message.
        
        Example:
            ```python
            sender.send_error(
                error_message="Failed to process user input due to invalid format",
                error_code="INPUT_FORMAT_ERROR"
            )
            ```
        """
        # Create the error message
        message = ErrorResponse(error=error_message, error_code=error_code)

        # Send the message
        if loop:
            asyncio.run_coroutine_threadsafe(self._send_model(message), loop)
        else:
            asyncio.create_task(self._send_model(message))
