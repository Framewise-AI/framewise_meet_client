import unittest
from unittest.mock import patch, Mock
import asyncio

from framewise_meet_client.error_handling import safe_model_validate, extract_message_content_safely
from framewise_meet_client.models.inbound import TranscriptMessage, ConnectionRejectedMessage

class TestErrorHandlingEdgeCases(unittest.TestCase):
    """Test error handling with various edge cases."""
    
    def test_safe_model_validate_with_extra_fields(self):
        """Test validation with extra fields that should be ignored."""
        data = {
            "type": "transcript",
            "content": {"text": "Hello", "is_final": True},
            "extra_field": "should be ignored",
            "another_extra": {"nested": "value"}
        }
        
        result = safe_model_validate(data, TranscriptMessage)
        self.assertIsNotNone(result)
        self.assertEqual(result.content.text, "Hello")
        
    def test_safe_model_validate_with_missing_required_field_and_fallback(self):
        """Test validation with missing required field, using fallback."""
        data = {
            "type": "transcript",
            # Missing content field
        }
        
        # Without fallback, should return None
        result_without_fallback = safe_model_validate(data, TranscriptMessage)
        self.assertIsNone(result_without_fallback)
        
        # With fallback, should create instance
        result_with_fallback = safe_model_validate(
            data, 
            TranscriptMessage, 
            fallback_type="transcript", 
            fallback_content={"text": "fallback text", "is_final": False}
        )
        self.assertIsNotNone(result_with_fallback)
        self.assertEqual(result_with_fallback.content.text, "fallback text")
        
    def test_extract_message_content_safely_with_invalid_input(self):
        """Test content extraction with various invalid inputs."""
        invalid_inputs = [
            None,
            42, 
            "string", 
            [], 
            {"no_content": "field"},
            {"content": None}
        ]
        
        default_value = "default"
        for invalid_input in invalid_inputs:
            result = extract_message_content_safely(invalid_input, "any_field", default_value)
            self.assertEqual(result, default_value, f"Failed for input: {invalid_input}")

if __name__ == '__main__':
    unittest.main()
