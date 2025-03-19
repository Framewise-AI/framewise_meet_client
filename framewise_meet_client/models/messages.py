from typing import Optional, List, Dict, Any, Union, ClassVar, Literal
from pydantic import BaseModel, Field, model_validator
import logging

logger = logging.getLogger(__name__)

class BaseMessage(BaseModel):
    """Base class for all message types."""
    message_type: ClassVar[str] = ""
    
    def model_post_init(self, __context):
        """Log successful object creation."""
        logger.debug(f"Created {self.__class__.__name__} object")
        return super().model_post_init(__context) if hasattr(super(), 'model_post_init') else None


class UserInfo(BaseModel):
    """Information about a user in a meeting."""
    meeting_id: str = Field(..., description="The ID of the meeting")


class JoinEvent(BaseModel):
    """Event data for a user joining a meeting."""
    user_joined: UserInfo = Field(..., description="User joining information")


class ExitEvent(BaseModel):
    """Event data for a user exiting a meeting."""
    user_exited: Optional[Union[UserInfo, str, Dict[str, Any]]] = Field(None, description="User exiting information")

class TranscriptContent(BaseModel):
    """Content of a transcript message."""
    text: str = Field("", description="The transcribed text")
    is_final: bool = Field(False, description="Whether this is a final transcript")


class MCQQuestionData(BaseModel):
    """Data for an MCQ question element."""
    id: str = Field(..., description="Unique identifier for the question")
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., description="List of answer options")
    response: Optional[str] = Field(None, description="The user's selected response")


class MCQQuestionResponseData(BaseModel):
    """Data for an MCQ question response."""
    id: str = Field(..., description="Unique identifier for the question")
    question: str = Field(..., description="The question text")
    selectedOption: str = Field(..., description="The selected option text")
    selectedIndex: int = Field(..., description="The selected option index (0-based)")
    options: Optional[List[str]] = Field(None, description="List of answer options")
    

class CustomUIElementData(BaseModel):
    """Data for a custom UI element response."""
    type: str = Field(..., description="Type of UI element")
    data: Union[MCQQuestionResponseData, Dict[str, Any]] = Field(..., description="Element-specific data")
    
    @model_validator(mode='after')
    def validate_data_type(self):
        """Validate that data matches the declared type."""
        return self

class MessagePayload(BaseModel):
    """Generic message payload that can contain any type of content."""
    type: str = Field(..., description="Message type identifier")
    content: Union[JoinEvent, ExitEvent, TranscriptContent, CustomUIElementData, Dict[str, Any]] = Field(
        ..., description="Message content")


# Specific message types
class JoinMessage(BaseMessage):
    """Message for a user joining event."""
    message_type: ClassVar[str] = "on_join"
    type: Literal["on_join"] = "on_join"
    content: JoinEvent


class ExitMessage(BaseMessage):
    """Message for a user exiting event."""
    message_type: ClassVar[str] = "on_exit"
    type: Literal["on_exit"] = "on_exit"
    content: ExitEvent


class TranscriptMessage(BaseMessage):
    """Message for a transcript event."""
    message_type: ClassVar[str] = "transcript"
    type: Literal["transcript"] = "transcript"
    content: TranscriptContent = Field(default_factory=TranscriptContent)
    
    # For backward compatibility
    transcript: Optional[str] = None
    is_final: Optional[bool] = None
    
    @model_validator(mode='after')
    def _normalize_transcript(self):
        """Support old format where transcript and is_final were at the top level."""
        if self.transcript is not None and not self.content.text:
            logger.debug(f"Converting legacy transcript format: '{self.transcript}' to content.text")
            self.content.text = self.transcript
        if self.is_final is not None:
            logger.debug(f"Converting legacy is_final format: {self.is_final} to content.is_final")
            self.content.is_final = self.is_final
        return self


class CustomUIElementMessage(BaseMessage):
    """Message for a custom UI element response."""
    message_type: ClassVar[str] = "custom_ui_element_response" 
    type: Literal["custom_ui_element_response"] = "custom_ui_element_response"
    content: CustomUIElementData


# MCQ-specific models
class MCQSelectionContent(BaseModel):
    """Content of an MCQ selection message."""
    selectedOption: str = Field(..., description="The selected option text")
    selectedIndex: int = Field(..., description="The selected option index (0-based)")
    question: str = Field(...,description="the question name")
    id: Optional[str] = Field(None, description="ID of the related question")
    image_path: Optional[str] = Field(None,description="imae_path")


class MCQSelectionMessage(BaseMessage):
    """Message for an MCQ selection event."""
    message_type: ClassVar[str] = "mcq_selection"
    type: Literal["mcq_selection"] = "mcq_selection"
    content: MCQSelectionContent



class GeneratedTextContent(BaseModel):
    """Content of a generated text message."""
    text: str = Field("", description="The generated text")
    is_generation_end: bool = Field(False, description="Whether this is the end of generation")


class GeneratedTextMessage(BaseMessage):
    """Message for sending generated text."""
    message_type: ClassVar[str] = "generated_text"
    type: Literal["generated_text"] = "generated_text"
    content: GeneratedTextContent


class MCQQuestionSendData(BaseModel):
    """Data for an MCQ question to be sent."""
    id: str = Field(..., description="Unique identifier for the question")
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., description="List of answer options")


class CustomUIElementSendData(BaseModel):
    """Data for a custom UI element to be sent."""
    type: str = Field(..., description="Type of UI element")
    data: Union[MCQQuestionSendData, Dict[str, Any]] = Field(..., description="Element-specific data")


class CustomUIElementSendMessage(BaseMessage):
    """Message for sending a custom UI element."""
    message_type: ClassVar[str] = "custom_ui_element"
    type: Literal["custom_ui_element"] = "custom_ui_element"
    content: CustomUIElementSendData


class ConnectionRejectedContent(BaseModel):
    """Content of a connection rejected message."""
    reason: str = Field("", description="Reason for connection rejection")
    meeting_id: str = Field("", description="Meeting ID for which connection was rejected")


class ConnectionRejectedMessage(BaseMessage):
    """Message for connection rejection."""
    message_type: ClassVar[str] = "connection_rejected"
    type: Literal["connection_rejected"] = "connection_rejected"
    content: ConnectionRejectedContent
