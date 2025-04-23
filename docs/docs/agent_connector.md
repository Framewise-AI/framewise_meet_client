# Agent Connector

The Framewise Meet Client includes an Agent Connector feature that allows you to create and manage multiple AI agents that can respond to meeting events.

## Overview

The Agent Connector lets you:

- Deploy multiple agent types that can be automatically started for different meetings
- Handle agent startup requests from the Framewise backend
- Manage agent processes with automatic cleanup
- Maintain a persistent WebSocket connection to the Framewise coordination server

## Basic Usage

```python
import asyncio
from framewise_meet_client.agent_connector import run_agent_connector
from framewise_meet_client.app import App

# Create your agent app
app = App(api_key="your_api_key_here", host="backendapi.framewise.ai", port=443)

# Define event handlers for your agent
@app.on_transcript()
def handle_transcript(message):
    # Process transcript...
    pass

@app.invoke
def handle_final_transcript(message):
    # Process final transcript...
    pass

# Additional event handlers...

# Define the agent module mapping
agent_modules = {
    "agent_name": "app"  # Map agent name to the app object
}

# Main function
async def main():
    api_key = "your_api_key_here"
    await run_agent_connector(api_key, agent_modules)

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration Options

### Agent Module Mapping

The `agent_modules` dictionary maps agent names to either:

1. **App objects** (direct references):
   ```python
   agent_modules = {
       "quiz_agent": app  # Reference to an App instance
   }
   ```

2. **Module paths** (strings):
   ```python
   agent_modules = {
       "quiz_agent": "my_module.app"  # String path to module with app attribute
   }
   ```

## Key Functions

### `run_agent_connector`

```python
async def run_agent_connector(api_key: str, agent_modules: Dict[str, Union[str, Any]])
```

This is the main entry point for the agent connector functionality:

| Parameter | Type | Description |
|-----------|------|-------------|
| `api_key` | str | Your Framewise API key for authentication |
| `agent_modules` | Dict[str, Union[str, Any]] | Mapping of agent names to app objects or module paths |

## Implementation Details

### Connection Handling

The Agent Connector:

- Maintains a persistent WebSocket connection to the Framewise coordination server
- Automatically reconnects with exponential backoff on connection failures
- Listens for agent start commands from the server

### Process Management

When a start command is received:

1. The connector verifies the requested agent exists in the agent_modules map
2. A new process is spawned for the agent (using Python's multiprocessing)
3. The agent process runs independently, connecting to the specified meeting
4. When the agent disconnects or errors, the process is terminated

## Advanced Usage

### Real-Time Agent Registration

You can register or unregister agents at runtime:

```python
from framewise_meet_client.agent_connector import AgentConnector

# Create the connector
connector = AgentConnector(api_key="your_key", agent_modules={})

# Register a new agent
connector.register_agent("new_agent", "module.path")

# Run the connector
await connector.connect_and_listen()
```

### Handling Multiple Agent Types

```python
# Define multiple agent apps
quiz_app = App(api_key="your_key")
support_app = App(api_key="your_key")

# Configure each app with different handlers
@quiz_app.on_transcript()
def quiz_handler(message):
    # Quiz-specific handling
    pass

@support_app.on_transcript()
def support_handler(message):
    # Support-specific handling
    pass

# Map multiple agent types
agent_modules = {
    "quiz": quiz_app,
    "support": support_app
}

# Run the connector
await run_agent_connector("your_key", agent_modules)
```

### Handling Agent Errors

To ensure your agents handle errors gracefully:

1. **Add error handling** in all event handlers
2. **Implement connection rejection handlers** to handle server-side limitations
3. **Add signal handlers** for clean shutdown

```python
import signal

@app.on_connection_rejected()
def handle_rejection(message):
    reason = message.content.reason
    logger.error(f"Connection rejected: {reason}")
    
def signal_handler(sig, frame):
    logger.info("Interrupt received, shutting down...")
    asyncio.get_event_loop().stop()

signal.signal(signal.SIGINT, signal_handler)
```

## Best Practices

1. **Use structured logging** to track agent activity and diagnose issues
2. **Handle connection rejection events** for each agent
3. **Implement proper shutdown** with signal handlers
4. **Monitor agent processes** in production environments
5. **Use unique agent names** to avoid conflicts

## Example: Complete Agent Connector Implementation

```python
import asyncio
import logging
import signal
import sys
from framewise_meet_client.app import App
from framewise_meet_client.agent_connector import run_agent_connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MyAgentConnector")

# Create App instances
quiz_app = App(api_key="your_api_key", host="backendapi.framewise.ai", port=443)
support_app = App(api_key="your_api_key", host="backendapi.framewise.ai", port=443)

# Configure quiz agent
@quiz_app.on_transcript()
def handle_quiz_transcript(message):
    # Process transcript for quiz agent
    pass

# Configure support agent
@support_app.on_transcript()
def handle_support_transcript(message):
    # Process transcript for support agent
    pass

# Add connection rejection handlers
@quiz_app.on_connection_rejected()
@support_app.on_connection_rejected()
def handle_rejection(message):
    reason = getattr(message.content, "reason", "unknown")
    logger.error(f"Connection rejected: {reason}")

# Main function
async def main():
    # Map agent names to app objects
    agent_modules = {
        "quiz": quiz_app,
        "support": support_app
    }
    
    api_key = "your_api_key"
    
    # Set up signal handling
    def signal_handler(sig, frame):
        logger.info("Interrupt received, shutting down...")
        asyncio.get_event_loop().stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the agent connector
    await run_agent_connector(api_key, agent_modules)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted")
        sys.exit(0)
```