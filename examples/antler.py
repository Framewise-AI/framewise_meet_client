import asyncio
import json
import logging
from typing import Optional
from examples.utils import prepare_basis_llm_v2
from framewise_meet_client.app import App
from framewise_meet_client.models.messages import TranscriptMessage, MCQSelectionMessage, JoinMessage, ExitMessage, CustomUIElementMessage

# Load environment variables from .env file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

AGENT, llm, session_id = prepare_basis_llm_v2()

app = App(api_key="1234567")

app.create_meeting("1234")
app.join_meeting(meeting_id="1234")


async def get_openai_response(text: Optional[str] = "") -> dict:
    try:
        global llm
        global session_id
        response = llm.invoke(
            {"input": text},
            config={"configurable": {"session_id": session_id}})
        mcq = AGENT.mcq_question_tracker()
        if mcq == 'None':
            return {
                "response": response.content,
                "mcq": {"id": "23860105-0ca1-4563-ab6f-00b73936fcd2",
                        "question": "How would you like to proceed?",
                        "options": ["Continue", "Start Over", "Try Something Else", "Exit"]
                        }
            }
        else:
            return {
                "response": response.content,
                "mcq": mcq
            }

    except Exception as e:
        error_msg = f"Error getting response: {str(e)}"
        logger.error(error_msg)
        return {"response": "Sorry, I encountered an error.", "mcq": None}


@app.on_transcript()
def on_transcript(message: TranscriptMessage):
    transcript = message.content.text
    is_final = message.content.is_final
    logger.info(f"Received transcript: {transcript}, is_final: {is_final}")


@app.invoke
async def process_final_transcript(message: TranscriptMessage):
    transcript = message.content.text
    is_final = message.content.is_final

    if is_final:
        logger.info(f"Processing final transcript: {transcript}")
        response_data = await get_openai_response(transcript)

        app.send_generated_text(
            response_data["response"],
            is_generation_end=True
        )

        if 'mcq' in response_data and response_data['mcq']:
            mcq_data = response_data['mcq']
            app.send_mcq_question(
                question_id=mcq_data["id"],
                question=mcq_data["question"],
                options=mcq_data["options"]
            )


@app.on("mcq_question")
def on_mcq_question(message: CustomUIElementMessage):
    mcq_data = message.content.data
    selected_option = mcq_data.selectedOption
    selected_index = mcq_data.selectedIndex
    question_id = mcq_data.id

    logger.info(
        f"MCQ selection: '{selected_option}' (index: {selected_index}) for question {question_id}")


@app.on_custom_ui_response()
def on_mcq_response(message: CustomUIElementMessage):
    subtype = message.content.type
    if subtype == "mcq_question":
        mcq_data = message.content.data
        selected_option = mcq_data.selectedOption
        selected_index = mcq_data.selectedIndex
        question_id = mcq_data.id

        logger.info(
            f"MCQ response: Selected '{selected_option}' (index: {selected_index}) for question {question_id}")


@app.on("join")
def on_user_join(message: JoinMessage):
    meeting_id = message.content.user_joined.meeting_id
    logger.info(f"User joined meeting: {meeting_id}")

    app.send_notification(
        message="User joined",
        level="info",
        duration=8000
    )


@app.on_exit()
def on_user_exit(message: ExitMessage):
    meeting_id = message.content.user_exited
    logger.info(f"User exited meeting: {meeting_id}")


@app.on_connection_rejected()
def on_connection_rejected(message):
    reason = getattr(message, 'reason', 'Unknown reason')
    logger.error(f"Connection rejected: {reason}")


def main():
    try:
        # App is already initialized with meeting created and joined
        # Just run the app
        app.run(log_level="DEBUG")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()
