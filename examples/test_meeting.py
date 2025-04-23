import asyncio
import logging
from framewise_meet_client.agent_connector import AgentConnector, run_agent_connector

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MeetingDiscovery")

async def main():
    try:
        # Create an AgentConnector instance
        connector = AgentConnector(api_key=1234567,agent_modules={})
        
        # Register kk.py as the command to be executed when a meeting is discovered
        connector.register_command("python kk.py")
        
        logger.info("Registered command: python kk.py")
        logger.info("Starting meeting discovery...")
        
        # Run the agent connector to discover meetings
        # This will execute the registered command when meetings are found
        await connector.connect_and_listen()
        
    except Exception as e:
        logger.error(f"Error running meeting discovery: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Meeting discovery stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")