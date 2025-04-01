import asyncio
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import json
from typing import Dict, Any

from framewise_meet_client.messaging import MessageSender
from framewise_meet_client.models.outbound import (
    MCQQuestionData, 
    NotificationData, 
    PlacesAutocompleteData,
    UploadFileData,
    TextInputData,
    ConsentFormData,
    CalendlyData
)
from framewise_meet_client.models.inbound import ConnectionRejectedMessage

class TestMessageSender(unittest.TestCase):
    def setUp(self):
        # Create a mock connection
        self.mock_connection = MagicMock()
        self.mock_connection.connected = True
        self.mock_connection.send = AsyncMock()
        
        # Create the MessageSender with the mock connection
        self.sender = MessageSender(self.mock_connection)
    
    def test_init(self):
        """Test that MessageSender initializes correctly."""
        self.assertEqual(self.sender.connection, self.mock_connection)
    
    @patch('asyncio.create_task')
    async def test_send_mcq_question(self):
        """Test sending an MCQ question."""
        with patch.object(self.sender, '_send_model') as mock_send:
            options = [{'id': '1', 'text': 'Option 1'}, {'id': '2', 'text': 'Option 2'}]
            coroutine = self.sender.send_mcq_question("test_id", "Test Question", options)
            
            # In Python 3.12, asyncio.coroutine is deprecated
            # Instead verify it's a coroutine object
            self.assertTrue(asyncio.iscoroutine(coroutine))
            
            await coroutine
            mock_send.assert_called_once()
            args, _ = mock_send.call_args
            self.assertEqual(args[0].type, "mcq")
        
    @patch('asyncio.create_task')
    def test_send_notification(self, mock_create_task):
        """Test sending a notification."""
        # Call the method
        self.sender.send_notification(
            notification_id="n1",
            text="Test notification",
            level="info",
            duration=5000,
        )
        
        # Verify create_task was called
        self.assertEqual(mock_create_task.call_count, 1)

    @patch('asyncio.create_task')
    def test_send_places_autocomplete(self, mock_create_task):
        """Test sending a places autocomplete UI element."""
        # Call the method
        self.sender.send_places_autocomplete(
            element_id="loc1",
            text="Enter your location",
            placeholder="Search for a place"
        )
        
        # Verify create_task was called
        self.assertEqual(mock_create_task.call_count, 1)

    @patch('asyncio.create_task')
    def test_send_upload_file(self, mock_create_task):
        """Test sending a file upload UI element."""
        # Call the method
        self.sender.send_upload_file(
            element_id="file1",
            text="Upload your document",
            allowed_types=["application/pdf", "image/jpeg"],
            max_size_mb=10
        )
        
        # Verify create_task was called
        self.assertEqual(mock_create_task.call_count, 1)

    @patch('asyncio.create_task')
    def test_send_text_input(self, mock_create_task):
        """Test sending a text input UI element."""
        # Call the method
        self.sender.send_text_input(
            element_id="input1",
            prompt="Please enter your feedback",
            placeholder="Type here...",
            multiline=True
        )
        
        # Verify create_task was called
        self.assertEqual(mock_create_task.call_count, 1)

    @patch('asyncio.create_task')
    def test_send_consent_form(self, mock_create_task):
        """Test sending a consent form UI element."""
        # Call the method
        self.sender.send_consent_form(
            element_id="consent1",
            text="I agree to the terms and conditions",
            checkbox_label="I agree",
            submit_label="Continue",
            required=True
        )
        
        # Verify create_task was called
        self.assertEqual(mock_create_task.call_count, 1)

    @patch('asyncio.create_task')
    def test_send_calendly(self, mock_create_task):
        """Test sending a Calendly scheduling UI element."""
        # Call the method
        self.sender.send_calendly(
            element_id="cal1",
            url="https://calendly.com/test/meeting",
            title="Schedule a call",
            subtitle="Choose a time that works for you"
        )
        
        # Verify create_task was called
        self.assertEqual(mock_create_task.call_count, 1)

    @patch('asyncio.run_coroutine_threadsafe')
    def test_send_with_custom_loop(self, mock_run_coroutine):
        """Test sending a message with a custom event loop."""
        # Create a mock loop
        mock_loop = MagicMock()
        
        # Call the method with the mock loop
        self.sender.send_mcq_question(
            question_id="q1",
            question="Test question?",
            options=["Option 1", "Option 2"],
            loop=mock_loop
        )
        
        # Verify run_coroutine_threadsafe was called with the mock loop
        self.assertEqual(mock_run_coroutine.call_count, 1)
        self.assertEqual(mock_run_coroutine.call_args[0][1], mock_loop)

    async def _test_send_model_implementation(self):
        """Test the actual implementation of _send_model."""
        # Create a test model
        test_data = MCQQuestionData(
            id="test-id",
            question="Test question",
            options=["Option 1", "Option 2"]
        )
        
        # Call the _send_model method
        await self.sender._send_model(test_data)
        
        # Verify the connection's send method was called with the correct data
        self.mock_connection.send.assert_called_once()
        sent_data = self.mock_connection.send.call_args[0][0]
        self.assertEqual(sent_data["id"], "test-id")
        self.assertEqual(sent_data["question"], "Test question")
        self.assertEqual(sent_data["options"], ["Option 1", "Option 2"])

    def test_send_model(self):
        """Test the _send_model method."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_send_model_implementation())
        finally:
            loop.close()

    async def _test_connection_not_established(self):
        """Test behavior when connection is not established."""
        # Set connection to not connected
        self.mock_connection.connected = False
        
        # Create a test model
        test_data = NotificationData(
            id="test-id",
            text="Test notification",
            level="info"
        )
        
        # Call the method
        await self.sender._send_model(test_data)
        
        # Verify send was not called
        self.mock_connection.send.assert_not_called()

    def test_connection_not_established(self):
        """Test behavior when connection is not established."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_connection_not_established())
        finally:
            loop.close()

    async def _test_handle_connection_rejected(self):
        """Test handling connection rejection message."""
        # Create mock message
        rejected_data = {
            "type": "connection_rejected",
            "content": {
                # Create content that matches the actual model structure
                "reason": "Invalid API key"
                # Note: Don't include meeting_id if it's not in the model
            }
        }
        
        # Create ConnectionRejectedMessage
        rejected_message = ConnectionRejectedMessage.model_validate(rejected_data)
        
        # Ensure the message has correct content
        self.assertEqual(rejected_message.content.reason, "Invalid API key")
        
        # Verify type
        self.assertEqual(rejected_message.type, "connection_rejected")

    def test_handle_connection_rejected(self):
        """Test the connection rejection handling."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._test_handle_connection_rejected())
        finally:
            loop.close()

if __name__ == '__main__':
    unittest.main()
