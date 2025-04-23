"""
Abstract interface definitions for the Framewise Meet client framework.

This module defines abstract base classes (ABCs) that specify the required
methods and properties for pluggable components such as connections,
event dispatchers, and UI element factories. These interfaces improve
testability and allow custom implementations to be provided.

Implementations:
    - WebSocketConnection implements Connection
    - EventDispatcher implements EventDispatcherInterface
    - MessageSender uses UI element factory internally
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable, Generic, TypeVar, List, Union
import asyncio

T = TypeVar('T')

class Connection(ABC):
    """
    Abstract interface for connection objects.

    Defines the required methods and properties for transport layers,
    allowing WebSocket or other communication protocols to be used interchangeably.
    """
    
    @property
    @abstractmethod
    def connected(self) -> bool:
        """Return True if the connection is currently established."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection to the remote server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection and release resources."""
        pass
    
    @abstractmethod
    async def send(self, data: Dict[str, Any]) -> None:
        """Send data over the connection."""
        pass
    
    @abstractmethod
    async def receive(self) -> Dict[str, Any]:
        """Receive data from the connection."""
        pass

class EventDispatcherInterface(ABC):
    """
    Abstract interface for event dispatchers.

    Specifies the API for registering event handlers and dispatching events
    without prescribing a specific implementation.
    """

    @abstractmethod
    def register_handler(self, event_type: str) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
        """
        Register a handler function for the given event type.

        Returns a decorator that wraps handler functions.
        """
        pass
    
    @abstractmethod
    async def dispatch(self, event_type: str, data: Any) -> None:
        """
        Dispatch an event to all registered handlers for the given event type.
        """
        pass

class UIElementFactory(ABC):
    """
    Abstract factory for creating UI element payloads.

    Defines the methods required to generate JSON-compatible dictionaries
    for various UI components, such as multiple-choice questions or notifications.
    """

    @abstractmethod
    def create_mcq_question(
        self,
        question_id: str,
        question: str,
        options: List[str],
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a dictionary for an MCQ question element."""
        pass
    
    @abstractmethod
    def create_notification(
        self,
        notification_id: str,
        text: str,
        level: str = "info",
        duration: int = 8000,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a dictionary for a notification element."""
        pass
    
    # Add other factory methods for different element types
