import unittest
from unittest.mock import MagicMock, patch
import asyncio

from framewise_meet_client.app import App
from framewise_meet_client.events import (
    CUSTOM_UI_EVENT,
    MCQ_QUESTION_EVENT,
    PLACES_AUTOCOMPLETE_EVENT,
    UPLOAD_FILE_EVENT,
    TEXTINPUT_EVENT,
    CONSENT_FORM_EVENT,
    CALENDLY_EVENT,
)

class TestAppUIHandlers(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.app = App()
        self.app.event_dispatcher = MagicMock()
        
    def test_on_ui_type_registration(self):
        """Test registering a handler for a specific UI element type."""
        # Define a sample handler function
        def sample_handler(message):
            return "processed"
        
        # Register the handler for a custom UI type
        self.app.on_ui_type("custom_chart")(sample_handler)
        
        # Verify the handler was registered with the event dispatcher
        self.app.event_dispatcher.register_handler.assert_called_once_with("custom_chart")

    def test_event_aliases(self):
        """Test that all UI element events are properly defined in event_aliases."""
        # Check that all required event types are mapped
        expected_mappings = {
            "mcq_question": MCQ_QUESTION_EVENT,
            "places_autocomplete": PLACES_AUTOCOMPLETE_EVENT,
            "upload_file": UPLOAD_FILE_EVENT,
            "textinput": TEXTINPUT_EVENT,
            "consent_form": CONSENT_FORM_EVENT,
            "calendly": CALENDLY_EVENT,
        }
        
        for event_name, event_type in expected_mappings.items():
            self.assertEqual(self.app._event_aliases[event_name], event_type)

    def test_on_custom_ui_element_response(self):
        """Test the on_custom_ui_element_response method."""
        # Define a sample handler function
        def sample_handler(message):
            return "processed"
        
        # Create a patch for the on method
        with patch.object(self.app, 'on') as mock_on:
            mock_decorator = MagicMock()
            mock_on.return_value = mock_decorator
            
            # Call with a handler function
            result = self.app.on_custom_ui_element_response(sample_handler)
            
            # Verify on was called with the right event type
            mock_on.assert_called_once_with(CUSTOM_UI_EVENT)
            # Verify the decorator was called with the handler
            mock_decorator.assert_called_once_with(sample_handler)
            # Verify the result is the mocked return value
            self.assertEqual(result, mock_decorator.return_value)
            
            # Reset mocks
            mock_on.reset_mock()
            mock_decorator.reset_mock()
            
            # Call without a handler function
            result = self.app.on_custom_ui_element_response()
            
            # Verify on was called with the right event type
            mock_on.assert_called_once_with(CUSTOM_UI_EVENT)
            # Verify the decorator wasn't called (since we didn't pass a handler)
            mock_decorator.assert_not_called()
            # Verify the result is the mocked decorator
            self.assertEqual(result, mock_decorator)

    def test_specific_ui_element_response_handlers(self):
        """Test the specific UI element response handler methods."""
        # Define a sample handler function
        def sample_handler(message):
            return "processed"
        
        # Test cases: (method_name, event_type)
        test_cases = [
            ('on_mcq_question_response', MCQ_QUESTION_EVENT),
            ('on_places_autocomplete_response', PLACES_AUTOCOMPLETE_EVENT),
            ('on_upload_file_response', UPLOAD_FILE_EVENT),
            ('on_textinput_response', TEXTINPUT_EVENT),
            ('on_consent_form_response', CONSENT_FORM_EVENT),
            ('on_calendly_response', CALENDLY_EVENT),
        ]
        
        for method_name, event_type in test_cases:
            with patch.object(self.app, 'on') as mock_on:
                mock_decorator = MagicMock()
                mock_on.return_value = mock_decorator
                
                # Get the method
                method = getattr(self.app, method_name)
                
                # Call with a handler function
                result = method(sample_handler)
                
                # Verify on was called with the right event type
                mock_on.assert_called_once_with(event_type)
                # Verify the decorator was called with the handler
                mock_decorator.assert_called_once_with(sample_handler)

                # Reset mocks
                mock_on.reset_mock()
                mock_decorator.reset_mock()
                
                # Call without a handler function
                result = method()
                
                # Verify on was called with the right event type
                mock_on.assert_called_once_with(event_type)
                # Verify the decorator wasn't called
                mock_decorator.assert_not_called()

    @patch('framewise_meet_client.app.register_event_handler')
    def test_on_method_ui_element(self, mock_register_event_handler):
        """Test handling UI element types in the on method."""
        # Define a sample handler function
        def sample_handler(message):
            return "processed"
        
        # Custom UI element type not in event_aliases
        custom_type = "custom_chart"
        
        # Call the on method with the custom type
        result = self.app.on(custom_type)(sample_handler)
        
        # Verify the event_dispatcher.register_handler was called
        self.app.event_dispatcher.register_handler.assert_called_once()
        
        # Verify register_event_handler was not called (since it's not a standard event)
        mock_register_event_handler.assert_not_called()
        
        # Verify the returned handler is our original handler
        self.assertEqual(result, sample_handler)

if __name__ == '__main__':
    unittest.main()
