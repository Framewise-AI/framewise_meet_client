# Adding Custom UI Components to Framewise Meet Client

This guide explains how to create and add custom UI components that can be sent to the Framewise Meet service.

## Overview

The Framewise Meet Client allows you to send custom UI elements to be displayed in the meeting interface. This is done through the `MessageSender.send_custom_ui_element()` method, which can be customized to create various UI components.

## Basic Usage

At its core, sending a custom UI element involves:

1. Creating a data structure for your UI component
2. Sending it using the `send_custom_ui_element` method
3. Handling any responses or interactions via event handlers

## Creating a Custom UI Component

### Step 1: Define Your UI Component Data Structure

First, define a data structure for your component in a Pydantic model. Add this to the appropriate location in the `models/outbound.py` file:

```python
from pydantic import BaseModel, Field

class YourCustomElementData(BaseModel):
    """Data structure for your custom UI element."""
    id: str
    title: str
    content: str
    # Add any other fields your component needs

class YourCustomElement(BaseModel):
    """Wrapper for your custom UI element."""
    type: str = "your_custom_element_type"
    data: YourCustomElementData
```

### Step 2: Add a Helper Method in MessageSender

Add a convenience method to the `MessageSender` class in `messaging.py`:

```python
def send_your_custom_element(
    self,
    element_id: str,
    title: str,
    content: str,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    """Send your custom UI element to the server.

    Args:
        element_id: Unique identifier for this element
        title: Title to display
        content: Content to display
        loop: Event loop to run the coroutine in
    """
    data = YourCustomElementData(
        id=element_id,
        title=title,
        content=content,
    )
    element = YourCustomElement(type="your_custom_element_type", data=data)
    message = self._prepare_message(CustomUIElementMessage, content=element)

    if loop:
        asyncio.run_coroutine_threadsafe(self._send_message(message), loop)
    else:
        asyncio.create_task(self._send_message(message))
```

### Step 3: Create an Event Handler for Responses (Optional)

If your UI component generates user interactions that will be sent back from the server, create a handler in the `events` directory:

```python
from framewise_meet_client.events.base_handler import BaseHandler

class YourCustomUIHandler(BaseHandler):
    """Handles responses from your custom UI element."""
    
    async def handle(self, data: dict) -> None:
        """Process the event data.
        
        Args:
            data: Event data from the server
        """
        # Extract relevant information
        element_id = data.get("id")
        response = data.get("response")
        
        # Process the response
        # ...

        # Call the callback if it exists
        if self.callback:
            await self.callback(data)
```

### Step 4: Register Your Handler

Make sure to register your handler with the event dispatcher when you set up your application:

```python
from framewise_meet_client.events.your_custom_ui_handler import YourCustomUIHandler

# In your setup code:
runner = AppRunner(app)
runner.event_dispatcher.register("your_custom_element_response", YourCustomUIHandler(callback=your_callback_function))
```

## Example: Creating a Simple Alert Component

Here's a complete example of creating a simple alert component:

### 1. Define the Model

```python
class AlertData(BaseModel):
    """Data for an alert UI element."""
    id: str
    title: str
    message: str
    severity: str = "info"  # info, warning, error, success

class AlertElement(BaseModel):
    """Alert UI element."""
    type: str = "alert"
    data: AlertData
```

### 2. Add Helper Method

```python
def send_alert(
    self,
    alert_id: str,
    title: str,
    message: str,
    severity: str = "info",
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    """Send an alert UI element to the server.

    Args:
        alert_id: Unique identifier for this alert
        title: Alert title
        message: Alert message
        severity: Alert severity (info, warning, error, success)
        loop: Event loop to run the coroutine in
    """
    alert_data = AlertData(
        id=alert_id,
        title=title,
        message=message,
        severity=severity,
    )
    alert_element = AlertElement(type="alert", data=alert_data)
    message = self._prepare_message(CustomUIElementMessage, content=alert_element)

    if loop:
        asyncio.run_coroutine_threadsafe(self._send_message(message), loop)
    else:
        asyncio.create_task(self._send_message(message))
```

### 3. Using the Component

```python
# Create an instance of MessageSender
message_sender = MessageSender(connection)

# Send an alert
message_sender.send_alert(
    alert_id="unique-alert-id",
    title="Important Notice",
    message="This is an important message for all participants.",
    severity="warning"
)
```

## Best Practices

1. **Use Unique IDs**: Always assign unique IDs to your UI elements to track responses.
2. **Keep Data Structures Simple**: UI elements should have clean, straightforward data models.
3. **Validate Input**: Ensure your data models include proper validation constraints.
4. **Handle Errors Gracefully**: Always add error handling in your event handlers.
5. **Document Your Components**: Clearly document the purpose and structure of each custom component.
6. **Test Thoroughly**: Verify that your custom components render correctly in the Framewise Meet interface.

## Limitations and Considerations

- The appearance of custom UI elements depends on the Framewise Meet client-side implementation.
- Not all UI concepts may be supported by the Framewise Meet rendering engine.
- Complex interactive components may require coordination with the Framewise Meet development team.

## Example Components

The Framewise Meet Client includes several built-in custom UI elements you can use as examples:

- MCQ Questions (`send_mcq_question`)
- Notifications (`send_notification`)
- Generated Text (`send_generated_text`)

Study these implementations to understand the patterns for creating effective custom UI components.