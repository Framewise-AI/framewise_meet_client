"""
Error handling utilities for the Framewise Meet client library.

This module provides functions to safely convert raw data into Pydantic models
and to extract content fields from messages without raising errors.
It helps maintain robust processing when input data may not conform to expected schemas.

Functions:
    safe_model_validate: Safely validate dict to Pydantic model, with fallback support.
    extract_message_content_safely: Safely extract a field from message content.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

def safe_model_validate(
    data: Dict[str, Any],
    model_class: Type[T],
    fallback_type: str = None,
    fallback_content: Dict[str, Any] = None
) -> Optional[T]:
    """
    Safely validate and convert a dictionary to a Pydantic model instance.

    This function wraps Pydantic's model_validate with error handling.
    If validation fails, it can create a minimal fallback instance if
    fallback parameters are provided, preventing application crashes.

    Args:
        data: The raw dictionary to validate against the model.
        model_class: The target Pydantic model class to instantiate.
        fallback_type: Optional 'type' field for creating a minimal instance if validation fails.
        fallback_content: Optional content for the fallback instance.

    Returns:
        An instance of model_class if validation succeeds or fallback is created,
        otherwise None.
    """
    try:
        return model_class.model_validate(data)
    except ValidationError as e:
        logger.warning(f"Validation error converting to {model_class.__name__}: {e}")
        if fallback_type is not None:
            try:
                minimal_data = {"type": fallback_type, "content": fallback_content or {}}
                logger.info(f"Creating minimal {model_class.__name__} instance")
                return model_class.model_validate(minimal_data)
            except Exception as inner_e:
                logger.error(f"Failed to create minimal instance: {inner_e}")
    except Exception as e:
        logger.error(f"Unexpected error converting to {model_class.__name__}: {e}")
        logger.debug(traceback.format_exc())
    return None


def extract_message_content_safely(message: Any, field_name: str, default_value: Any = None) -> Any:
    """
    Safely extract a field from message content regardless of structure.

    Supports both dict-based messages and model instances with attributes.
    Returns a default value if extraction fails or the field is missing.

    Args:
        message: The message object, either a dict or Pydantic model instance.
        field_name: The name of the field to extract from message.content.
        default_value: The value to return if extraction fails.

    Returns:
        The extracted value or default_value if not found or error occurs.
    """
    try:
        if hasattr(message, 'content') and hasattr(message.content, field_name):
            return getattr(message.content, field_name)
        if isinstance(message, dict) and 'content' in message:
            content = message['content']
            if isinstance(content, dict) and field_name in content:
                return content[field_name]
    except Exception as e:
        logger.debug(f"Error extracting {field_name} from message: {e}")
    return default_value
