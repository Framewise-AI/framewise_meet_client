# Update imports to use inbound module
from ..models.inbound import (
    JoinMessage,
    ExitMessage,
    TranscriptMessage,
    CustomUIElementResponse,
    ConnectionRejectedMessage,
    InvokeMessage
)

from .base_handler import EventHandler, register_event_handler
from .transcript_handler import TranscriptHandler
from .join_handler import JoinHandler
from .exit_handler import ExitHandler
from .custom_ui_handler import CustomUIHandler
from .invoke_handler import InvokeHandler
from .connection_rejected_handler import ConnectionRejectedHandler

# Event type constants
TRANSCRIPT_EVENT = "transcript"
JOIN_EVENT = "on_join"
EXIT_EVENT = "on_exit"
CUSTOM_UI_EVENT = "custom_ui_element_response"
INVOKE_EVENT = "invoke"
CONNECTION_REJECTED_EVENT = "connection_rejected"
CUSTOM_UI_ELEMENT_RESPONSE_EVENT = "custom_ui_element_response"
# UI Element Response subtypes
MCQ_QUESTION_EVENT = "mcq_question"
PLACES_AUTOCOMPLETE_EVENT = "places_autocomplete"
UPLOAD_FILE_EVENT = "upload_file"
TEXTINPUT_EVENT = "textinput"
CONSENT_FORM_EVENT = "consent_form"
CALENDLY_EVENT = "calendly"

# Mapping of event types to handler classes
EVENT_HANDLERS = {
    TRANSCRIPT_EVENT: TranscriptHandler,
    JOIN_EVENT: JoinHandler,
    EXIT_EVENT: ExitHandler,
    CUSTOM_UI_EVENT: CustomUIHandler,
    INVOKE_EVENT: InvokeHandler,
    CONNECTION_REJECTED_EVENT: ConnectionRejectedHandler,
    CUSTOM_UI_ELEMENT_RESPONSE_EVENT: CustomUIHandler,  # Corrected to reference the handler class
    # UI Element Response subtypes - reuse the CustomUIHandler
    MCQ_QUESTION_EVENT: CustomUIHandler,
    PLACES_AUTOCOMPLETE_EVENT: CustomUIHandler,
    UPLOAD_FILE_EVENT: CustomUIHandler,
    TEXTINPUT_EVENT: CustomUIHandler,
    CONSENT_FORM_EVENT: CustomUIHandler,
    CALENDLY_EVENT: CustomUIHandler,
}

__all__ = [
    "EventHandler",
    "register_event_handler",
    "TranscriptHandler",
    "JoinHandler",
    "ExitHandler",
    "CustomUIHandler",
    "InvokeHandler",
    "ConnectionRejectedHandler",
    "TRANSCRIPT_EVENT",
    "JOIN_EVENT",
    "EXIT_EVENT",
    "CUSTOM_UI_EVENT",
    "INVOKE_EVENT",
    "CONNECTION_REJECTED_EVENT",
    "CUSTOM_UI_ELEMENT_RESPONSE_EVENT",
    "MCQ_QUESTION_EVENT",
    "PLACES_AUTOCOMPLETE_EVENT",
    "UPLOAD_FILE_EVENT",
    "TEXTINPUT_EVENT",
    "CONSENT_FORM_EVENT",
    "CALENDLY_EVENT",
    "EVENT_HANDLERS",
]
