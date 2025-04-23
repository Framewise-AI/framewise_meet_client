"""
Outbound message models for the Framewise Meet client.

This module defines all Pydantic models for messages sent from the client
to the Framewise backend server. These models ensure that outgoing messages
conform to the expected JSON structures, providing type safety and validation.

Key message categories:
- Simple UI elements (buttons, inputs)
- Custom UI components (MCQ questions, notifications, file uploads, etc.)
- Generated text messages for conversational responses
- Subscription and handler registration messages for UI events

Usage example:
    sender.send_mcq_question(
        question_id="q1",
        question="What is the capital of France?",
        options=["Paris", "Berlin", "Madrid"]
    )

    # Subscribe to responses for MCQ components
    subscription = ElementResponseSubscription(
        element_types=["mcq_question"],
        handler_id="mcq_handler_1"
    )
    sender.send_custom_ui_element(subscription)
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class MCQOption(BaseModel):
    """
    Represents one selectable option in a multiple-choice question.

    Attributes:
        id: Unique identifier for this option.
        text: Display text for this option.

    Example:
        MCQOption(id="opt1", text="Option A")
    """

    id: str = Field(..., description="Option identifier")
    text: str = Field(..., description="Option text")


class MultipleChoiceQuestion(BaseModel):
    """
    Model for a multiple-choice question payload.

    Attributes:
        question_id: Unique identifier for the question.
        question_text: The text prompt of the question.
        options: List of MCQOption instances defining the selectable options.

    Example:
        MultipleChoiceQuestion(
            question_id="q1",
            question_text="Choose a number:",
            options=[MCQOption(id="1", text="One"), MCQOption(id="2", text="Two")]
        )
    """

    question_id: str = Field(..., description="Question identifier")
    question_text: str = Field(..., description="Question text")
    options: List[MCQOption] = Field(..., description="Available options")


class ButtonElement(BaseModel):
    """
    Defines a clickable button UI component.

    Attributes:
        id: Unique identifier for the button.
        text: Label displayed on the button.
        style: Optional dictionary for styling properties (CSS-like).

    Example:
        ButtonElement(id="btn1", text="Submit", style={"color": "blue"})
    """

    id: str = Field(..., description="Button identifier")
    text: str = Field(..., description="Button text")
    style: Optional[Dict[str, Any]] = Field(
        None, description="Optional styling information"
    )


class InputElement(BaseModel):
    """
    Defines a text input UI component.

    Attributes:
        id: Unique identifier for the input field.
        label: Display label for the input.
        placeholder: Placeholder text shown when the field is empty.
        type: Input data type, e.g., "text" or "number".
        default_value: Optional default value pre-filled in the field.

    Example:
        InputElement(
            id="inp1",
            label="Your name",
            placeholder="Enter name",
            type="text"
        )
    """

    id: str = Field(..., description="Input identifier")
    label: str = Field(..., description="Input label")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    type: str = Field("text", description="Input type (text, number, etc.)")
    default_value: Optional[str] = Field(None, description="Default value")


class CustomUIElement(BaseModel):
    """
    Base class for all custom UI elements sent to the client.

    The 'type' field identifies the specific element subtype. Subclasses
    must specify a Literal type to constrain valid values.
    """

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
    """
    Payload for streaming or non-streaming generated text responses.

    Attributes:
        text: The generated text to display.
        is_generation_end: True if this is the final chunk of text.
    """

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
    """
    Message model for sending generated conversational text.

    Fields:
        type: Must be "generated_text".
        content: GeneratedTextContent instance with the text payload.
    """

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
    """
    UI element representing a multiple-choice question to the client.

    Attributes:
        type: Literal "mcq_question".
        data: MCQQuestionData model with question details and options.
    """

    type: Literal["mcq_question"] = "mcq_question"
    data: MCQQuestionData = Field(..., description="MCQ question data")


class NotificationData(BaseModel):
    """Data for a notification UI element."""

    id: str = Field(..., description="Notification identifier")
    level: Literal["info", "warning", "error", "success"] = Field(
        "info", description="Notification level"
    )
    message: str = Field(..., description="Notification message text")
    duration: int = Field(8000, description="Duration in milliseconds")


class NotificationElement(BaseModel):
    """
    UI element for displaying styled notifications or alerts.

    Attributes:
        type: Literal "notification_element".
        data: NotificationData with message text and display options.
    """

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
    """
    UI element for location input with autocomplete functionality.

    Attributes:
        type: Literal "places_autocomplete".
        data: PlacesAutocompleteData with placeholder and prompt.
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
    """
    UI element for allowing users to upload files from their device.

    Attributes:
        type: Literal "upload_file".
        data: UploadFileData specifying file type and size restrictions.
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
    """
    UI element for free-form text entry, single or multiline.

    Attributes:
        type: Literal "textinput".
        data: TextInputData with prompt, placeholder, and multiline flag.
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
    """
    UI element for consent acknowledgments (e.g., terms of service).

    Attributes:
        type: Literal "consent_form".
        data: ConsentFormData with text and checkbox labels.
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
    """
    UI element embedding a Calendly scheduling interface.

    Attributes:
        type: Literal "calendly".
        data: CalendlyData with URL, title, and subtitle.
    """

    type: Literal["calendly"] = "calendly"
    data: CalendlyData = Field(..., description="Calendly data")


# Update the CustomUIElementMessage to include all the new element types
class CustomUIElementMessage(BaseModel):
    """
    Envelope message model for sending any custom UI element.

    Fields:
        type: Literal "custom_ui_element".
        content: One of the recognized CustomUIElement subclasses.
    """

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
    """
    Subscription message for handling client-side UI interactions.

    This message registers a handler for a specific UI element type,
    enabling the backend to route user responses to the correct logic.

    Fields:
        type: Literal "ui_element_response_handler".
        element_type: The UI element type string to handle (e.g., "mcq_question").
        element_id: Identifier of the specific element instance to listen for.
    """

    type: Literal["ui_element_response_handler"] = "ui_element_response_handler"
    element_type: str = Field(..., description="Type of UI element to handle")
    element_id: str = Field(..., description="ID of the UI element to handle")


class ElementResponseSubscription(BaseModel):
    """
    Subscription message to receive user interaction events for multiple elements.

    This message tells the backend which UI element types the client wants
    to subscribe to, and includes a handler ID to correlate responses.

    Fields:
        type: Literal "subscribe_element_responses".
        element_types: List of element type strings to subscribe to.
        handler_id: Unique identifier for the event handler on the backend.
    """

    type: Literal["subscribe_element_responses"] = "subscribe_element_responses"
    element_types: List[str] = Field(
        ..., description="Types of elements to subscribe to"
    )
    handler_id: str = Field(..., description="ID of the handler for responses")
