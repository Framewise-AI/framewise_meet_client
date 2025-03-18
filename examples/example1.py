import logging
import uuid
from framewise_meet_client.app import App
from framewise_meet_client.models.messages import (
    TranscriptMessage, MCQSelectionMessage, JoinMessage, 
    ExitMessage, CustomUIElementMessage, ConnectionRejectedMessage
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = App(api_key="1234567")

app.create_meeting("1234")
app.join_meeting(meeting_id="1234")

@app.on_transcript()
def on_transcript(message: TranscriptMessage):
    transcript = message.content.text
    is_final = message.content.is_final
    print(f"Received transcript: {transcript}")

@app.invoke
def process_final_transcript(message: TranscriptMxessage):
    transcript = message.content.text
    print(f"Processing final transcript with invoke: {transcript}")
    
    app.send_generated_text(f"You said: {transcript}", is_generation_end=True)
    
    question_id = str(uuid.uuid4())
    app.send_mcq_question(
        question_id=question_id,
        question="How would you like to proceed?",
        options=["Continue", "Start over", "Try something else", "Exit"]
    )

@app.on("mcq_question")
def on_mcq_question_ui(message: CustomUIElementMessage):
    mcq_data = message.content.data
    selected_option = mcq_data.selectedIndex
    selected_index = mcq_data.selectedOption
    question_id = mcq_data.id
    
    print(f"MCQ question UI handler: Selected '{selected_option}' (index: {selected_index}) for question {question_id}")
    app.send_generated_text(f"UI handler received: {selected_option}", is_generation_end=True)


@app.on_custom_ui_response()
def on_mcq_question_ui(message: CustomUIElementMessage):
    subtype = message.content.type
    if subtype == "mcq_question":
        mcq_data = message.content.data
        selected_option = mcq_data.selectedIndex
        selected_index = mcq_data.selectedOption
        question_id = mcq_data.id
    
        print(f"MCQ question UI handler: Selected '{selected_option}' (index: {selected_index}) for question {question_id}")
        app.send_generated_text(f"UI handler received: {selected_option}", is_generation_end=True)


@app.on("join")
def on_user_join(message: JoinMessage):
    meeting_id = message.content.user_joined.meeting_id
    print(f"User joined meeting: {meeting_id}")
    
    app.send_generated_text(f"Welcome to meeting {meeting_id}!", is_generation_end=True)

@app.on_exit()
def on_user_exit(message: ExitMessage):
    meeting_id = message.content.user_exited.meeting_id if message.content.user_exited else "unknown"
    print(f"User exited meeting: {meeting_id}")
    app.send_generated_text("User has left the meeting.", is_generation_end=True)

# Add an example handler for connection rejected events
@app.on_connection_rejected()
def on_connection_rejected(message: ConnectionRejectedMessage):
    reason = message.content.reason
    meeting_id = message.content.meeting_id
    print(f"Connection rejected for meeting {meeting_id}: {reason}")
    # You might want to take specific actions here, like trying a different meeting ID
    # or notifying the user

if __name__ == "__main__":
    app.run(log_level="DEBUG")
