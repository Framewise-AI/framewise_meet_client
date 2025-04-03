import unittest
from framewise_meet_client.app import EventType, JOIN_EVENT, EXIT_EVENT, TRANSCRIPT_EVENT, CUSTOM_UI_EVENT, INVOKE_EVENT, CONNECTION_REJECTED_EVENT

class TestEventTypes(unittest.TestCase):
    def test_event_type_enum(self):
        """Test that the EventType enum has correct values."""
        self.assertEqual(EventType.JOIN.value, JOIN_EVENT)
        self.assertEqual(EventType.EXIT.value, EXIT_EVENT)
        self.assertEqual(EventType.TRANSCRIPT.value, TRANSCRIPT_EVENT)
        self.assertEqual(EventType.CUSTOM_UI_RESPONSE.value, CUSTOM_UI_EVENT)
        self.assertEqual(EventType.INVOKE.value, INVOKE_EVENT)
        self.assertEqual(EventType.CONNECTION_REJECTED.value, CONNECTION_REJECTED_EVENT)
    
    def test_event_aliases(self):
        """Test that event aliases are properly mapped."""
        from framewise_meet_client.app import App
        
        app = App()
        
        self.assertEqual(app._event_aliases["connection_rejected"], CONNECTION_REJECTED_EVENT)
        self.assertEqual(app._event_aliases["join"], JOIN_EVENT)
        self.assertEqual(app._event_aliases["exit"], EXIT_EVENT)
        self.assertEqual(app._event_aliases["transcript"], TRANSCRIPT_EVENT)
        self.assertEqual(app._event_aliases["custom_ui_response"], CUSTOM_UI_EVENT)
        self.assertEqual(app._event_aliases["invoke"], INVOKE_EVENT)

if __name__ == '__main__':
    unittest.main()
