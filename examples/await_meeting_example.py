import asyncio
import logging
from framewise_meet_client.app import App
from framewise_meet_client.models.inbound import TranscriptMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize app with your API key
app = App(api_key="YOUR_API_KEY_HERE", host="backendapi.framewise.ai", port=443)

# Register event handlers
@app.on_transcript()
def handle_transcript(message: TranscriptMessage):
    logger.info(f"Received transcript: {message.content.text}")
    if message.content.is_final:
        app.send_text("I received your message!")

@app.on("join")
def handle_join(message):
    logger.info(f"User joined meeting")
    app.send_text("Welcome to the meeting! I'm an auto-joining bot.")

async def main():
    # Method 1: Await meeting and then run the app
    meeting_id = await app.await_meeting()
    if meeting_id:
        logger.info(f"Successfully joined meeting: {meeting_id}")
        app.run()
    else:
        logger.error("Failed to join any meeting")

if __name__ == "__main__":
    asyncio.run(main())
