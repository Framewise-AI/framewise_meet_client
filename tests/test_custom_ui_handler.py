import unittest
from unittest.mock import Mock, MagicMock
from framewise_meet_client.events.custom_ui_handler import CustomUIHandler
from framewise_meet_client.event_handler import EventDispatcher
from framewise_meet_client.models.outbound import CustomUIElementMessage as CustomUIElementResponse

class TestCustomUIHandler(unittest.TestCase):
    def setUp(self):
        self.dispatcher = MagicMock(spec=EventDispatcher)
        self.handler = CustomUIHandler(self.dispatcher)

    def test_event_type_default(self):
        """Test the default event_type is correctly set."""
        self.assertEqual(self.handler.event_type, "custom_ui_element_response")

    def test_message_class(self):
        """Test that the message_class is correctly set."""
        self.assertEqual(self.handler.message_class, CustomUIElementResponse)

    def test_get_element_type_valid(self):
        """Test extracting the element type from a valid payload."""
        # Create a sample payload with a content.type field
        data = {
            "content": {
                "type": "mcq_question",
                "data": {
                    "id": "q1",
                    "question": "Sample question?",
                    "options": ["Option 1", "Option 2"]
                }
            }
        }
        
        # Call the method
        result = self.handler.get_element_type(data)
        
        # Verify the result
        self.assertEqual(result, "mcq_question")

    def test_get_element_type_missing(self):
        """Test extracting the element type when it's missing."""
        # Create a sample payload without content.type
        data = {
            "content": {
                "data": {
                    "id": "q1",
                    "question": "Sample question?",
                    "options": ["Option 1", "Option 2"]
                }
            }
        }
        
        # Call the method
        result = self.handler.get_element_type(data)
        
        # Verify the result
        self.assertIsNone(result)

    def test_get_element_type_malformed(self):
        """Test extracting the element type from malformed data."""
        # Create various malformed data structures
        test_cases = [
            {},  # Empty dict
            {"content": "not a dict"},  # content is not a dict
            {"wrong_field": {}},  # Missing content field
            None,  # None value
            "not a dict"  # String instead of dict
        ]
        
        for data in test_cases:
            # Call the method
            result = self.handler.get_element_type(data)
            
            # Verify the result
            self.assertIsNone(result, f"Failed with data: {data}")
