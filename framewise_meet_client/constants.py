"""
Constants used throughout the Framewise Meet client library.

This module defines string constants for event types, UI element types,
notification levels, and default connection parameters. Using these constants
ensures consistency across the application and prevents typos in event strings.

Usage example:
    from framewise_meet_client.constants import TRANSCRIPT_EVENT, MCQ_QUESTION_EVENT

    if event_type == TRANSCRIPT_EVENT:
        handle_transcript(message)
"""

# Event types
TRANSCRIPT_EVENT = "transcript"
JOIN_EVENT = "on_join"
EXIT_EVENT = "on_exit"
CUSTOM_UI_EVENT = "custom_ui_element_response"
INVOKE_EVENT = "invoke"
CONNECTION_REJECTED_EVENT = "connection_rejected"
CUSTOM_UI_ELEMENT_RESPONSE_EVENT = "custom_ui_element_response"

# UI Element Types
MCQ_QUESTION_EVENT = "mcq_question"
PLACES_AUTOCOMPLETE_EVENT = "places_autocomplete"
UPLOAD_FILE_EVENT = "upload_file"
TEXTINPUT_EVENT = "textinput"
CONSENT_FORM_EVENT = "consent_form"
CALENDLY_EVENT = "calendly"

# Notification levels
NOTIFICATION_LEVEL_INFO = "info"
NOTIFICATION_LEVEL_WARNING = "warning"
NOTIFICATION_LEVEL_ERROR = "error"
NOTIFICATION_LEVEL_SUCCESS = "success"

# Default values
DEFAULT_NOTIFICATION_DURATION = 8000
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000
