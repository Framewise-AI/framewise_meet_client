import asyncio
import json
import logging
import websockets
import ssl
from typing import Optional, Dict, Any

from .errors import ConnectionError, AuthenticationError

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """
    Manages WebSocket connection to the Framewise backend server.
    
    This class provides a robust WebSocket client implementation for communicating with
    the Framewise Meet backend. It handles connection establishment, authentication,
    message sending and receiving, and proper connection cleanup.
    
    Key features:
    - Secure WebSocket connections with SSL/TLS support
    - API key-based authentication
    - JSON message serialization and deserialization
    - Proper error handling with custom exception classes
    - Graceful connection cleanup
    
    This class is used internally by the App and AgentConnector classes
    to establish communication channels with the Framewise backend.
    """

    def __init__(
        self, host: str, port: int, meeting_id: str, api_key: Optional[str] = None
    ):
        """
        Initialize the WebSocket connection with server details and authentication.
        
        Args:
            host: Server hostname or IP address where the Framewise backend is running.
                 Example: "backend.framewise.ai" or "localhost"
            port: Server port number. Typically 443 for secure connections or 8000 for
                 local development.
            meeting_id: Unique identifier for the meeting to join. This ID must be valid
                       and correspond to an existing meeting in the Framewise system.
            api_key: Optional API key for authentication. Required for accessing protected
                    APIs and features in production environments.
        """
        self.host = host
        self.port = port
        self.meeting_id = meeting_id
        self.api_key = api_key
        self.websocket = None
        self.connected = False

    async def connect(self) -> None:
        """
        Establish a WebSocket connection to the Framewise backend server.
        
        This method:
        1. Constructs the appropriate WebSocket URL based on host, port and meeting_id
        2. Sets up any required authentication headers
        3. Establishes the WebSocket connection with appropriate SSL configuration
        4. Handles the authentication confirmation flow if an API key is provided
        
        Raises:
            ConnectionError: If the connection cannot be established due to network
                           issues, invalid host/port, or other connection problems.
            AuthenticationError: If the provided API key is rejected by the server.
            
        Note:
            This method automatically selects between secure (wss://) and regular (ws://)
            WebSocket connections based on the port number, with port 443 triggering
            secure connections with SSL certificate validation.
        """
        # Determine protocol based on port
        protocol = "wss" if self.port == 443 else "ws"
        url = f"{protocol}://{self.host}:{self.port}/listen/{self.meeting_id}"

        # Add API key to headers if provided
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            logger.debug("Added API key to connection headers")

        try:
            # For secure connections, use the default SSL context which verifies certificates
            ssl_context = None
            if protocol == "wss":
                ssl_context = ssl.create_default_context()
            
            self.websocket = await websockets.connect(
                url, 
                ssl=ssl_context
            )
            
            self.connected = True
            logger.info(f"Connected to server at {url}")

            # Wait for auth confirmation if API key was provided
            if self.api_key:
                try:
                    # Wait for auth confirmation message with timeout
                    auth_message = await asyncio.wait_for(
                        self.websocket.recv(), timeout=5.0
                    )
                    auth_data = json.loads(auth_message)

                    if auth_data.get("type") == "auth_result" and not auth_data.get(
                        "success", False
                    ):
                        logger.error("Authentication rejected by server")
                        await self.disconnect()
                        raise AuthenticationError("Authentication rejected by server")

                    logger.info("Server authenticated connection")

                except asyncio.TimeoutError:
                    # If we don't get an explicit auth confirmation, assume it's OK
                    logger.warning(
                        "No explicit authentication confirmation from server"
                    )

        except Exception as e:
            self.connected = False
            logger.error(f"Failed to connect: {str(e)}")
            raise ConnectionError(f"Failed to connect: {str(e)}")

    async def disconnect(self) -> None:
        """
        Disconnect from the WebSocket server gracefully.
        
        This method ensures that the WebSocket connection is properly closed
        and resources are released. It sets the connected flag to False to
        prevent further communication attempts on this connection.
        
        Note:
            This method should be called when the connection is no longer needed
            or before attempting to reconnect after an error.
        """
        if self.websocket and self.connected:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from server")

    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a JSON-serializable message to the server.
        
        This method serializes the provided dictionary to a JSON string
        and sends it over the WebSocket connection to the server.
        
        Args:
            message: A dictionary containing the message data to send.
                   This must be JSON-serializable.
                   
        Raises:
            ConnectionError: If the connection is not established or if
                           there's an error during message transmission.
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to server")

        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise ConnectionError(f"Failed to send message: {str(e)}")

    async def send_json(self, message):
        """
        Send a JSON serializable message to the server (alias for send).
        
        This method provides an alternative name for the send method to
        maintain a consistent API with other WebSocket implementations.
        
        Args:
            message: JSON-serializable message to send, typically a dictionary.
            
        Raises:
            ConnectionError: If the connection is not established or if
                           there's an error during message transmission.
        """
        # This is an alias for the send method
        return await self.send(message)

    async def receive(self) -> Dict[str, Any]:
        """
        Receive and parse a JSON message from the server.
        
        This method:
        1. Receives a raw string message from the WebSocket connection
        2. Parses it as JSON into a Python dictionary
        3. Returns the parsed message
        
        Returns:
            A dictionary containing the parsed JSON message from the server.
            
        Raises:
            ConnectionError: If the connection is not established, if the connection
                           is closed by the server, or if there's an error during
                           message reception or JSON parsing.
                           
        Note:
            If the connection is closed by the server, this method will set
            the connected flag to False before raising the exception.
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
