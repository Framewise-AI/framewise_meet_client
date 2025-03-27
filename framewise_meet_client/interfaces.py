"""Interface definitions to improve code structure and testing."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable, Generic, TypeVar, List, Union
import asyncio

T = TypeVar('T')

class Connection(ABC):
    """Abstract interface for connections."""
    
    @property
    @abstractmethod
    def connected(self) -> bool:
        """Return whether the connection is established."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection."""
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
    """Abstract interface for event dispatchers."""
    
    @abstractmethod
    def register_handler(self, event_type: str) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
        """Register a handler for the given event type."""
        pass
    
    @abstractmethod
    async def dispatch(self, event_type: str, data: Any) -> None:
        """Dispatch an event to registered handlers."""
        pass

class UIElementFactory(ABC):
    """Abstract factory for creating UI elements."""
    
    @abstractmethod
    def create_mcq_question(self, question_id: str, question: str, options: List[str], 
                           image_path: Optional[str] = None) -> Dict[str, Any]:
        """Create an MCQ question UI element."""
        pass
    
    @abstractmethod
    def create_notification(self, notification_id: str, text: str, level: str = "info", 
                           duration: int = 8000, color: Optional[str] = None) -> Dict[str, Any]:
        """Create a notification UI element."""
        pass
    
    # Add other factory methods for different element types
