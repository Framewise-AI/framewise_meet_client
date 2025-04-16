import asyncio
import logging
import uuid
import signal
from framewise_meet_client.app import App
from framewise_meet_client.agent_connector import AgentConnector, run_agent_connector
from framewise_meet_client.models.inbound import (
    TranscriptMessage,
    MCQSelectionMessage,
    JoinMessage,
    ExitMessage,
    CustomUIElementResponse as CustomUIElementMessage,
    ConnectionRejectedMessage,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("QuizAgent")

# Create the App instance
app = App(api_key="1234567", host='backendapi.framewise.ai', port=443)

# Define the agent behavior
@app.on_transcript()
def on_transcript(message: TranscriptMessage):
    transcript = message.content.text
    is_final = message.content.is_final
    logger.info(f"Received transcript: {transcript}")

@app.invoke
def process_final_transcript(message: TranscriptMessage):
    transcript = message.content.text
    logger.info(f"Processing final transcript with invoke: {transcript}")

    app.send_generated_text(f"You said: {transcript}", is_generation_end=False)
    
    # Check if this is a quiz-related question
    if "quiz" in transcript.lower() or "question" in transcript.lower():
        send_quiz_question()
    else:
        app.send_generated_text("Ask me to start a quiz if you'd like to test your knowledge!", is_generation_end=True)

def send_quiz_question():
    question_id = str(uuid.uuid4())
    app.send_mcq_question(
        question_id=question_id,
        question="Which one of these is NOT a feature of Python?",
        options=["Dynamic typing", "Automatic garbage collection", "Strong static typing", "Interpreted language"],
    )

@app.on("mcq_question")
def on_mcq_question_ui(message):
    try:
        if isinstance(message, dict) and 'data' in message:
            mcq_data = message['data']
            selected_option = mcq_data.get('selectedOption')
            selected_index = mcq_data.get('selectedIndex')
            question_id = mcq_data.get('id')
            
            logger.info(f"MCQ selection: '{selected_option}' (index: {selected_index}) for question {question_id}")
            
            # Check if answer is correct (option "Strong static typing" is the correct answer)
            if selected_index == 2:
                app.send_generated_text("Correct! Python has dynamic typing, not static typing.", is_generation_end=True)
            else:
                app.send_generated_text(f"Not quite. '{selected_option}' is indeed a feature of Python. 'Strong static typing' is not a Python feature.", is_generation_end=True)
                
        elif hasattr(message, 'content') and hasattr(message.content, 'data'):
            # Handle as properly parsed Pydantic model
            mcq_data = message.content.data
            selected_option = mcq_data.selectedOption
            selected_index = mcq_data.selectedIndex
            question_id = mcq_data.id
            
            logger.info(f"MCQ selection: '{selected_option}' (index: {selected_index}) for question {question_id}")
            
            # Check if answer is correct (option "Strong static typing" is the correct answer)
            if selected_index == 2:
                app.send_generated_text("Correct! Python has dynamic typing, not static typing.", is_generation_end=True)
            else:
                app.send_generated_text(f"Not quite. '{selected_option}' is indeed a feature of Python. 'Strong static typing' is not a Python feature.", is_generation_end=True)
        else:
            logger.error(f"Unexpected message format: {type(message)}")
    except Exception as e:
        logger.error(f"Error handling MCQ question: {str(e)}")

@app.on("join")
def on_user_join(message: JoinMessage):
    try:
        meeting_id = message.content.meeting_id if hasattr(message.content, "meeting_id") else "unknown"
        logger.info(f"User joined meeting: {meeting_id}")
        app.send_generated_text(f"Welcome to the Quiz Bot! Ask me to start a quiz to test your knowledge.", is_generation_end=True)
    except Exception as e:
        logger.error(f"Error handling join event: {str(e)}")

@app.on_exit()
def on_user_exit(message: ExitMessage):
    try:
        meeting_id = message.content.user_exited.meeting_id if hasattr(message.content, "user_exited") and message.content.user_exited else "unknown"
        logger.info(f"User exited meeting: {meeting_id}")
    except Exception as e:
        logger.error(f"Error handling exit event: {str(e)}")

@app.on_connection_rejected()
def on_reject(message):
    try:
        if hasattr(message, 'content') and hasattr(message.content, 'reason'):
            reason = message.content.reason
        elif isinstance(message, dict) and 'content' in message:
            reason = message['content'].get('reason', 'unknown')
        else:
            reason = "unknown"
        logger.error(f"Connection rejected: {reason}")
    except Exception as e:
        logger.error(f"Error handling connection rejection: {str(e)}")

# Main function to run the agent connector
async def main():
    # Define the agent module mapping
    agent_modules = {
        "quiz": "app"
    }
    api_key = "1234567"
    
    # Run the agent connector
    await run_agent_connector(api_key, agent_modules)

if __name__ == "__main__":
    def signal_handler(sig, frame):
        logger.info("Keyboard interrupt received, shutting down...")
        asyncio.get_event_loop().stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())
