"""Outbound message models for the Framewise Meet client.

This module contains all message types that are sent to the server.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base class for all responses sent to the server."""

    message_id: str = Field(..., description="ID of the message")
    meeting_id: str = Field(..., description="ID of the meeting")
    timestamp: str = Field(..., description="Timestamp of the response")


class MCQOption(BaseModel):
    """Option for a multiple-choice question."""

    id: str = Field(..., description="Option identifier")
    text: str = Field(..., description="Option text")


class MultipleChoiceQuestion(BaseModel):
    """Multiple-choice question model."""

    question_id: str = Field(..., description="Question identifier")
    question_text: str = Field(..., description="Question text")
    options: List[MCQOption] = Field(..., description="Available options")


class ButtonElement(BaseModel):
    """Button UI element model."""

    id: str = Field(..., description="Button identifier")
    text: str = Field(..., description="Button text")
    style: Optional[Dict[str, Any]] = Field(
        None, description="Optional styling information"
    )


class InputElement(BaseModel):
    """Input field UI element model."""

    id: str = Field(..., description="Input identifier")
    label: str = Field(..., description="Input label")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    type: str = Field("text", description="Input type (text, number, etc.)")
    default_value: Optional[str] = Field(None, description="Default value")


class CustomUIElement(BaseModel):
    """Base class for custom UI elements."""

    type: str = Field(..., description="Element type")


class CustomUIButtonElement(CustomUIElement):
    """Button UI element."""

    type: Literal["button"] = "button"
    data: ButtonElement = Field(..., description="Button data")


class CustomUIInputElement(CustomUIElement):
    """Input field UI element."""

    type: Literal["input"] = "input"
    data: InputElement = Field(..., description="Input data")


class GeneratedTextContent(BaseModel):
    """Content for generated text response."""

    text: str = Field(..., description="Generated text")
    is_generation_end: bool = Field(
        False, description="Whether this is the end of generation"
    )


class MCQContent(BaseModel):
    """Content for MCQ response."""

    question: MultipleChoiceQuestion = Field(
        ..., description="Multiple choice question"
    )


class CustomUIContent(BaseModel):
    """Content for custom UI response."""

    elements: List[Union[CustomUIButtonElement, CustomUIInputElement]] = Field(
        ..., description="UI elements"
    )


class GeneratedTextMessage(BaseResponse):
    """Response with generated text."""

    type: Literal["generated_text"] = "generated_text"
    content: GeneratedTextContent = Field(
        ..., description="Content of the generated text"
    )


class MCQMessage(BaseResponse):
    """Response with a multiple-choice question."""

    type: Literal["mcq"] = "mcq"
    content: MCQContent = Field(..., description="Content of the MCQ")


class CustomUIMessage(BaseResponse):
    """Response with custom UI elements."""

    type: Literal["custom_ui"] = "custom_ui"
    content: CustomUIContent = Field(..., description="Content of the custom UI")


class ErrorResponse(BaseResponse):
    """Error response."""

    type: Literal["error"] = "error"
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


# New classes for specific custom UI elements


class MCQQuestionData(BaseModel):
    """Data for a multiple-choice question UI element."""

    id: str = Field(..., description="Question identifier")
    question: str = Field(..., description="Question text")
    options: List[str] = Field(..., description="List of option texts")
    image_path: Optional[str] = Field(None, description="Optional path to an image")


class MCQQuestionElement(BaseModel):
    """MCQ question UI element."""

    type: Literal["mcq_question"] = "mcq_question"
    data: MCQQuestionData = Field(..., description="MCQ question data")


class NotificationData(BaseModel):
    """Data for a notification UI element."""

    message: str = Field(..., description="Notification message")
    level: str = Field(
        "info", description="Notification level (info, warning, error, success)"
    )
    duration: int = Field(8000, description="Duration in milliseconds")


class NotificationElement(BaseModel):
    """Notification UI element."""

    type: Literal["notification_element"] = "notification_element"
    data: NotificationData = Field(..., description="Notification data")


class CustomUIElementMessage(BaseResponse):
    """Message for sending a custom UI element."""

    type: Literal["custom_ui_element"] = "custom_ui_element"
    content: Union[MCQQuestionElement, NotificationElement, CustomUIElement] = Field(
        ..., description="Custom UI element"
    )
