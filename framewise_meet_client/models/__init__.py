"""Models for the Framewise Meet client."""

# Import and re-export inbound message types
from .inbound import (
    TranscriptMessage,
    InvokeMessage,
    JoinMessage,
    ExitMessage,
    MCQSelectionMessage,
    CustomUIElementResponse as InboundCustomUIMessage,  # Fix typo
    ConnectionRejectedMessage,
    TranscriptContent,
    InvokeContent,
    JoinEvent,
    ExitEvent,
    MCQSelectionEvent,
    CustomUIEvent,
    ConnectionRejectedEvent,
)

# Import and re-export outbound message types
from .outbound import (
    GeneratedTextMessage,
    MCQMessage,
    CustomUIMessage as OutboundCustomUIMessage,
    CustomUIElementMessage,
    ErrorResponse,
    GeneratedTextContent,
    MCQContent,
    CustomUIContent,
    MultipleChoiceQuestion,
    MCQOption,
    ButtonElement,
    InputElement,
    CustomUIElement,
    CustomUIButtonElement,
    CustomUIInputElement,
    MCQQuestionData,
    MCQQuestionElement,
    NotificationData,
    NotificationElement,
)

# Export everything with type aliases to avoid confusion
__all__ = [
    # Inbound message base types
    # Inbound message types
    "TranscriptMessage",
    "InvokeMessage",
    "JoinMessage",
    "ExitMessage",
    "MCQSelectionMessage",
    "ConnectionRejectedMessage",
    # Inbound content types
    "TranscriptContent",
    "InvokeContent",
    "JoinEvent",
    "ExitEvent",
    "MCQSelectionEvent",
    "CustomUIEvent",
    "ConnectionRejectedEvent",
    # Outbound message base types,
    # Outbound message types
    "GeneratedTextMessage",
    "MCQMessage",
    "CustomUIElementMessage",
    "ErrorResponse",
    # Outbound content types
    "GeneratedTextContent",
    "MCQContent",
    "CustomUIContent",
    "MultipleChoiceQuestion",
    "MCQOption",
    # UI elements
    "ButtonElement",
    "InputElement",
    "CustomUIElement",
    "CustomUIButtonElement",
    "CustomUIInputElement",
    "MCQQuestionData",
    "MCQQuestionElement",
    "NotificationData",
    "NotificationElement",
    # Aliases to distinguish between inbound and outbound custom UI messages
    "InboundCustomUIMessage",
    "OutboundCustomUIMessage",
]
