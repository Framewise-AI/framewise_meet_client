"""Error handling utilities for the Framewise Meet client."""

import logging
import traceback
from typing import Any, Dict, Optional, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

def safe_model_validate(
    data: Dict[str, Any],
    model_class: Type[T],
    fallback_type: str = None,
    fallback_content: Dict[str, Any] = None
) -> Optional[T]:
    """Safely validate and convert a dict to a Pydantic model.
    
    Args:
        data: Dictionary data to convert
        model_class: Target Pydantic model class
        fallback_type: Type to use for minimal fallback instance
        fallback_content: Content to use for minimal fallback instance
        
    Returns:
        Converted model instance or None if conversion fails
    """
    try:
        return model_class.model_validate(data)
    except ValidationError as e:
        logger.warning(f"Validation error converting to {model_class.__name__}: {e}")
        
        # Try to create minimal instance
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
    """Safely extract content from message objects regardless of structure.
    
    Works with both dict messages and model instances.
    
    Args:
        message: Message object (dict or model instance)
        field_name: Name of the field to extract
        default_value: Default value to return if extraction fails
        
    Returns:
        Extracted field value or default value
    """
    try:
        if hasattr(message, 'content') and hasattr(message.content, field_name):
            return getattr(message.content, field_name)
        elif isinstance(message, dict) and 'content' in message:
            content = message['content']
            if isinstance(content, dict) and field_name in content:
                return content[field_name]
    except Exception as e:
        logger.debug(f"Error extracting {field_name} from message: {e}")
    
    return default_value
