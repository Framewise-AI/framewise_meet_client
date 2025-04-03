import unittest
from unittest.mock import MagicMock, patch, AsyncMock, Mock
import asyncio
import json

from framewise_meet_client.app import App
from framewise_meet_client.events.custom_ui_handler import CustomUIHandler
from framewise_meet_client.runner import AppRunner
from framewise_meet_client.models.outbound import CustomUIElementMessage,CustomUIElement

class TestUIElementsIntegration(unittest.TestCase):
    """Integration tests for custom UI elements functionality."""
    
    def setUp(self):
        """Set up the test environment with mocked components."""
        # Create the app
        self.app = App()
        
        # Create mocked connection
        self.mock_connection = MagicMock()
        self.mock_connection.connected = True
        self.mock_connection.send = AsyncMock()
        self.mock_connection.receive = AsyncMock()
        
        # Setup the app with the mocked connection
        self.app.connection = self.mock_connection
        
        # Create a real event dispatcher
        self.app.event_dispatcher.dispatch = AsyncMock()
        
        # Create the AppRunner with the mocks
        self.runner = AppRunner(
            self.mock_connection,
            self.app.event_dispatcher,
            auto_reconnect=False
        )
        self.runner.app = self.app

    async def _test_ui_element_dispatch(self, element_type):
        """Helper method to test UI element dispatch."""
        # Create a mock app
        app = Mock()
        handler_called = False
        
        # Create event data based on the element type
        data = {
            "element_type": element_type,
            "data": {"test": "data"}
        }
        
        # Create a content object with the data
        content = CustomUIElement(**data)
        
        # Create the message
        message = CustomUIElementMessage(content=content)
        
        # Create a handler that sets the flag when called
        async def custom_handler(type_name, data):
            nonlocal handler_called
            handler_called = True
            self.assertEqual(type_name, element_type)
            
        # Register the handler
        app.on_custom_ui_element_response = custom_handler
        
        # Create a CustomUIHandler instance
        handler = CustomUIHandler(app)
        
        # Process the message
        await handler.handle_event(message)
        
        # Verify the handler was called
        self.assertTrue(handler_called, f"Handler for custom_ui_element_response was not called")

    def test_mcq_question_dispatch(self):
        """Test MCQ question response dispatch."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_ui_element_dispatch("mcq_question"))
        finally:
            loop.close()
    
    def test_places_autocomplete_dispatch(self):
        """Test places autocomplete response dispatch."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_ui_element_dispatch("places_autocomplete"))
        finally:
            loop.close()
    
    def test_upload_file_dispatch(self):
        """Test file upload response dispatch."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_ui_element_dispatch("upload_file"))
        finally:
            loop.close()
    
    def test_textinput_dispatch(self):
        """Test text input response dispatch."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_ui_element_dispatch("textinput"))
        finally:
            loop.close()
    
    def test_consent_form_dispatch(self):
        """Test consent form response dispatch."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_ui_element_dispatch("consent_form"))
        finally:
            loop.close()
    
    def test_calendly_dispatch(self):
        """Test Calendly response dispatch."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_ui_element_dispatch("calendly"))
        finally:
            loop.close()

if __name__ == '__main__':
    unittest.main()
