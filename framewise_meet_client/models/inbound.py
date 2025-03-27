"""Inbound message models for the Framewise Meet client.

This module contains all message types that are received from the server.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


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


class MCQSelectionEvent(BaseModel):
    """Multiple-choice question selection event data."""

    question_id: str = Field(..., description="ID of the question")
    selected_option_id: str = Field(..., description="ID of the selected option")
    participant_id: str = Field(
        ..., description="ID of the participant who made the selection"
    )


class CustomUIEvent(BaseModel):
    """Custom UI event data."""

    element_type: str = Field(..., description="Type of the UI element")
    element_id: str = Field(..., description="ID of the UI element")
    action: str = Field(..., description="Action performed on the UI element")
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Additional data for the event"
    )


class ConnectionRejectedEvent(BaseModel):
    """Connection rejected event data."""

    reason: str = Field(..., description="Reason for the rejection")
    error_code: Optional[str] = Field(None, description="Error code")



class TranscriptMessage(BaseModel):
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


class InvokeMessage(BaseModel):
    """Invoke message received from the server."""

    type: Literal["invoke"] = "invoke"
    content: InvokeContent = Field(..., description="Content of the invoke message")


class JoinMessage(BaseModel):
    """Join message received from the server."""

    type: Literal["on_join"] = "on_join"
    content: JoinEvent = Field(..., description="Content of the join message")


class ExitMessage(BaseModel):
    """Exit message received from the server."""

    type: Literal["on_exit"] = "on_exit"
    content: ExitEvent = Field(..., description="Content of the exit message")


class MCQSelectionMessage(BaseModel):
    """MCQ selection message received from the server."""

    type: Literal["mcq_selection"] = "mcq_selection"
    content: MCQSelectionEvent = Field(
        ..., description="Content of the MCQ selection message"
    )


class CustomUIElementResponse(BaseModel):
    """Custom UI message received from the server."""

    type: Literal["custom_ui"] = "custom_ui_element_response"
    content: CustomUIEvent = Field(..., description="Content of the custom UI message")


class ConnectionRejectedMessage(BaseModel):
    """Connection rejected message received from the server."""

    type: Literal["connection_rejected"] = "connection_rejected"
    content: ConnectionRejectedEvent = Field(
        ..., description="Content of the connection rejected message"
    )
