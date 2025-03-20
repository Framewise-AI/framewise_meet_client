# Framewise Meet Client

A Python client library for building interactive applications with the Framewise API.

## Installation

Install the package using pip:

```bash
pip install framewise-meet-client
```

## Getting Started

### Basic Usage

```python
from framewise_meet_client import App
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

# Define an event handler for final transcripts using invoke
@app.invoke
def process_command(message: TranscriptMessage):
    command = message.content.text
    print(f"Processing command: {command}")
    
    # Send a response
    app.send_generated_text(f"I received: {command}")

# Run the app
if __name__ == "__main__":
    app.run()
```

## Features

### Authentication

The client supports API key authentication:

```python
app = App(api_key="your_api_key_here")
```

### Message Types

The client supports several message types:

1. **Transcripts**: Real-time speech transcriptions
2. **Join/Exit Events**: Notifications when users join or leave
3. **MCQ Questions**: Multiple-choice questions
4. **Custom UI Elements**: Flexible UI components

### Event Handlers

Register handlers for different event types:

```python
# Using typed method
@app.on_transcript()
def handle_transcript(message: TranscriptMessage):
    print(f"Transcript: {message.content.text}")

# Using general method
@app.on("mcq_selection")
def handle_mcq_selection(message: MCQSelectionMessage):
    print(f"Selected: {message.content.selectedOption}")

# Using invoke for final transcripts
@app.invoke
def process_final(message: TranscriptMessage):
    print(f"Final transcript: {message.content.text}")
```

### Sending Responses

Send various types of responses:

```python
# Send text
app.send_text("Hello there!")

# Send generated text (with streaming support)
app.send_generated_text("Processing your request...", is_generation_end=False)
app.send_generated_text("Here's the answer!", is_generation_end=True)

# Send an MCQ question
app.send_mcq(
    question="How would you like to proceed?",
    options=["Continue", "Start over", "Exit"],
    correct_index=0
)

# Send a custom UI element
app.send_custom_ui_element("card", {
    "title": "Important Information",
    "content": "This is a custom card element",
    "buttons": ["OK", "Cancel"]
})
```

## Multiple-Choice Questions (MCQs)

The Framewise client provides robust support for creating and handling multiple-choice questions:

### Sending MCQs

There are two ways to send MCQs to the user:

#### 1. Traditional MCQs

```python
# Send a standard MCQ
app.send_mcq(
    question="What's your favorite color?",
    options=["Red", "Blue", "Green", "Yellow"],
    correct_index=0  # Optional - marks the first option as "correct"
)
```

#### 2. Enhanced MCQs via Custom UI

```python
# Send an MCQ with a unique ID for tracking responses
import uuid
question_id = str(uuid.uuid4())

app.send_mcq_question(
    question_id=question_id,
    question="How would you rate this service?",
    options=["Excellent", "Good", "Fair", "Poor"]
)
```

### Handling MCQ Responses

When a user selects an option from an MCQ, you'll receive an `mcq_selection` event:

```python
@app.on_mcq_selection
def handle_mcq_selection(message: MCQSelectionMessage):
    # Get the selected option text
    selected_option = message.content.selectedOption
    
    # Get the selected option index (0-based)
    selected_index = message.content.selectedIndex
    
    # Get the question ID (if provided in the original MCQ)
    question_id = message.content.questionId
    
    print(f"User selected '{selected_option}' (index: {selected_index}) for question {question_id}")
    
    # Respond based on the selection
    if selected_option == "Excellent":
        app.send_text("Thank you for your positive feedback!")
    else:
        app.send_text(f"You selected: {selected_option}. We appreciate your feedback.")
```

### MCQ Message Format

When receiving an MCQ selection, the message structure is:

```python
{
    "type": "mcq_selection",
    "content": {
        "selectedOption": "Option text that was selected",
        "selectedIndex": 2,  # Zero-based index of the selected option
        "questionId": "unique-id-if-provided"  # Only present if you used send_mcq_question
    }
}
```

This structure is automatically parsed into the `MCQSelectionMessage` object when using the `@app.on_mcq_selection` decorator.

## Custom UI Elements

The Framewise client supports custom UI elements with direct subtype handling:

### Handling UI Element Types

Each custom UI element has a specific type that you can handle directly:

```python
# Handle "mcq_question" UI elements directly
@app.on_ui_type("mcq_question")
def handle_mcq_question(message: CustomUIElementMessage):
    data = message.content.data
    selected_option = data.get("selectedOption")
    question_id = data.get("id")
    print(f"MCQ response: {selected_option} for question {question_id}")
    app.send_generated_text(f"You chose: {selected_option}")

# Handle "info_card" UI elements
@app.on_ui_type("info_card") 
def handle_info_card(message: CustomUIElementMessage):
    data = message.content.data
    action = data.get("action")
    print(f"Info card action: {action}")
    app.send_generated_text(f"Action taken: {action}")
```

### Generic Handler vs Specific Handlers

You can use both specific handlers for known UI types and a generic fallback:

```python
# Specific handler
@app.on_ui_type("poll")
def handle_poll(message: CustomUIElementMessage):
    # Handle poll responses
    pass

# Generic handler for any other UI types
@app.on_custom_ui_response()
def handle_any_ui(message: CustomUIElementMessage):
    ui_type = message.content.type
    if (ui_type not in ["mcq_question"]):
        # Handle unknown UI types
        pass
```

## Advanced Features

### Meeting Creation

Create meetings programmatically:

```python
app = App(api_key="your_api_key_here")

# Create a meeting
meeting_data = app.create_meeting(
    meeting_id="new_meeting_123",
    start_time_utc="2023-06-01T15:00:00Z",
    end_time_utc="2023-06-01T16:00:00Z"
)

# Join the created meeting
app.join_meeting(meeting_id=meeting_data["meeting_id"])
```

### Logging

Configure logging level when running the app:

```python
app.run(log_level="DEBUG")  # Other options: INFO, WARNING, ERROR, CRITICAL
```

## Documentation

For complete documentation, visit [https://framewise-ai.github.io/framewise_meet_client/](https://framewise-ai.github.io/framewise_meet_client/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
