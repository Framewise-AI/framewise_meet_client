# Framewise Meet Client

A Python client library for building interactive applications with the Framewise API.

## Installation

Install the package using pip:

```bash
pip install -r requirements.txt
```

## Getting Started

### Basic Usage

```python
from framewise_meet_client.app import App
from framewise_meet_client.models.messages import TranscriptMessage

# Create an app instance with your API key
app = App(api_key="your_api_key_here")

# Join a specific meeting
app.join_meeting(meeting_id="your_meeting_id")

# Define an event handler for transcripts
@app.on_transcript()
def handle_transcript(message: TranscriptMessage):
    transcript = message.content.text
    is_final = message.content.is_final
    print(f"Received: {transcript}")

# Run the app
if __name__ == "__main__":
    app.run()
```

## Documentation Structure

- **Core Features**
  - [Continuous Listener](continuous_listener.md): Auto-reconnection and robust connection handling
  - [Custom UI Components](adding_custom_ui_components.md): Adding interactive UI elements
  - [Agent Connector](agent_connector.md): Managing multiple AI agents with automatic startup
- **API Reference**: Detailed documentation of all modules and functions
