class InvalidMessageTypeError(TypeError):
    """Exception raised when a message cannot be converted to the expected type."""
    
    def __init__(self, expected_type, actual_type):
        self.expected_type = expected_type
        self.actual_type = actual_type
        message = f"Expected message of type {expected_type} or a subclass, but got {actual_type}"
        super().__init__(message)
