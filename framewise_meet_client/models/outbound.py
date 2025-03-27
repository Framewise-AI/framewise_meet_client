"""Outbound message models for the Framewise Meet client.

This module contains all message types that are sent to the server.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field



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


class GeneratedTextMessage(BaseModel):
    """Response with generated text."""

    type: Literal["generated_text"] = "generated_text"
    content: GeneratedTextContent = Field(
        ..., description="Content of the generated text"
    )


class MCQMessage(BaseModel):
    """Response with a multiple-choice question."""

    type: Literal["mcq"] = "mcq"
    content: MCQContent = Field(..., description="Content of the MCQ")


class CustomUIMessage(BaseModel):
    """Response with custom UI elements."""

    type: Literal["custom_ui"] = "custom_ui"
    content: CustomUIContent = Field(..., description="Content of the custom UI")


class ErrorResponse(BaseModel):
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

    id: str = Field(..., description="Notification identifier")
    level: str = Field(
        "info", description="Notification level (info, warning, error, success)"
    )
    text: str = Field(..., description="notification text")
    duration: int = Field(8000, description="Duration in milliseconds")
    color: Optional[str] = Field(None, description="Custom color for the notification")


class NotificationElement(BaseModel):
    """Notification UI element."""

    type: Literal["notification_element"] = "notification_element"
    data: NotificationData = Field(..., description="Notification data")


class PlacesAutocompleteData(BaseModel):
    """Data for a places autocomplete UI element.

    This element allows users to search for and select geographic locations using
    an autocomplete feature, typically powered by a mapping service.
    """

    id: str = Field(..., description="Element identifier")
    text: str = Field(..., description="Prompt text")
    placeholder: Optional[str] = Field("Enter location", description="Placeholder text")


class PlacesAutocompleteElement(BaseModel):
    """Places autocomplete UI element.

    Container for the places autocomplete data that defines the element type.
    """

    type: Literal["places_autocomplete"] = "places_autocomplete"
    data: PlacesAutocompleteData = Field(..., description="Places autocomplete data")


class UploadFileData(BaseModel):
    """Data for a file upload UI element.

    This element provides a file picker interface for users to upload files,
    with optional restrictions on file types and sizes.
    """

    id: str = Field(..., description="Element identifier")
    text: str = Field(..., description="Prompt text")
    allowed_types: Optional[List[str]] = Field(None, description="Allowed file types")
    maxSizeMB: Optional[int] = Field(None, description="Maximum file size in MB")


class UploadFileElement(BaseModel):
    """File upload UI element.

    Container for the file upload data that defines the element type.
    """

    type: Literal["upload_file"] = "upload_file"
    data: UploadFileData = Field(..., description="File upload data")


class TextInputData(BaseModel):
    """Data for a text input UI element.

    This element allows users to input text, with options for single or multiline input.
    """

    id: str = Field(..., description="Element identifier")
    prompt: str = Field(..., description="Prompt text")
    placeholder: Optional[str] = Field("", description="Placeholder text")
    multiline: Optional[bool] = Field(
        False, description="Whether to use multiline input"
    )


class TextInputElement(BaseModel):
    """Text input UI element.

    Container for the text input data that defines the element type.
    """

    type: Literal["textinput"] = "textinput"
    data: TextInputData = Field(..., description="Text input data")


class ConsentFormData(BaseModel):
    """Data for a consent form UI element.

    This element presents users with a consent form that requires confirmation,
    typically used for terms of service or privacy policy acceptance.
    """

    id: str = Field(..., description="Element identifier")
    text: str = Field(..., description="Consent form text")
    required: Optional[bool] = Field(True, description="Whether consent is required")
    checkboxLabel: Optional[str] = Field(
        "I agree", description="Label for the checkbox"
    )
    submitLabel: Optional[str] = Field(
        "Submit", description="Label for the submit button"
    )


class ConsentFormElement(BaseModel):
    """Consent form UI element.

    Container for the consent form data that defines the element type.
    """

    type: Literal["consent_form"] = "consent_form"
    data: ConsentFormData = Field(..., description="Consent form data")


class CalendlyData(BaseModel):
    """Data for a Calendly scheduling UI element.

    This element embeds a Calendly scheduling interface for booking appointments or meetings.
    """

    id: str = Field(..., description="Element identifier")
    url: str = Field(..., description="Calendly URL")
    title: Optional[str] = Field("Schedule a meeting", description="Title text")
    subtitle: Optional[str] = Field(None, description="Subtitle text")


class CalendlyElement(BaseModel):
    """Calendly scheduling UI element.

    Container for the Calendly scheduling data that defines the element type.
    """

    type: Literal["calendly"] = "calendly"
    data: CalendlyData = Field(..., description="Calendly data")


# Update the CustomUIElementMessage to include all the new element types
class CustomUIElementMessage(BaseModel):
    """Message for sending a custom UI element."""

    type: Literal["custom_ui_element"] = "custom_ui_element"
    content: Union[
        MCQQuestionElement,
        NotificationElement,
        PlacesAutocompleteElement,
        UploadFileElement,
        TextInputElement,
        ConsentFormElement,
        CalendlyElement,
        CustomUIElement,
    ] = Field(..., description="Custom UI element")


# Add response handler class for custom UI element responses
class UIElementResponseHandler(BaseModel):
    """Base class for handling custom UI element responses.

    This class defines the structure for handlers that respond to UI element interactions.
    """

    type: Literal["ui_element_response_handler"] = "ui_element_response_handler"
    element_type: str = Field(..., description="Type of UI element to handle")
    element_id: str = Field(..., description="ID of the UI element to handle")


class ElementResponseSubscription(BaseModel):
    """Response subscribing to custom UI element responses.

    This class defines which element types to listen for and receive responses from.
    """

    type: Literal["subscribe_element_responses"] = "subscribe_element_responses"
    element_types: List[str] = Field(
        ..., description="Types of elements to subscribe to"
    )
    handler_id: str = Field(..., description="ID of the handler for responses")
