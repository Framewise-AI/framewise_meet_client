import logging
import uuid
from framewise_meet_client.app import App
from framewise_meet_client.models.inbound import (
    TranscriptMessage,
    MCQSelectionMessage,
    JoinMessage,
    ExitMessage,
    CustomUIElementResponse as CustomUIElementMessage,
    ConnectionRejectedMessage,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = App(api_key="1234567", host='backendapi.framewise.ai', port=443)

app.create_meeting("1234")


@app.on_transcript()
def on_transcript(message: TranscriptMessage):
    transcript = message.content.text
    is_final = message.content.is_final
    print(f"Received transcript: {transcript}")


@app.invoke
def process_final_transcript(message: TranscriptMessage):
    transcript = message.content.text
    print(f"Processing final transcript with invoke: {transcript}")

    app.send_generated_text(f"You said: {transcript}", is_generation_end=True)

    question_id = str(uuid.uuid4())
    app.send_mcq_question(
        question_id=question_id,
        question="How would you like to proceed?",
        options=["Continue", "Start over", "Try something else", "Exit"],
    )


@app.on("mcq_question")
def on_mcq_question_ui(message):
    # Handle the message directly as a dictionary to avoid model validation issues
    try:
        if isinstance(message, dict) and 'data' in message:
            mcq_data = message['data']
            selected_option = mcq_data.get('selectedOption')
            selected_index = mcq_data.get('selectedIndex')
            question_id = mcq_data.get('id')
            
            print(
                f"MCQ question UI handler: Selected '{selected_option}' (index: {selected_index}) for question {question_id}"
            )
            app.send_generated_text(
                f"UI handler received: {selected_option}", is_generation_end=True
            )
        elif hasattr(message, 'content') and hasattr(message.content, 'data'):
            # Handle as properly parsed Pydantic model
            mcq_data = message.content.data
            selected_option = mcq_data.selectedOption
            selected_index = mcq_data.selectedIndex
            question_id = mcq_data.id
            
            print(
                f"MCQ question UI handler: Selected '{selected_option}' (index: {selected_index}) for question {question_id}"
            )
            app.send_generated_text(
                f"UI handler received: {selected_option}", is_generation_end=True
            )
        else:
            logging.error(f"Unexpected message format: {type(message)}")
    except Exception as e:
        logging.error(f"Error handling MCQ question: {str(e)}")


@app.on_custom_ui_response()
def on_custom_ui_response(message):
    # Handle the message directly as a dictionary to avoid model validation issues
    try:
        if isinstance(message, dict):
            # Access as dictionary
            subtype = message.get('content', {}).get('type')
            if subtype == "mcq_question":
                mcq_data = message.get('content', {}).get('data', {})
                selected_option = mcq_data.get('selectedOption')
                selected_index = mcq_data.get('selectedIndex')
                question_id = mcq_data.get('id')

                print(
                    f"Custom UI response handler: Selected '{selected_option}' (index: {selected_index}) for question {question_id}"
                )
                app.send_generated_text(
                    f"UI handler received: {selected_option}", is_generation_end=True
                )
        elif hasattr(message, 'content') and hasattr(message.content, 'type'):
            # Handle as properly parsed Pydantic model
            subtype = message.content.type
            if subtype == "mcq_question" and hasattr(message.content, 'data'):
                mcq_data = message.content.data
                selected_option = mcq_data.selectedOption
                selected_index = mcq_data.selectedIndex
                question_id = mcq_data.id

                print(
                    f"Custom UI response handler: Selected '{selected_option}' (index: {selected_index}) for question {question_id}"
                )
                app.send_generated_text(
                    f"UI handler received: {selected_option}", is_generation_end=True
                )
        else:
            logging.error(f"Unexpected message format in custom UI response: {type(message)}")
    except Exception as e:
        logging.error(f"Error handling custom UI response: {str(e)}")


@app.on("join")
def on_user_join(message: JoinMessage):
    # Use proper Pydantic model access
    meeting_id = message.content.meeting_id
    print(f"User joined meeting: {meeting_id}")

    app.send_generated_text(f"Welcome to meeting {meeting_id}!", is_generation_end=True)


@app.on_exit()
def on_user_exit(message: ExitMessage):
    # Use proper Pydantic model access with null safety
    meeting_id = message.content.user_exited.meeting_id if hasattr(message.content, "user_exited") and message.content.user_exited else "unknown"
    print(f"User exited meeting: {meeting_id}")
    app.send_generated_text("User has left the meeting.", is_generation_end=True)


@app.on_connection_rejected()
def on_reject(message):
    try:
        # Try to access as Pydantic model first
        if hasattr(message, 'content') and hasattr(message.content, 'reason'):
            reason = message.content.reason
        # Fall back to dictionary access
        elif isinstance(message, dict) and 'content' in message:
            reason = message['content'].get('reason', 'unknown')
        else:
            reason = "unknown"
        print(f"Connection rejected: {reason}")
    except Exception as e:
        logging.error(f"Error handling connection rejection: {str(e)}")


if __name__ == "__main__":
    app.run(log_level="DEBUG",mode="discover")
