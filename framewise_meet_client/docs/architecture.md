# Framewise Meet Client Architecture

## Overview

The Framewise Meet Client is structured around an event-driven architecture. It processes various types of messages and dispatches them to the appropriate handlers.

## Key Components

### App
The central class that provides the main API for the client. It handles registration of event handlers and manages the connection lifecycle.

### EventDispatcher
Responsible for routing events to the appropriate handlers.

### EventHandlers
Various handler classes that process specific event types:
- `TranscriptHandler`: Handles transcript events
- `JoinHandler`: Handles join events
- `ExitHandler`: Handles exit events
- `CustomUIHandler`: Handles UI element responses
- `InvokeHandler`: Handles invoke events
- `ConnectionRejectedHandler`: Handles connection rejection events

### Models
Data models for both inbound and outbound messages:
- `inbound.py`: Contains models for messages received from the server
- `outbound.py`: Contains models for messages sent to the server

### Messaging
`MessageSender` class that handles sending formatted messages to the server.

### Runner
`AppRunner` manages the application's main event loop and connection lifecycle.

## Flow of Events

1. Messages are received from the WebSocket connection
2. Messages are parsed into appropriate model classes
3. Events are dispatched to registered handlers based on message type
4. UI element responses may be further dispatched to specific handlers based on element type

## UI Element Handling

Custom UI elements, such as MCQ questions, have a special handling mechanism. When a custom UI element response is received:
1. The standard handler for `CUSTOM_UI_EVENT` is invoked
2. The element type is extracted from the message
3. If there's a specific handler registered for that UI element type, it's invoked as well
