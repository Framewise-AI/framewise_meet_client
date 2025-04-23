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
    """
    Event handler for incoming transcript messages.
    
    This function is triggered whenever a transcript message is received from
    the Framewise API, whether it's an interim or final transcript. It logs
    the received transcript for monitoring purposes.
    
    Args:
        message (TranscriptMessage): A message object containing the transcript text
            and metadata such as whether it's a final transcript.
    """
    transcript = message.content.text
    is_final = message.content.is_final
    logger.info(f"Received transcript: {transcript}")

@app.invoke
def process_final_transcript(message: TranscriptMessage):
    """
    Process final transcript messages for interactive responses.
    
    This function is decorated with @app.invoke, meaning it automatically receives
    transcript messages that are marked as final (completed utterances). It analyzes
    the transcript content and responds appropriately, either by starting a quiz or
    providing information about available interactions.
    
    Args:
        message (TranscriptMessage): A message object containing the final transcript 
            text and related metadata.
    """
    transcript = message.content.text
    logger.info(f"Processing final transcript with invoke: {transcript}")

    app.send_generated_text(f"You said: {transcript}", is_generation_end=False)
    
    # Check if this is a quiz-related question
    if "quiz" in transcript.lower() or "question" in transcript.lower():
        send_quiz_question()
    else:
        app.send_generated_text("Ask me to start a quiz if you'd like to test your knowledge!", is_generation_end=True)

def send_quiz_question():
    """
    Sends a multiple-choice question to the user.
    
    This function creates and sends a pre-defined quiz question about Python features.
    It generates a unique UUID for the question ID to track responses correctly.
    The question asks the user to identify which option is NOT a feature of Python,
    with "Strong static typing" being the correct answer.
    
    Returns:
        None: This function sends the MCQ question to the Framewise API but does not return a value.
    """
    question_id = str(uuid.uuid4())
    app.send_mcq_question(
        question_id=question_id,
        question="Which one of these is NOT a feature of Python?",
        options=["Dynamic typing", "Automatic garbage collection", "Strong static typing", "Interpreted language"],
    )

@app.on("mcq_question")
def on_mcq_question_ui(message):
    """
    Event handler for MCQ (Multiple Choice Question) responses.
    
    This function processes user responses to multiple-choice quiz questions.
    It supports two different message formats:
    1. Dictionary format (for direct API responses)
    2. Pydantic model format (for parsed responses)
    
    The handler provides appropriate feedback based on the selected answer,
    with index 2 ("Strong static typing") being the correct answer.
    
    Args:
        message: A message object containing the user's MCQ selection, either
            as a dictionary or as a parsed Pydantic model.
            
    Raises:
        Exception: Logs any errors that occur during processing.
    """
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
    """
    Event handler for user join events.
    
    This function is triggered whenever a user joins a meeting. It logs the meeting ID
    and sends a welcome message to the new participant introducing the Quiz Bot's
    functionality.
    
    Args:
        message (JoinMessage): A message object containing information about the
            user who joined and the meeting they joined.
            
    Raises:
        Exception: Logs any errors that occur during processing.
    """
    try:
        meeting_id = message.content.meeting_id if hasattr(message.content, "meeting_id") else "unknown"
        logger.info(f"User joined meeting: {meeting_id}")
        app.send_generated_text(f"Welcome to the Quiz Bot! Ask me to start a quiz to test your knowledge.", is_generation_end=True)
    except Exception as e:
        logger.error(f"Error handling join event: {str(e)}")

@app.on_exit()
def on_user_exit(message: ExitMessage):
    """
    Event handler for user exit events.
    
    This function is triggered whenever a user leaves a meeting. It logs the meeting ID
    from which the user exited for monitoring purposes. No response is sent since the
    user has already left.
    
    Args:
        message (ExitMessage): A message object containing information about the
            user who left and the meeting they exited.
            
    Raises:
        Exception: Logs any errors that occur during processing.
    """
    try:
        meeting_id = message.content.user_exited.meeting_id if hasattr(message.content, "user_exited") and message.content.user_exited else "unknown"
        logger.info(f"User exited meeting: {meeting_id}")
    except Exception as e:
        logger.error(f"Error handling exit event: {str(e)}")

@app.on_connection_rejected()
def on_reject(message):
    """
    Event handler for connection rejection events.
    
    This function is triggered when a connection attempt to the Framewise API is rejected.
    It handles rejection messages in both object format and dictionary format, extracting
    the rejection reason and logging it for troubleshooting.
    
    Args:
        message: A message object containing the rejection reason, either as a
            structured object or as a dictionary.
            
    Raises:
        Exception: Logs any errors that occur during processing.
    """
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


async def main():
    """
    Main entry point for the Quiz Agent application.
    
    This function initializes and runs the agent connector with the configured Quiz agent.
    The agent connector manages the lifecycle of the agent, including:
    - Establishing and maintaining WebSocket connections
    - Handling authentication with the Framewise API
    - Managing reconnection attempts on connection failures
    - Routing messages between the agent and the Framewise backend
    
    Returns:
        None: This function runs indefinitely until interrupted.
    
    Raises:
        ConnectionError: If unable to establish connection with the Framewise API.
        AuthenticationError: If API key authentication fails.
    """
    # Correct way to map the agent name to the app object
    agent_modules = {
        "quiz": app  # Reference to the App instance, not a string
    }
    api_key = "1234567"
    await run_agent_connector(api_key, agent_modules)

if __name__ == "__main__":
    def signal_handler(sig, frame):
        """
        Signal handler for gracefully shutting down the application.
        
        This function is registered to handle SIGINT (Ctrl+C) signals, ensuring
        that the application performs a clean shutdown by stopping the asyncio
        event loop.
        
        Args:
            sig (int): Signal number.
            frame (frame): Current stack frame.
        """
        logger.info("Keyboard interrupt received, shutting down...")
        asyncio.get_event_loop().stop()

    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())
