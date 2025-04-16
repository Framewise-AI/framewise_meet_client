import asyncio
import json
import logging
import sys
import websockets
import importlib
import multiprocessing
from typing import Dict, Optional, Any, Callable, Union

from .errors import ConnectionError, AuthenticationError

logger = logging.getLogger("AgentConnector")

class AgentConnector:
    """
    Connector for agent management and coordination.
    
    This class handles WebSocket connections to receive agent start commands
    and manages spawning agent processes.
    """
    
    def __init__(self, api_key: str, agent_modules: Dict[str, Union[str, Any]]):
        """Initialize the agent connector.
        
        Args:
            api_key: API key for authentication
            agent_modules: Mapping of agent names to either:
                           - module paths (string)
                           - app objects (direct references)
        """
        self.api_key = api_key
        self.ws_url = f"wss://backend.framewise.ai/ws/api_key/{api_key}"
        self.running = False
        self.active_agents = {}  # Keep track of running agent processes
        self.agent_modules = agent_modules
        self.websocket = None
        
    async def connect_and_listen(self):
        """Connect to WebSocket and listen for agent start commands."""
        self.running = True
        logger.info(f"Connecting to WebSocket at {self.ws_url}")
        
        reconnect_delay = 1
        max_reconnect_delay = 60
        
        while self.running:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.websocket = websocket
                    logger.info("Successfully connected to WebSocket")
                    reconnect_delay = 1
                    
                    while self.running:
                        try:
                            message = await websocket.recv()
                            await self.handle_message(message)
                        except websockets.exceptions.ConnectionClosed:
                            logger.error("WebSocket connection closed")
                            break
                        except Exception as e:
                            logger.error(f"Error receiving/handling message: {str(e)}")
                            break
                    
            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                if self.running:
                    logger.info(f"Reconnecting in {reconnect_delay} seconds...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
    
    async def handle_message(self, message_raw):
        """Process received WebSocket message.
        
        Args:
            message_raw: Raw message string from WebSocket
        """
        try:
            message = json.loads(message_raw)
            logger.info(f"Received message: {message}")
            
            agent_name = message.get("agent_name")
            meeting_id = message.get("meeting_id")
            
            if agent_name and meeting_id:
                logger.info(f"Starting agent {agent_name} for meeting {meeting_id}")
                # Always create a new process, don't reuse existing ones
                self.start_agent_process(agent_name, meeting_id)
            else:
                logger.warning(f"Received message without agent_name or meeting_id: {message}")
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse message: {message_raw}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    def start_agent_process(self, agent_name: str, meeting_id: str) -> bool:
        """Start an agent in a separate process.
        
        Args:
            agent_name: Name of the agent to start
            meeting_id: Meeting ID to connect the agent to
            
        Returns:
            True if agent was started successfully, False otherwise
        """
        if agent_name not in self.agent_modules:
            logger.error(f"Unknown agent: {agent_name}")
            return False
        
        try:
            agent_value = self.agent_modules[agent_name]
            
            # Determine if the agent_value is a module path or an app object
            if isinstance(agent_value, str):
                # It's a module path, define the process function to import it
                def run_agent_process():
                    try:
                        agent_module = importlib.import_module(agent_value)
                        if hasattr(agent_module, 'app'):
                            # Use app.join_meeting() instead of init_meeting()
                            agent_module.app.join_meeting(meeting_id)
                            agent_module.app.run(log_level="DEBUG")
                        else:
                            logger.error(f"Agent module {agent_name} does not have 'app' attribute")
                    except Exception as e:
                        logger.error(f"Error in agent process: {str(e)}")
            else:
                # It's an app object, define the process function to use it directly
                def run_agent_process():
                    try:
                        # Use the app object directly
                        app_object = agent_value
                        app_object.join_meeting(meeting_id)
                        app_object.run(log_level="DEBUG")
                    except Exception as e:
                        logger.error(f"Error in agent process: {str(e)}")
            
            # Start new process
            process = multiprocessing.Process(target=run_agent_process)
            process.daemon = True
            process.start()
            
            # Generate a unique ID for this process instance
            process_id = f"{agent_name}_{meeting_id}_{id(process)}"
            
            # Track the process
            self.active_agents[process_id] = process
            logger.info(f"Started agent process: {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting agent {agent_name}: {str(e)}")
            return False
    
    def stop(self):
        """Stop the connector and cleanup resources."""
        logger.info("Stopping agent connector...")
        self.running = False
        
        # Terminate any running agent processes
        for process_id, process in self.active_agents.items():
            if process.is_alive():
                logger.info(f"Terminating agent process: {process_id}")
                process.terminate()
                
        self.active_agents.clear()

    def register_agent(self, name: str, module_path_or_app_object: Union[str, Any]):
        """Register a new agent type.
        
        Args:
            name: Agent name
            module_path_or_app_object: Either a module path (string) or an app object
        """
        self.agent_modules[name] = module_path_or_app_object
        logger.info(f"Registered agent '{name}'")
        
    def unregister_agent(self, name: str):
        """Unregister an agent type.
        
        Args:
            name: Agent name to unregister
        """
        if name in self.agent_modules:
            del self.agent_modules[name]
            logger.info(f"Unregistered agent '{name}'")

async def run_agent_connector(api_key: str, agent_modules: Dict[str, Union[str, Any]]):
    """Run an agent connector instance.
    
    Args:
        api_key: API key for authentication
        agent_modules: Mapping of agent names to either module paths (string) or app objects
    """
    connector = AgentConnector(api_key=api_key, agent_modules=agent_modules)
    
    try:
        await connector.connect_and_listen()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        connector.stop()
        await asyncio.sleep(1)  # Allow time for cleanup