"""
Inbound message models for the Framewise Meet client.

This module contains all message types that are received from the Framewise backend server.
These Pydantic models provide type safety and validation for incoming WebSocket messages,
ensuring that the application can safely process data from the server.

The module implements a hierarchy of message types:
- BaseMessage: The common base class for all message types
- Content models: Specialized data structures for different message payloads
- Specific message types: Complete messages with their content structures

Usage:
    These models are typically used internally by the framework to parse and validate
    incoming WebSocket messages. Application code will receive instances of these models
    in event handler functions.

    ```python
    @app.on_transcript()
    def handle_transcript(message: TranscriptMessage):
        # Access validated content
        transcript_text = message.content.text
        is_final = message.content.is_final
        
        # Process the transcript
        if is_final:
            process_complete_transcript(transcript_text)
    ```
"""

from typing import Any, ClassVar, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

class BaseMessage(BaseModel):
    """
    Base class for all inbound messages from the Framewise backend.
    
    This abstract base class defines the common structure for all messages
    received from the server. Each specific message type inherits from this
    class and implements its own content structure.
    
    Attributes:
        message_type: Class variable indicating the type of message (for internal use).
        type: The type identifier string of the message, used for routing.
        content: The payload of the message, with a structure specific to each message type.
    """
    message_type: ClassVar[str] = "base"
    type: str
    content: Any


class TranscriptContent(BaseModel):
    """
    Content structure for speech-to-text transcript messages.
    
    This model represents the transcript text and its associated metadata,
    including whether it's a final transcript (complete utterance) or an
    interim transcript (partial, still being processed).
    
    Attributes:
        text: The transcribed text content.
        is_final: Flag indicating if this is a complete, final transcript (True)
                or an interim, partial transcript (False).
        confidence: Optional confidence score (0.0-1.0) indicating transcription accuracy.
        language_code: Optional language code (e.g., "en-US") for the transcript.
        alternatives: Optional list of alternative transcriptions with their confidence scores.
        speaker_id: Optional identifier for the speaker, enabling speaker diarization.
    
    Example:
        ```python
        {
            "text": "Hello, how can I help you today?",
            "is_final": True,
            "confidence": 0.95,
            "language_code": "en-US",
            "speaker_id": "speaker_1"
        }
        ```
    """

    text: str = Field(..., description="The transcript text")
    is_final: bool = Field(False, description="Whether this is a final transcript")
    confidence: Optional[float] = Field(
        None, description="Confidence score for the transcript"
    )
    language_code: Optional[str] = Field(
        None, description="Language code for the transcript"
    )
    alternatives: Optional[List[Dict[str, Any]]] = Field(
        None, description="Alternative transcriptions"
    )
    speaker_id: Optional[str] = Field(None, description="ID of the speaker")


class InvokeContent(BaseModel):
    """
    Content structure for function invocation messages.
    
    This model represents a request to call a specific function with arguments,
    typically used for remote procedure calls or agent actions.
    
    Attributes:
        function_name: The name of the function to invoke.
        arguments: Dictionary of argument names to values for the function call.
    
    Example:
        ```python
        {
            "function_name": "search_database",
            "arguments": {
                "query": "framewise documentation",
                "max_results": 10
            }
        }
        ```
    """

    function_name: str = Field(..., description="Name of the function to invoke")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the function"
    )


class JoinEvent(BaseModel):
    """
    Data model for meeting join events.
    
    This model contains information about a participant joining a meeting,
    including their identifiers and optional metadata.
    
    Attributes:
        meeting_id: Unique identifier for the meeting.
        participant_id: Unique identifier for the participant who joined.
        participant_name: Optional display name of the participant.
        participant_role: Optional role of the participant (e.g., "host", "attendee").
    
    Example:
        ```python
        {
            "meeting_id": "meet-abc-123",
            "participant_id": "user-456",
            "participant_name": "John Doe",
            "participant_role": "host"
        }
        ```
    """

    meeting_id: str = Field(..., description="ID of the meeting")
    participant_id: str = Field(..., description="ID of the participant who joined")
    participant_name: Optional[str] = Field(
        None, description="Name of the participant who joined"
    )
    participant_role: Optional[str] = Field(
        None, description="Role of the participant who joined"
    )


