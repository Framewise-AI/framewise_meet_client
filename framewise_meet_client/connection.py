import asyncio
import json
import logging
import websockets
from typing import Optional, Dict, Any

from .errors import ConnectionError, AuthenticationError

logger = logging.getLogger(__name__)

class WebSocketConnection:
    """Manages WebSocket connection to the server."""
    
    def __init__(self, host: str, port: int, meeting_id: str, api_key: Optional[str] = None):
        """Initialize the connection.
        
        Args:
            host: Server hostname
            port: Server port
            meeting_id: ID of the meeting to join
            api_key: Optional API key for authentication
        """
        self.host = host
        self.port = port
        self.meeting_id = meeting_id
        self.api_key = api_key
        self.websocket = None
        self.connected = False
    
    async def connect(self) -> None:
        """Connect to the WebSocket server."""
        url = f"ws://{self.host}:{self.port}/listen/{self.meeting_id}"
        
        # Add API key to headers if provided
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            logger.debug("Added API key to connection headers")
        
        try:
            self.websocket = await websockets.connect(url)
            self.connected = True
            logger.info(f"Connected to server at {url}")
            
            # Wait for auth confirmation if API key was provided
            if self.api_key:
                try:
                    # Wait for auth confirmation message with timeout
                    auth_message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    auth_data = json.loads(auth_message)
                    
                    if auth_data.get("type") == "auth_result" and not auth_data.get("success", False):
                        logger.error("Authentication rejected by server")
                        await self.disconnect()
                        raise AuthenticationError("Authentication rejected by server")
                    
                    logger.info("Server authenticated connection")
                    
                except asyncio.TimeoutError:
                    # If we don't get an explicit auth confirmation, assume it's OK
                    logger.warning("No explicit authentication confirmation from server")
                    
            
        except Exception as e:
            self.connected = False
            logger.error(f"Failed to connect: {str(e)}")
            raise ConnectionError(f"Failed to connect: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if self.websocket and self.connected:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from server")
    
    async def send(self, message: Dict[str, Any]) -> None:
        """Send a message to the server.
        
        Args:
            message: JSON-serializable message to send
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to server")
        
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise ConnectionError(f"Failed to send message: {str(e)}")
        
    
    async def send_json(self,message):
        """Send a JSON serializable message to the server.
                
        Args:
            message: JSON-serializable message to send
        """
        # This is an alias for the send method
        return await self.send(message)
    
    async def receive(self) -> Dict[str, Any]:
        """Receive a message from the server.
        
        Returns:
            Parsed JSON message from the server
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to server")
        
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            logger.warning("Connection closed")
            raise ConnectionError("Connection closed")
        except Exception as e:
            logger.error(f"Failed to receive message: {str(e)}")
            raise ConnectionError(f"Failed to receive message: {str(e)}")