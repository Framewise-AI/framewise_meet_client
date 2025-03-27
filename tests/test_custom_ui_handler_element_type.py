import unittest
from framewise_meet_client.events.custom_ui_handler import CustomUIHandler
from unittest.mock import Mock

class TestCustomUIHandlerElementType(unittest.TestCase):
    """Test the get_element_type method of CustomUIHandler."""
    
    def setUp(self):
        """Set up the test with a CustomUIHandler instance."""
        self.handler = CustomUIHandler(Mock())
    
    def test_extract_element_type_success(self):
        """Test successfully extracting element type from data."""
        data = {
            "content": {
                "type": "mcq_question",
                "data": {"some": "data"}
            }
        }
        element_type = self.handler.get_element_type(data)
        self.assertEqual(element_type, "mcq_question")
    
    def test_none_data_raises_error(self):
        """Test that None data raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.handler.get_element_type(None)
        self.assertIn("Cannot extract element type from None data", str(context.exception))
    
    def test_non_dict_data_raises_error(self):
        """Test that non-dictionary data raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.handler.get_element_type("not a dict")
        self.assertEqual(str(context.exception), "Expected dict data, got str")
    
    def test_empty_dict_raises_error(self):
        """Test that empty dictionary raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.handler.get_element_type({})
        self.assertEqual(str(context.exception), "Cannot extract element type from empty dictionary")
    
    def test_missing_content_field_raises_error(self):
        """Test that missing content field raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.handler.get_element_type({"other": "value"})
        self.assertEqual(str(context.exception), "Missing 'content' field in data")
    
    def test_non_dict_content_returns_none(self):
        """Test that non-dictionary content returns None."""
        data = {"content": "not a dict"}
        element_type = self.handler.get_element_type(data)
        self.assertIsNone(element_type)

if __name__ == "__main__":
    unittest.main()
