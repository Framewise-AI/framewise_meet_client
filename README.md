# Framewise Meet Client

A Python client library for building interactive applications with the Framewise API.

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
  - [Authentication](#authentication)
  - [Event Handlers](#event-handlers)
  - [Sending Responses](#sending-responses)
  - [Multiple-Choice Questions (MCQs)](#multiple-choice-questions-mcqs)
  - [Custom UI Elements](#custom-ui-elements)
- [Advanced Features](#advanced-features)
  - [Meeting Management](#meeting-management)
  - [Logging Configuration](#logging-configuration)
- [API Reference](#api-reference)
- [License](#license)

## Installation

Install the package using pip:

```bash
pip install framewise-meet-client
```

## Quick Start

```python
from framewise_meet_client import App
from framewise_meet_client.models.inbound import TranscriptMessage

# Create an app instance with your API key
app = App(api_key="your_api_key_here", host="backendapi.framewise.ai", port=443)

# Join a meeting
app.join_meeting("your_meeting_id")

# Handle transcript events
@app.on_transcript()
def handle_transcript(message: TranscriptMessage):
    print(f"Received transcript: {message.content.text}")
    if message.content.is_final:
        print("This is a final transcript")

# Run the app
if __name__ == "__main__":
    app.run()
```

## Core Features

### Authentication

The client supports API key authentication:

```python
# Initialize with API key
app = App(api_key="your_api_key_here", host="backendapi.framewise.ai", port=443)

# Or set API key later
app = App(host="backendapi.framewise.ai", port=443)
app.set_api_key("your_api_key_here")
```

### Event Handlers

Register handlers for different event types using the decorator pattern:

#### Typed Event Handlers

```python
# Transcript events
@app.on_transcript()
def handle_transcript(message: TranscriptMessage):
    print(f"Transcript: {message.content.text}")

# Join events
@app.on_join()
def handle_join(message: JoinMessage):
    print(f"User joined: {message.content.user.name}")

# Exit events
@app.on_exit()
def handle_exit(message: ExitMessage):
    print(f"User left: {message.content.user.name}")

# MCQ selection events
@app.on_mcq_selection()
def handle_selection(message: MCQSelectionMessage):
    print(f"Selected option: {message.content.selectedOption}")
```

#### Generic Event Handlers

```python
# Using string event type
@app.on("transcript")
def handle_any_transcript(message):
    print(f"Generic handler: {message.content.text}")

# Using invoke for final transcripts
@app.invoke
def process_command(message: TranscriptMessage):
    if message.content.is_final:
        print(f"Processing command: {message.content.text}")
        app.send_text(f"Received command: {message.content.text}")
```

### Sending Responses

The client provides several methods to send different types of content:

```python
# Send plain text
app.send_text("Hello world!")

# Send generated text with streaming support
app.send_generated_text("Starting to generate content...", is_generation_end=False)
app.send_generated_text("Here's the complete response!", is_generation_end=True)

# Send notifications with different levels
app.send_notification("Operation completed", level="info", duration=5000)

# Send custom UI elements
app.send_custom_ui_element("card", {
    "title": "Important Information",
    "content": "This is a custom card element",
    "buttons": ["OK", "Cancel"]
})
```

### Multiple-Choice Questions (MCQs)

Create interactive polls and quizzes:

```python
# Send an MCQ question
app.send_mcq_question(
    question_id="quiz-1",
    question="What is the capital of France?",
    options=["Paris", "London", "Berlin", "Madrid"]
)

# Handle MCQ responses
@app.on_mcq_selection()
def handle_mcq_response(message):
    question_id = message.content.questionId
    selected_option = message.content.selectedOption
    selected_index = message.content.selectedIndex
    user = message.content.user
    
    print(f"User {user.name} selected {selected_option} (index: {selected_index}) for question {question_id}")
    
    # Send acknowledgment
    if selected_option == "Paris":
        app.send_text("Correct!")
    else:
        app.send_text("Incorrect. The answer is Paris.")
```

### Custom UI Elements

Display custom interface components:

```python
# Send a custom card element
app.send_custom_ui_element("card", {
    "title": "Weather Forecast",
    "content": "Today will be sunny with a high of 75°F",
    "image": "https://example.com/weather.png",
    "buttons": ["View Details", "Dismiss"]
})

# Handle UI element interactions
@app.on_custom_ui()
def handle_ui_interaction(message):
    ui_type = message.content.uiType
    action = message.content.action
    data = message.content.data
    
    print(f"UI interaction: type={ui_type}, action={action}, data={data}")
```

#### Specific UI Element Handlers

```python
# Handle specific UI element types
@app.on_custom_ui(ui_type="card")
def handle_card_interaction(message):
    print(f"Card interaction: {message.content.action}")
    
    if message.content.action == "button_click" and message.content.data["button"] == "View Details":
        app.send_text("Showing detailed weather forecast...")
```

## Advanced Features

### Meeting Management

Create and manage meetings programmatically:

```python
# Create a new meeting
meeting_data = app.create_meeting(
    meeting_id="team_meeting_123",
    start_time_utc="2023-08-15T14:00:00Z",
    end_time_utc="2023-08-15T15:00:00Z"
)

# Join the newly created meeting
app.join_meeting(meeting_id=meeting_data["meeting_id"])
```

### Logging Configuration

Configure logging when running the app:

```python
# Set logging level
app.run(log_level="DEBUG")  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Configure auto-reconnect behavior
app.run(auto_reconnect=True, reconnect_delay=5)
```

## API Reference

For complete API documentation, visit [https://docs.framewise.ai/docs/](https://docs.framewise.ai/docs/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
