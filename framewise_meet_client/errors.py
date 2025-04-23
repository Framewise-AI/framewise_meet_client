"""
Custom exception hierarchy for the Framewise Meet client library.

Defines base error classes that represent various failure scenarios
in the client framework, such as connection errors, authentication
failures, and event handler errors.

Usage example:
    raise ConnectionError("WebSocket disconnected unexpectedly")
"""

class AppError(Exception):
    """
    Base exception class for all application-level errors in the Framewise Meet client.
    """
    pass

class AppNotRunningError(AppError):
    """
    Exception raised when an operation requires the application to be running,
    but it is not (e.g., attempting to send a message before connecting).
    """
    pass

class ConnectionError(AppError):
    """
    Exception raised for WebSocket connection failures, including send/receive errors.
    """
    pass

class HandlerError(AppError):
    """
    Exception raised when an event handler encounters an unexpected error.
    """
    pass

class MessageError(AppError):
    """
    Exception raised for errors during message processing or serialization.
    """
    pass

class AuthenticationError(AppError):
    """
    Exception raised for API key authentication failures or invalid credentials.
    """
    pass
