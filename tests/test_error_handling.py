import unittest
from unittest.mock import Mock, patch
import json

from framewise_meet_client.error_handling import safe_model_validate, extract_message_content_safely
from framewise_meet_client.models.inbound import TranscriptMessage, CustomUIElementResponse
from pydantic import BaseModel, Field

class TestErrorHandling(unittest.TestCase):
    """Test error handling utilities."""
    
    def test_safe_model_validate_success(self):
        """Test successful model validation."""
        data = {
            "type": "transcript",
            "content": {"text": "Hello", "is_final": True}
        }
        
        result = safe_model_validate(data, TranscriptMessage)
        self.assertIsNotNone(result)
        self.assertEqual(result.content.text, "Hello")
        self.assertTrue(result.content.is_final)
    
    def test_safe_model_validate_failure(self):
        """Test handling of validation failures."""
        data = {
            "type": "transcript",
            "content": {"wrong_field": "value"}  # Missing required fields
        }
        
        result = safe_model_validate(data, TranscriptMessage)
        self.assertIsNone(result)
    
    def test_safe_model_validate_fallback(self):
        """Test fallback creation of minimal instance."""
        data = {
            "type": "transcript",
            "invalid_field": "value"  # Invalid structure
        }
        
        result = safe_model_validate(
            data, 
            TranscriptMessage, 
            fallback_type="transcript", 
            fallback_content={"text": "fallback", "is_final": False}
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.content.text, "fallback")
        self.assertFalse(result.content.is_final)
    
    def test_extract_message_content_safely_from_model(self):
        """Test extracting content from model instance."""
        message = TranscriptMessage(
            type="transcript",
            content={"text": "Hello world", "is_final": True}
        )
        
        result = extract_message_content_safely(message, "text")
        self.assertEqual(result, "Hello world")
    
    def test_extract_message_content_safely_from_dict(self):
        """Test extracting content from dict."""
        message = {
            "type": "transcript",
            "content": {"text": "Hello world", "is_final": True}
        }
        
        result = extract_message_content_safely(message, "text")
        self.assertEqual(result, "Hello world")
    
    def test_extract_message_content_safely_missing_field(self):
        """Test handling of missing fields."""
        message = {
            "type": "transcript",
            "content": {"is_final": True}  # No text field
        }
        
        result = extract_message_content_safely(message, "text", default_value="default")
        self.assertEqual(result, "default")

if __name__ == '__main__':
    unittest.main()
