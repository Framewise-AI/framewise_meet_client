class AppError(Exception):
    """Base exception class for application errors."""
    pass

class AppNotRunningError(AppError):
    """Exception raised when an operation requires the app to be running."""
    pass

class ConnectionError(AppError):
    """Exception raised for WebSocket connection errors."""
    pass

class HandlerError(AppError):
    """Exception raised for errors in event handlers."""
    pass

class MessageError(AppError):
    """Exception raised for errors in message processing."""
    pass

class AuthenticationError(AppError):
    """Exception raised for authentication errors."""
    pass
