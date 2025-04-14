import asyncio
import json
import logging
import websockets
from typing import Optional
from .errors import AuthenticationError

logger = logging.getLogger(__name__)

async def await_meeting(api_key: str, host: str, port: int = 443, ws_url: Optional[str] = None, timeout: Optional[int] = None) -> Optional[str]:
    """Wait for a WebSocket message containing meeting details.
    
    Args:
        api_key: API key for authentication
        host: Server hostname
        port: Server port
        ws_url: Optional WebSocket URL to connect to.
               If not provided, constructs a URL based on host/port/api_key.
        timeout: Optional timeout in seconds. None means wait indefinitely.
        
    Returns:
        The meeting_id received from the WebSocket or None if timed out/error occurred
    """
    if not api_key:
        raise AuthenticationError("API key is required to await meetings")
        
    # Construct WebSocket URL if not provided
    if not ws_url:
        ws_url = f"wss://{host}/ws/api_key/{api_key}"
        
    logger.info(f"Connecting to WebSocket at {ws_url} and awaiting meeting details")
    
    reconnect_delay = 1
    max_reconnect_delay = 60
    meeting_id = None
    
    try:
        while not meeting_id:
            try:
                async with websockets.connect(ws_url, ping_timeout=30) as websocket:
                    logger.info("Successfully connected to WebSocket")
                    reconnect_delay = 1
                    
                    while True:
                        try:
                            # Set up timeout if specified
                            if timeout:
                                message_raw = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                            else:
                                message_raw = await websocket.recv()
                                
                            # Parse and process the message
                            try:
                                message = json.loads(message_raw)
                                logger.info(f"Received message: {message}")
                                
                                # Extract meeting details
                                meeting_id = message.get("meeting_id")
                                agent_name = message.get("agent_name", "unnamed_agent")
                                
                                if meeting_id:
                                    logger.info(f"Received meeting ID: {meeting_id} for agent: {agent_name}")
                                    return meeting_id
                                else:
                                    logger.warning("Received message without meeting_id")
                                    
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse message: {message_raw}")
                                
                        except asyncio.TimeoutError:
                            logger.warning(f"Timed out after {timeout} seconds waiting for meeting details")
                            return None
                            
                        except Exception as e:
                            logger.error(f"Error receiving/handling message: {str(e)}")
                            break
                            
            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                logger.info(f"Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                
    except KeyboardInterrupt:
        logger.info("Awaiting meeting interrupted by user")
        
    return meeting_id
