import asyncio
import json
import logging
import sys
import websockets
import importlib
import multiprocessing
from typing import Dict, Optional, Any, Callable, Union
from .errors import ConnectionError, AuthenticationError
import subprocess

logger = logging.getLogger("AgentConnector")

class AgentConnector:
    """
    Connector for agent management and coordination in the Framewise Meet system.
    
    The AgentConnector serves as an intermediary between the Framewise backend and
    agent instances. It maintains a WebSocket connection to receive agent start commands
    from the backend and manages the lifecycle of agent processes, starting them in 
    separate processes for isolation and stability.
    
    Key features:
    - WebSocket connection to the Framewise backend for receiving agent commands
    - Dynamic agent process management with multiprocessing
    - Automatic reconnection with exponential backoff
    - Support for both module path-based and direct app object-based agent registration
    - Process tracking and cleanup
    
    This class is typically used in a server-side deployment to dynamically start
    agent instances in response to meeting join events.
    """
    
    def __init__(self, api_key: str, agent_modules: Dict[str, Union[str, Any]]):
        """
        Initialize the agent connector with authentication and agent configuration.
        
        Args:
            api_key: API key for authentication with the Framewise backend.
                    This key is used to establish the WebSocket connection and
                    authorize agent operations.
            agent_modules: Mapping of agent names to either:
                          - module paths (string) that will be dynamically imported
                          - app objects (direct references) that will be used directly
                          
                          Example: {"quiz_agent": "myagents.quiz", "support_agent": app_instance}
        """
        self.api_key = api_key
        self.ws_url = f"wss://backend.framewise.ai/ws/api_key/{api_key}"
        self.running = False
        self.active_agents = {}  # Keep track of running agent processes
        self.agent_modules = agent_modules
        self.websocket = None
        self.command = None
        
    async def connect_and_listen(self):
        """
        Connect to the WebSocket endpoint and listen for agent start commands.
        
        This method establishes a persistent WebSocket connection to the Framewise
        backend and listens for incoming commands. It implements an exponential
        backoff reconnection strategy to handle temporary connection failures.
        
        The method runs indefinitely until the connector is explicitly stopped,
        providing continuous service for agent management.
        
        Raises:
            ConnectionError: If there's a persistent failure to connect to the WebSocket.
            AuthenticationError: If the API key is rejected by the server.
        """
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
        """
        Process received WebSocket messages and take appropriate actions.
        
        This method parses incoming JSON messages and processes agent start
        commands by extracting the agent name and meeting ID, then launching
        the appropriate agent process.
        
        Args:
            message_raw: Raw message string from the WebSocket connection.
                       Expected format: {"agent_name": "agent_id", "meeting_id": "meeting_id"}
                       
        Note:
            Any errors during message parsing or agent startup are caught and logged
            to prevent the WebSocket connection from terminating.
        """
        try:
            message = json.loads(message_raw)
            logger.info(f"Received message: {message}")
            
            agent_name = message.get("agent_name")
            meeting_id = message.get("meeting_id")
            
            if agent_name and meeting_id:
                logger.info(f"Starting agent {agent_name} for meeting {meeting_id}")
                # Always create a new process, don't reuse existing ones
                self.command_manager(meeting_id=meeting_id)
                self.start_agent_process(agent_name, meeting_id)
            else:
                logger.warning(f"Received message without agent_name or meeting_id: {message}")
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse message: {message_raw}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    def command_manager(self, meeting_id):
        """Execute a system command with meeting_id as an argument.
        
        Args:
            command: The shell command to execute
            meeting_id: The meeting ID to pass as an argument
            
        Returns:
            The return code of the command execution
        """
        try:
            logger.info(f"Executing command: {self.command} with meeting_id: {meeting_id}")
            
            # Run the command with meeting_id as an argument
            process = subprocess.run(f"{self.command} {meeting_id}", shell=True, check=False)
            
            if process.returncode == 0:
                logger.info(f"Command executed successfully")
            else:
                logger.error(f"Command execution failed with return code: {process.returncode}")
                
            return process.returncode
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return -1
    
    def register_command(self,command):
        self.command = command
    
    def start_agent_process(self, agent_name: str, meeting_id: str) -> bool:
        """
        Start an agent in a separate process to handle a specific meeting.
        
        This method creates a new process for the requested agent and meeting,
        either by dynamically importing a module or using a directly provided
        app object. The agent process is tracked for lifecycle management.
        
        Args:
            agent_name: Name of the agent to start, must match a key in agent_modules.
            meeting_id: Meeting ID to connect the agent to.
            
        Returns:
            bool: True if the agent was started successfully, False otherwise.
            
        Note:
            Each agent process is isolated and runs independently, which prevents
            issues in one agent from affecting others. The process is tracked in
            the active_agents dictionary for later cleanup.
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
        """
        Stop the connector and clean up all resources.
        
        This method:
        1. Sets the running flag to False to stop the main loop
        2. Terminates all active agent processes
        3. Clears the active_agents registry
        
        It should be called when shutting down the application or when the
        connector is no longer needed to ensure proper resource cleanup.
        """
        logger.info("Stopping agent connector...")
        self.running = False
        
        # Terminate any running agent processes
        for process_id, process in self.active_agents.items():
            if process.is_alive():
                logger.info(f"Terminating agent process: {process_id}")
                process.terminate()
                
        self.active_agents.clear()

    def register_agent(self, name: str, module_path_or_app_object: Union[str, Any]):
        """
        Register a new agent type with the connector.
        
        This method allows dynamic registration of agents after the connector
        has been initialized, providing flexibility for runtime configuration.
        
        Args:
            name: Agent name identifier used in start commands.
            module_path_or_app_object: Either:
                                      - A module path (string) that will be imported when starting the agent
                                      - An app object (reference) that will be used directly
                                      
        Example:
            ```python
            connector.register_agent("my_agent", "mypackage.myagent")
            connector.register_agent("direct_agent", app_instance)
            ```
        """
        self.agent_modules[name] = module_path_or_app_object
        logger.info(f"Registered agent '{name}'")
        
    def unregister_agent(self, name: str):
        """
        Unregister an agent type from the connector.
        
        This method removes an agent from the registry, preventing it from being
        started in response to future commands. It does not affect already running
        agent processes.
        
        Args:
            name: Agent name to unregister.
        """
        if name in self.agent_modules:
            del self.agent_modules[name]
            logger.info(f"Unregistered agent '{name}'")

async def run_agent_connector(api_key: str, agent_modules: Dict[str, Union[str, Any]]):
    """
    Run an agent connector instance as a standalone service.
    
    This convenience function creates an AgentConnector instance and runs it until
    interrupted. It handles proper shutdown when the process receives a keyboard
    interrupt (Ctrl+C).
    
    Args:
        api_key: API key for authentication with the Framewise backend.
        agent_modules: Mapping of agent names to either module paths (strings) or app objects.
        
    Example:
        ```python
        agent_modules = {
            "quiz": "myagents.quiz_agent",
            "support": app_instance
        }
        asyncio.run(run_agent_connector("api_key_12345", agent_modules))
        ```
    """
    connector = AgentConnector(api_key=api_key, agent_modules=agent_modules)
    
    try:
        await connector.connect_and_listen()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        connector.stop()
        await asyncio.sleep(1)  # Allow time for cleanup