class ExitEvent(BaseModel):
    """
    Data model for meeting exit events.
    
    This model contains information about a participant leaving a meeting,
    including their identifiers and optional metadata.
    
    Attributes:
        meeting_id: Unique identifier for the meeting.
        participant_id: Unique identifier for the participant who exited.
        participant_name: Optional display name of the participant.
        participant_role: Optional role of the participant (e.g., "host", "attendee").
    
    Example:
        ```python
        {
            "meeting_id": "meet-abc-123",
            "participant_id": "user-456",
            "participant_name": "John Doe",
            "participant_role": "host"
        }
        ```
    """

    meeting_id: str = Field(..., description="ID of the meeting")
    participant_id: str = Field(..., description="ID of the participant who exited")
    participant_name: Optional[str] = Field(
        None, description="Name of the participant who exited"
    )
    participant_role: Optional[str] = Field(
        None, description="Role of the participant who exited"
    )


# Custom UI element response data models
class MCQQuestionResponseData(BaseModel):
    """
    Data model for multiple-choice question responses.
    
    This model represents the user's selection in response to a multiple-choice
    question, including both the selected option text and its index in the options list.
    
    Attributes:
        id: Unique identifier for the MCQ question.
        question: Optional text of the question (for reference).
        options: Optional list of all available options (for reference).
        selectedOption: The text content of the selected option.
        selectedIndex: The zero-based index of the selected option in the options list.
        response: Legacy field for the selected response text.
    
    Example:
        ```python
        {
            "id": "question-123",
            "question": "What is your favorite color?",
            "options": ["Red", "Green", "Blue", "Yellow"],
            "selectedOption": "Blue",
            "selectedIndex": 2
        }
        ```
    """
    
    id: str = Field(..., description="ID of the MCQ question")
    question: Optional[str] = Field(None, description="The question text")
    options: Optional[List[str]] = Field(None, description="List of options")
    # Add these fields to match the actual response format
    selectedOption: Optional[str] = Field(None, description="The selected option text")
    selectedIndex: Optional[int] = Field(None, description="The index of the selected option")
    response: Optional[str] = Field(None, description="The selected response (legacy)")


class PlacesAutocompleteResponseData(BaseModel):
    """
    Data model for Google Places Autocomplete responses.
    
    This model represents the location selected by a user from the Places
    Autocomplete component, including the formatted address string and
    geographical coordinates.
    
    Attributes:
        id: Unique identifier for the Places Autocomplete element.
        text: Prompt text shown with the component.
        address: The full formatted address string selected by the user.
        placeId: Google Places API place ID for the selected location.
        coordinates: Dictionary with "lat" and "lng" keys for the location coordinates.
    
    Example:
        ```python
        {
            "id": "location-123",
            "text": "Enter your shipping address:",
            "address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
            "placeId": "ChIJj61dQgK6j4AR4GeTYWZsKWw",
            "coordinates": {"lat": 37.422, "lng": -122.084}
        }
        ```
    """
    
    id: str = Field(..., description="ID of the places autocomplete element")
    text: str = Field(..., description="Prompt text")
    address: str = Field(..., description="Selected address")
    placeId: str = Field(..., description="Google Places ID")
    coordinates: Dict[str, float] = Field(..., description="Lat/lng coordinates")


class UploadFileResponseData(BaseModel):
    """
    Data model for file upload responses.
    
    This model represents a file uploaded by the user, including metadata
    about the file and its content encoded as a base64 string.
    
    Attributes:
        id: Unique identifier for the file upload element.
        text: Prompt text shown with the component.
        fileName: Name of the uploaded file including extension.
        fileType: MIME type of the uploaded file (e.g., "application/pdf").
        fileSize: Size of the file in bytes.
        fileData: Base64-encoded content of the uploaded file.
    
    Example:
        ```python
        {
            "id": "resume-upload",
            "text": "Please upload your resume:",
            "fileName": "resume.pdf",
            "fileType": "application/pdf",
            "fileSize": 1048576,
            "fileData": "JVBERi0xLjMK..."  # Base64-encoded PDF data
        }
        ```
        
    Note:
        The fileData field may contain large amounts of base64-encoded data,
        which should be decoded before processing.
    """
    
    id: str = Field(..., description="ID of the upload element")
    text: str = Field(..., description="Prompt text")
    fileName: str = Field(..., description="Name of the uploaded file")
    fileType: str = Field(..., description="MIME type of the uploaded file")
    fileSize: int = Field(..., description="Size of the file in bytes")
    fileData: str = Field(..., description="Base64-encoded file data")


class TextInputResponseData(BaseModel):
    """Data for a text input response."""
    
    id: str = Field(..., description="ID of the text input element")
    prompt: str = Field(..., description="Prompt text")
    text: str = Field(..., description="Entered text")


class ConsentFormResponseData(BaseModel):
    """Data for a consent form response."""
    
    id: str = Field(..., description="ID of the consent form element")
    text: str = Field(..., description="Consent text")
    isChecked: bool = Field(..., description="Whether consent was given")


