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

# Mapping of event types to handler classes
EVENT_HANDLERS = {
    TRANSCRIPT_EVENT: TranscriptHandler,
    JOIN_EVENT: JoinHandler,
    EXIT_EVENT: ExitHandler,
    CUSTOM_UI_EVENT: CustomUIHandler,
    INVOKE_EVENT: InvokeHandler,
    CONNECTION_REJECTED_EVENT: ConnectionRejectedHandler
}

__all__ = [
    'EventHandler', 'register_event_handler',
    'TranscriptHandler', 'JoinHandler', 'ExitHandler', 
    'CustomUIHandler', 'InvokeHandler',
    'TRANSCRIPT_EVENT', 'JOIN_EVENT', 'EXIT_EVENT',
    'MCQ_SELECTION_EVENT', 'CUSTOM_UI_EVENT', 'INVOKE_EVENT',
    'EVENT_HANDLERS'
]
