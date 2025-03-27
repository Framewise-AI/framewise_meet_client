import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from framewise_meet_client.app import App, CONNECTION_REJECTED_EVENT
# Update import to use inbound module
from framewise_meet_client.models.inbound import ConnectionRejectedMessage
from framewise_meet_client.errors import AuthenticationError

class TestConnectionRejection(unittest.TestCase):
    def setUp(self):
        self.app = App(api_key="test-api-key", host="localhost", port=8000)
        self.app.join_meeting("test-meeting")
        
        # Create mock connection
        self.mock_connection = MagicMock()
        self.mock_connection.connected = True
        self.mock_connection.send = AsyncMock()
        self.app.connection = self.mock_connection
    
    def test_connection_rejected_handler_registration(self):
        """Test that the connection rejected handler is correctly registered."""
        # Register a test handler
        test_handler_called = False
        
        def test_handler(message):
            nonlocal test_handler_called
            test_handler_called = True
            self.assertEqual(message.content.reason, "Invalid API key")
            
        # Register the handler
        self.app.on_connection_rejected(test_handler)
        
        # Check that the handler is registered
        self.assertTrue(CONNECTION_REJECTED_EVENT in self.app.event_dispatcher.handlers)
        
        # Create a mock rejection message
        mock_message = ConnectionRejectedMessage(
            type="connection_rejected",
            content={
                "reason": "Invalid API key"
            }
        )
        
        # Dispatch the event to our handler
        asyncio.run(self.app.event_dispatcher.dispatch(CONNECTION_REJECTED_EVENT, mock_message))
        
        # Verify the handler was called
        self.assertTrue(test_handler_called)
    
    @patch('framewise_meet_client.auth.authenticate_api_key')
    def test_authentication_error_handling(self, mock_authenticate):
        """Test that authentication errors are properly handled."""
        # Set up the mock to fail authentication
        mock_authenticate.return_value = False
        
        # Authentication should raise an error when it fails
        with self.assertRaises(AuthenticationError):
            self.app.run()
            
    def test_default_connection_rejected_handler(self):
        """Test the default connection rejected handler."""
        # Ensure the app has a default handler
        self.app._register_default_handlers()
        
        # Create a mock rejection message
        mock_message = ConnectionRejectedMessage(
            type="connection_rejected",
            content={
                "reason": "Invalid API key"
            }
        )
        
        # The default handler should set running to False
        self.app.running = True
        
        # Dispatch the event to the default handler
        asyncio.run(self.app.event_dispatcher.dispatch(CONNECTION_REJECTED_EVENT, mock_message))
        
        # Verify app is no longer running
        self.assertFalse(self.app.running)

if __name__ == '__main__':
    unittest.main()