class CalendlyResponseData(BaseModel):
    """Data for a Calendly response."""
    
    id: str = Field(..., description="ID of the Calendly element")
    scheduledMeeting: Dict[str, Any] = Field(..., description="Meeting details")


class CustomUIContent(BaseModel):
    """Content for a custom UI element response."""
    
    type: str = Field(..., description="Type of UI element")
    data: Union[
        MCQQuestionResponseData,
        PlacesAutocompleteResponseData,
        UploadFileResponseData,
        TextInputResponseData,
        ConsentFormResponseData,
        CalendlyResponseData,
        Dict[str, Any]  # Fallback for unknown types
    ] = Field(..., description="Data for the UI element")


class ConnectionRejectedEvent(BaseModel):
    """Connection rejected event data."""

    reason: str = Field(..., description="Reason for the rejection")
    error_code: Optional[str] = Field(None, description="Error code")


class MCQSelectionEvent(BaseModel):
    """Multiple-choice question selection event data."""

    question_id: str = Field(..., description="ID of the question")
    selected_option_id: str = Field(..., description="ID of the selected option")
    participant_id: str = Field(
        ..., description="ID of the participant who made the selection"
    )


class TranscriptMessage(BaseMessage):
    """Transcript message received from the server."""

    type: Literal["transcript"] = "transcript"
    content: TranscriptContent = Field(
        ..., description="Content of the transcript message"
    )
    # For backwards compatibility
    transcript: Optional[str] = None
    is_final: Optional[bool] = None

    def model_post_init(self, *args, **kwargs):
        """Handle legacy transcript format."""
        if self.transcript is not None:
            self.content.text = self.transcript
        if self.is_final is not None:
            self.content.is_final = self.is_final


class InvokeMessage(BaseMessage):
    """Invoke message received from the server."""

    type: Literal["invoke"] = "invoke"
    content: InvokeContent = Field(..., description="Content of the invoke message")


class JoinMessage(BaseMessage):
    """Join message received from the server."""

    type: Literal["on_join"] = "on_join"
    content: Union[JoinEvent, Dict[str, Any]] = Field(
        ..., description="Content of the join message"
    )

    def model_post_init(self, *args, **kwargs):
        """Handle various join message formats."""
        # Convert dictionary content to a JoinEvent object if needed
        if isinstance(self.content, dict):
            if "user_joined" in self.content:
                user_joined_data = self.content["user_joined"]
                if isinstance(user_joined_data, dict):
                    # Create a UserJoinedInfo object
                    self.content = JoinEvent(
                        user_joined=UserJoinedInfo(**user_joined_data)
                    )


class ExitMessage(BaseMessage):
    """Exit message received from the server."""

    type: Literal["on_exit"] = "on_exit"
    content: ExitEvent = Field(..., description="Content of the exit message")


class MCQSelectionMessage(BaseMessage):
    """MCQ selection message received from the server."""

    type: Literal["mcq_question"] = "mcq_question"
    content: MCQSelectionEvent = Field(
        ..., description="Content of the MCQ selection message"
    )


class CustomUIElementResponse(BaseMessage):
    """Custom UI message received from the server."""

    type: Literal["custom_ui_element_response"] = "custom_ui_element_response"
    content: CustomUIContent = Field(..., description="Content of the custom UI message")


class ConnectionRejectedMessage(BaseMessage):
    """Connection rejected message received from the server."""

    type: Literal["connection_rejected"] = "connection_rejected"
    content: ConnectionRejectedEvent = Field(
        ..., description="Content of the connection rejected message"
    )


class UserInfo(BaseModel):
    """Information about a user in a meeting."""

    meeting_id: Optional[str] = Field(None, description="ID of the meeting")
    participant_id: Optional[str] = Field(None, description="ID of the participant")
    participant_name: Optional[str] = Field(None, description="Name of the participant")
    participant_role: Optional[str] = Field(None, description="Role of the participant")


class UserJoinedInfo(BaseModel):
    """Information about a user that joined a meeting - matches actual server format."""
    
    meeting_id: str = Field(..., description="ID of the meeting")


class JoinEvent(BaseModel):
    """Join event data."""

    meeting_id: Optional[str] = Field(None, description="ID of the meeting")
    participant_id: Optional[str] = Field(None, description="ID of the participant who joined")
    participant_name: Optional[str] = Field(
        None, description="Name of the participant who joined"
    )
    participant_role: Optional[str] = Field(
        None, description="Role of the participant who joined"
    )
    user_joined: Optional[UserJoinedInfo] = Field(
        None, description="User joining information (server format)"
    )
