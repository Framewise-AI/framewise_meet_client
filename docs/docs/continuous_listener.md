# Continuous Listener Feature

The Framewise Meet Client includes a robust continuous listener feature that automatically maintains a stable connection to the Framewise API server.

## Overview

The continuous listener feature enables your application to:

- Automatically reconnect when connection issues occur
- Configure reconnection behavior with customizable parameters
- Handle connection rejection events gracefully
- Maintain a persistent connection for real-time event processing

## Configuration Options

When starting your application with `app.run()`, you can configure the continuous listener behavior:

```python
app.run(
    auto_reconnect=True,     # Enable/disable automatic reconnection (default: True)
    reconnect_delay=5,       # Seconds to wait between reconnection attempts (default: 5)
    log_level="INFO"         # Optional logging level
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auto_reconnect` | bool | `True` | Whether to automatically reconnect when disconnected |
| `reconnect_delay` | int | `5` | Time in seconds to wait between reconnection attempts |
| `log_level` | str | `None` | Optional logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

## Handling Connection Events

The client provides event handlers for connection-related events:

### Connection Rejected Handler

```python
@app.on_connection_rejected()
def handle_connection_rejection(message):
    reason = message.content.reason
    print(f"Connection rejected: {reason}")
    
    # Implement custom reconnection logic
    if "limit" in reason.lower():
        time.sleep(10)
        app.join_meeting(meeting_id="your_meeting_id")
```

## Implementation Details

### Exponential Backoff

The reconnection mechanism uses exponential backoff to avoid overwhelming the server during connection issues. If multiple reconnection attempts fail, the wait time between attempts will gradually increase up to a configurable maximum.

### Connection States

The client maintains internal connection states to track:
- Connection status
- Authentication status
- Rejection reasons (if applicable)

## Best Practices

1. **Always implement a connection_rejected handler**: This ensures your application can respond appropriately to server-side connection limitations.

2. **Use appropriate reconnect delays**: For development or testing environments, shorter delays (1-5 seconds) work well. For production environments, longer delays (5-15 seconds) prevent overwhelming the server.

3. **Enable logging**: Set the log_level parameter to get visibility into connection events.

4. **Graceful shutdown**: Call `app.stop()` to properly close connections when your application is terminating.

## Example: Robust Connection Handling

```python
import time
from framewise_meet_client.app import App
from framewise_meet_client.models.inbound import ConnectionRejectedMessage

# Create app instance
app = App(api_key="your_api_key")
app.join_meeting(meeting_id="your_meeting_id")

# Track connection state
connection_state = {
    "connected": False,
    "authenticated": False,
    "rejected_reason": None
}

@app.on_connection_rejected()
def handle_rejection(message: ConnectionRejectedMessage):
    reason = message.content.reason
    print(f"Connection rejected: {reason}")
    
    connection_state["connected"] = False
    connection_state["rejected_reason"] = reason
    
    # Implement custom reconnection logic with progressive backoff
    if "limit" in reason.lower():
        wait_time = 5
        print(f"Connection limit reached. Retrying in {wait_time} seconds...")
        time.sleep(wait_time)
        app.join_meeting(meeting_id="your_meeting_id")

@app.on("join")
def on_join(message):
    connection_state["connected"] = True
    connection_state["authenticated"] = True
    print("Successfully connected and authenticated")

if __name__ == "__main__":
    # Enable continuous listener with custom configuration
    app.run(
        auto_reconnect=True,
        reconnect_delay=10,
        log_level="DEBUG"
    )
```