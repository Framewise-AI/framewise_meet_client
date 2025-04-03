"""Inbound message models for the Framewise Meet client.

This module contains all message types that are received from the server.
"""

from typing import Any, ClassVar, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

class BaseMessage(BaseModel):
    """Base class for all messages."""
    message_type: ClassVar[str] = "base"
    type: str
    content: Any


class TranscriptContent(BaseModel):
    """Content of a transcript message."""

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
    """Content of an invoke message."""

    function_name: str = Field(..., description="Name of the function to invoke")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the function"
    )


class JoinEvent(BaseModel):
    """Join event data."""

    meeting_id: str = Field(..., description="ID of the meeting")
    participant_id: str = Field(..., description="ID of the participant who joined")
    participant_name: Optional[str] = Field(
        None, description="Name of the participant who joined"
    )
    participant_role: Optional[str] = Field(
        None, description="Role of the participant who joined"
    )


class ExitEvent(BaseModel):
    """Exit event data."""

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
    """Data for an MCQ question response."""
    
    id: str = Field(..., description="ID of the MCQ question")
    question: Optional[str] = Field(None, description="The question text")
    options: Optional[List[str]] = Field(None, description="List of options")
    # Add these fields to match the actual response format
    selectedOption: Optional[str] = Field(None, description="The selected option text")
    selectedIndex: Optional[int] = Field(None, description="The index of the selected option")
    response: Optional[str] = Field(None, description="The selected response (legacy)")


class PlacesAutocompleteResponseData(BaseModel):
    """Data for a places autocomplete response."""
    
    id: str = Field(..., description="ID of the places autocomplete element")
    text: str = Field(..., description="Prompt text")
    address: str = Field(..., description="Selected address")
    placeId: str = Field(..., description="Google Places ID")
    coordinates: Dict[str, float] = Field(..., description="Lat/lng coordinates")


class UploadFileResponseData(BaseModel):
    """Data for a file upload response."""
    
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
