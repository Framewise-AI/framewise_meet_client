import logging
import uuid
import time
import sys
import json
from framewise_meet_client.app import App
from framewise_meet_client.models.inbound import (
    TranscriptMessage,
    MCQSelectionMessage,
    JoinMessage,
    ExitMessage,
    CustomUIElementResponse as CustomUIElementMessage,
    ConnectionRejectedMessage,
)

# Configure more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("ui_demo")

# Initialize app with API key
app = App(api_key="1234567", host='backendapi.framewise.ai', port=443)

# Track sent UI elements to help debug
sent_elements = {
    "notification": 0,
    "mcq_question": 0,
    "places_autocomplete": 0,
    "upload_file": 0,
    "textinput": 0,
    "consent_form": 0,
    "calendly": 0
}

# Track received responses
received_responses = dict(sent_elements)

# Track connection state
connection_state = {
    "connected": False,
    "authenticated": False,
    "rejected_reason": None,
    "current_meeting_id": None
}

# Use a fixed meeting ID - don't create, just join
MEETING_ID = "46234"
connection_state["current_meeting_id"] = MEETING_ID

# Join existing meeting instead of creating a new one
logger.info(f"Joining existing meeting with ID: {MEETING_ID}")
app.join_meeting(meeting_id=MEETING_ID)


@app.on_transcript()
def on_transcript(message: TranscriptMessage):
    transcript = message.content.text
    is_final = message.content.is_final
    print(f"Received transcript: {transcript}")
    
    # If this is a final transcript, check for commands
    if is_final:
        transcript_lower = transcript.lower()
        
        # Handle specific commands for UI elements
        if "show all" in transcript_lower or "show ui elements" in transcript_lower:
            app.send_generated_text("I'll demonstrate all UI elements one by one...", is_generation_end=True)
            schedule_ui_element_demonstration()
            return
            
        # Check for specific element requests and handle them immediately
        elif "show notification" in transcript_lower:
            app.send_generated_text("Showing notification:", is_generation_end=True)
            send_notification_demo()
            return
        elif "show mcq" in transcript_lower:
            app.send_generated_text("Showing multiple choice question:", is_generation_end=True)
            send_mcq_demo()
            return
        elif "show places" in transcript_lower:
            app.send_generated_text("Showing places autocomplete:", is_generation_end=True)
            send_places_demo()
            return
        elif "show upload" in transcript_lower:
            app.send_generated_text("Showing file upload:", is_generation_end=True)
            send_upload_demo()
            return
        elif "show text input" in transcript_lower:
            app.send_generated_text("Showing text input:", is_generation_end=True)
            send_text_input_demo()
            return
        elif "show consent" in transcript_lower:
            app.send_generated_text("Showing consent form:", is_generation_end=True)
            send_consent_demo()
            return
        elif "show calendly" in transcript_lower:
            app.send_generated_text("Showing Calendly scheduler:", is_generation_end=True)
            send_calendly_demo()
            return
        elif "help" in transcript_lower or "what can you do" in transcript_lower:
            app.send_generated_text("I can demonstrate various UI elements. Say 'show ui elements' to see all, or 'show [element name]' to see a specific one.", is_generation_end=True)
            send_ui_element_menu()
            return
            
        # Default response with confirmation and menu
        app.send_generated_text(f"You said: {transcript}", is_generation_end=True)
        app.send_generated_text("Would you like to see any UI elements? Choose from the menu:", is_generation_end=False)
        send_ui_element_menu()


def show_all_ui_elements_sequence():
    """Show all UI elements with a clear introduction for each"""
    # Check if connected before sending elements
    if not connection_state["connected"]:
        logger.warning("Cannot show UI elements: Not connected to server")
        app.send_generated_text("Cannot show UI elements: Not connected to server", is_generation_end=True)
        return
        
    app.send_generated_text("Demonstrating all UI elements in sequence...", is_generation_end=False)
    
    # For each element, check element availability before sending
    elements_to_show = [
        ("notification", send_notification_demo),
        ("mcq_question", send_mcq_demo),
        ("places_autocomplete", send_places_demo),
        ("upload_file", send_upload_demo),
        ("textinput", send_text_input_demo),
        ("consent_form", send_consent_demo),
        ("calendly", send_calendly_demo)
    ]
    
    for name, send_func in elements_to_show:
        # Check element availability before sending
        if check_element_availability(name):
            app.send_generated_text(f"Demonstrating {name}:", is_generation_end=False)
            send_func()
            # Small pause to ensure elements don't get overwhelmed
            time.sleep(2)
        else:
            app.send_generated_text(f"Element {name} is not available in this API version", is_generation_end=False)
    
    app.send_generated_text("All available UI elements have been demonstrated!", is_generation_end=True)
    # Finally, show the menu of choices again
    send_ui_element_menu()


def check_element_availability(element_type):
    """Check if a UI element type is available in the API"""
    # For this example, we'll assume all elements are available except when explicitly disabled
    # In a real implementation, you might query capabilities from the server
    
    # Check if the corresponding method exists in the App class
    method_name = f"send_{element_type}"
    if element_type == "mcq_question":
        return True  # MCQ questions are definitely supported
    
    has_method = hasattr(app, method_name)
    logger.info(f"Checking availability of {element_type}: {'Available' if has_method else 'Not available'}")
    return has_method


def send_ui_element_menu():
    """Send an MCQ menu for selecting UI elements to demonstrate"""
    question_id = str(uuid.uuid4())
    logger.info(f"SENDING UI ELEMENT MENU with ID: {question_id}")
    
    try:
        app.send_mcq_question(
            question_id=question_id,
            question="Which UI element would you like to see?",
            options=[
                "Show All Elements", 
                "Notification", 
                "MCQ Question",
                "Places Autocomplete", 
                "File Upload", 
                "Text Input", 
                "Consent Form", 
                "Calendly"
            ],
        )
        sent_elements["mcq_question"] += 1
        logger.info(f"✓ UI element menu sent successfully (total: {sent_elements['mcq_question']})")
    except Exception as e:
        logger.error(f"❌ Error sending UI element menu: {str(e)}")
        import traceback
        traceback.print_exc()


def send_notification_demo():
    """Send a sample notification"""
    notification_id = str(uuid.uuid4())
    logger.info(f"SENDING NOTIFICATION with ID: {notification_id}")
    try:
        app.send_notification(
            notification_id=notification_id,
            text="This is a sample notification",
            duration=8000,
            
        )
        sent_elements["notification"] += 1
        logger.info(f"✓ Notification sent successfully (total: {sent_elements['notification']})")
    except Exception as e:
        logger.error(f"❌ Error sending notification: {str(e)}")
        import traceback
        traceback.print_exc()


def send_mcq_demo():
    """Send a sample MCQ question"""
    question_id = str(uuid.uuid4())
    logger.info(f"SENDING MCQ QUESTION with ID: {question_id}")
    try:
        app.send_mcq_question(
            question_id=question_id,
            question="What is your favorite color?",
            options=["Red", "Green", "Blue", "Yellow"],
        )
        sent_elements["mcq_question"] += 1
        logger.info(f"✓ MCQ Question sent successfully (total: {sent_elements['mcq_question']})")
    except Exception as e:
        logger.error(f"❌ Error sending MCQ question: {str(e)}")
        import traceback
        traceback.print_exc()


def send_places_demo():
    """Send a sample places autocomplete field"""
    places_id = str(uuid.uuid4())
    logger.info(f"SENDING PLACES AUTOCOMPLETE with ID: {places_id}")
    try:
        app.send_places_autocomplete(
            element_id=places_id,
            text="Please enter your location:",
            placeholder="Start typing your address or location"
        )
        sent_elements["places_autocomplete"] += 1
        logger.info(f"✓ Places Autocomplete sent successfully (total: {sent_elements['places_autocomplete']})")
    except Exception as e:
        logger.error(f"❌ Error sending places autocomplete: {str(e)}")
        import traceback
        traceback.print_exc()


def send_upload_demo():
    """Send a sample file upload element"""
    upload_id = str(uuid.uuid4())
    logger.info(f"SENDING FILE UPLOAD with ID: {upload_id}")
    try:
        app.send_upload_file(
            element_id=upload_id,
            text="Please upload a document:",
            allowed_types=["image/jpeg", "image/png", "application/pdf"],
            max_size_mb=10
        )
        sent_elements["upload_file"] += 1
        logger.info(f"✓ Upload File sent successfully (total: {sent_elements['upload_file']})")
    except Exception as e:
        logger.error(f"❌ Error sending file upload: {str(e)}")
        import traceback
        traceback.print_exc()


def send_text_input_demo():
    """Send a sample text input element"""
    text_input_id = str(uuid.uuid4())
    logger.info(f"SENDING TEXT INPUT with ID: {text_input_id}")
    try:
        app.send_text_input(
            element_id=text_input_id,
            prompt="Please provide additional information:",
            placeholder="Type your response here",
            multiline=True
        )
        sent_elements["textinput"] += 1
        logger.info(f"✓ Text Input sent successfully (total: {sent_elements['textinput']})")
    except Exception as e:
        logger.error(f"❌ Error sending text input: {str(e)}")
        import traceback
        traceback.print_exc()


def send_consent_demo():
    """Send a sample consent form"""
    consent_id = str(uuid.uuid4())
    logger.info(f"SENDING CONSENT FORM with ID: {consent_id}")
    try:
        app.send_consent_form(
            element_id=consent_id,
            text="I agree to the terms and conditions outlined in this demonstration.",
            checkbox_label="I understand and agree",
            submit_label="Submit Consent",
            required=True
        )
        sent_elements["consent_form"] += 1
        logger.info(f"✓ Consent Form sent successfully (total: {sent_elements['consent_form']})")
    except Exception as e:
        logger.error(f"❌ Error sending consent form: {str(e)}")
        import traceback
        traceback.print_exc()


def send_calendly_demo():
    """Send a sample Calendly scheduling element"""
    calendly_id = str(uuid.uuid4())
    logger.info(f"SENDING CALENDLY with ID: {calendly_id}")
    try:
        app.send_calendly(
            element_id=calendly_id,
            url="https://calendly.com/example/meeting",
            title="Schedule a Demo Meeting",
            subtitle="Choose a time that works for you"
        )
        sent_elements["calendly"] += 1
        logger.info(f"✓ Calendly element sent successfully (total: {sent_elements['calendly']})")
    except Exception as e:
        logger.error(f"❌ Error sending Calendly element: {str(e)}")
        import traceback
        traceback.print_exc()


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
    try:
        if isinstance(message, dict) and 'data' in message:
            mcq_data = message['data']
            selected_option = mcq_data.get('selectedOption')
            selected_index = mcq_data.get('selectedIndex')
            question_id = mcq_data.get('id')
            
            print(f"MCQ question UI handler: Selected '{selected_option}' (index: {selected_index}) for question {question_id}")
            process_mcq_selection(selected_option)
            
        elif hasattr(message, 'content') and hasattr(message.content, 'data'):
            # Handle as properly parsed Pydantic model
            mcq_data = message.content.data
            selected_option = mcq_data.selectedOption
            selected_index = mcq_data.selectedIndex
            question_id = mcq_data.id
            
            print(f"MCQ question UI handler: Selected '{selected_option}' (index: {selected_index}) for question {question_id}")
            process_mcq_selection(selected_option)
            
        else:
            logging.error(f"Unexpected message format: {type(message)}")
    except Exception as e:
        logging.error(f"Error handling MCQ question: {str(e)}")


def process_mcq_selection(selected_option):
    """Process MCQ selection and show the appropriate UI element"""
    app.send_generated_text(f"You selected: {selected_option}", is_generation_end=True)
    
    # Map selections to UI element demonstrations
    if selected_option == "Show All Elements":
        show_all_ui_elements_sequence()
    elif selected_option == "Notification":
        send_notification_demo()
    elif selected_option == "MCQ Question":
        send_mcq_demo()
    elif selected_option == "Places Autocomplete":
        send_places_demo()
    elif selected_option == "File Upload":
        send_upload_demo()
    elif selected_option == "Text Input":
        send_text_input_demo()
    elif selected_option == "Consent Form":
        send_consent_demo()
    elif selected_option == "Calendly":
        send_calendly_demo()


@app.on_custom_ui_response()
def on_custom_ui_response(message):
    """Handle all custom UI element responses"""
    logger.info(f"RECEIVED CUSTOM UI RESPONSE: {message}")
    
    try:
        # Extract element type using different possible message formats
        element_type = None
        element_data = {}
        
        if isinstance(message, dict):
            # Dictionary access for raw message
            if 'content' in message:
                element_type = message.get('content', {}).get('type')
                element_data = message.get('content', {}).get('data', {})
            elif 'data' in message:
                # Direct data field for some message formats
                element_type = message.get('type')
                element_data = message.get('data', {})
                
        elif hasattr(message, 'content'):
            # Pydantic model access
            if hasattr(message.content, 'type'):
                element_type = message.content.type
                if hasattr(message.content, 'data'):
                    element_data = message.content.data
        
        # Log what type was extracted
        logger.info(f"UI RESPONSE TYPE: {element_type}")
        
        # Count received response by type
        if element_type in received_responses:
            received_responses[element_type] += 1
            logger.info(f"✓ Response received for {element_type} (total: {received_responses[element_type]})")
        
        # Process by type with additional logging
        if element_type == "mcq_question":
            logger.info(f"HANDLING MCQ RESPONSE: {element_data}")
            handle_mcq_response(element_data)
        elif element_type == "places_autocomplete":
            logger.info(f"HANDLING PLACES RESPONSE: {element_data}")
            handle_places_response(element_data)
        elif element_type == "upload_file":
            logger.info(f"HANDLING UPLOAD RESPONSE: {element_data}")
            handle_upload_response(element_data)
        elif element_type == "textinput":
            logger.info(f"HANDLING TEXT INPUT RESPONSE: {element_data}")
            handle_text_input_response(element_data)
        elif element_type == "consent_form":
            logger.info(f"HANDLING CONSENT RESPONSE: {element_data}")
            handle_consent_response(element_data)
        elif element_type == "calendly":
            logger.info(f"HANDLING CALENDLY RESPONSE: {element_data}")
            handle_calendly_response(element_data)
        elif element_type == "notification_element":
            logger.info(f"NOTIFICATION ACKNOWLEDGED: {element_data}")
        else:
            logger.warning(f"⚠️ UNHANDLED UI RESPONSE TYPE: {element_type}")
            # Log the full message for debugging
            logger.info(f"FULL RESPONSE MESSAGE: {message}")
                
    except Exception as e:
        logger.error(f"❌ ERROR HANDLING CUSTOM UI RESPONSE: {str(e)}")
        import traceback
        traceback.print_exc()


def handle_mcq_response(data):
    """Handle MCQ question response"""
    if isinstance(data, dict):
        selected_option = data.get('selectedOption')
        selected_index = data.get('selectedIndex')
        question_id = data.get('id')
    else:
        selected_option = data.selectedOption
        selected_index = data.selectedIndex
        question_id = data.id
    
    print(f"MCQ selection: '{selected_option}' (index: {selected_index}) for question {question_id}")
    
    # Respond to the selection
    app.send_generated_text(f"You selected: {selected_option}", is_generation_end=True)
    
    # Process the selection
    if selected_option == "Show All Elements":
        app.send_generated_text("Showing all UI elements one by one...", is_generation_end=True)
        schedule_ui_element_demonstration()
    elif selected_option in ["Notification", "MCQ Question", "Places Autocomplete", "File Upload", 
                            "Text Input", "Consent Form", "Calendly"]:
        process_mcq_selection(selected_option)
        
        # After a short delay, offer to show more UI elements
        time.sleep(3)  # Wait a bit for the user to interact with the element
        app.send_generated_text("Would you like to see another UI element?", is_generation_end=False)
        send_ui_element_menu()
    else:
        # For other options like Continue, Exit, etc.
        process_mcq_selection(selected_option)


def handle_places_response(data):
    """Handle places autocomplete response"""
    if isinstance(data, dict):
        place_id = data.get('id')
        # For dictionary input, try both formats
        if 'place' in data:
            place_name = data.get('place', {}).get('name', '')
            place_address = data.get('place', {}).get('formatted_address', '')
        else:
            place_name = data.get('address', '')  # Use address directly
            place_address = data.get('address', '')  # Address is the same
    else:
        place_id = data.id
        # For Pydantic model input, check which attributes exist
        if hasattr(data, 'place'):
            place_name = getattr(getattr(data, 'place', None), 'name', '')
            place_address = getattr(getattr(data, 'place', None), 'formatted_address', '')
        else:
            place_name = getattr(data, 'address', '')  # Use address directly
            place_address = getattr(data, 'address', '')  # Address is the same
    
    print(f"Places selection: {place_name}, {place_address} for element {place_id}")
    app.send_generated_text(f"You selected location: {place_name}, {place_address}", is_generation_end=True)


def handle_upload_response(data):
    """Handle file upload response"""
    if isinstance(data, dict):
        element_id = data.get('id')
        file_name = data.get('fileName', '')
        file_url = data.get('fileUrl', '')
        file_type = data.get('fileType', '')
    else:
        element_id = data.id
        file_name = getattr(data, 'fileName', '')
        file_url = getattr(data, 'fileUrl', '')
        file_type = getattr(data, 'fileType', '')
    
    print(f"File uploaded: {file_name} ({file_type}) - URL: {file_url} for element {element_id}")
    app.send_generated_text(f"You uploaded file: {file_name}", is_generation_end=True)


def handle_text_input_response(data):
    """Handle text input response"""
    if isinstance(data, dict):
        element_id = data.get('id')
        text_value = data.get('value', '')
    else:
        element_id = data.id
        text_value = getattr(data, 'value', '')
    
    print(f"Text input: {text_value} for element {element_id}")
    app.send_generated_text(f"You entered: {text_value}", is_generation_end=True)


def handle_consent_response(data):
    """Handle consent form response"""
    if isinstance(data, dict):
        element_id = data.get('id')
        agreed = data.get('agreed', False)
    else:
        element_id = data.id
        agreed = getattr(data, 'agreed', False)
    
    consent_status = "provided consent" if agreed else "declined consent"
    print(f"Consent form: User {consent_status} for element {element_id}")
    app.send_generated_text(f"You {consent_status}", is_generation_end=True)


def handle_calendly_response(data):
    """Handle Calendly response"""
    if isinstance(data, dict):
        element_id = data.get('id')
        event_url = data.get('eventUrl', '')
        event_date = data.get('eventDate', '')
    else:
        element_id = data.id
        event_url = getattr(data, 'eventUrl', '')
        event_date = getattr(data, 'eventDate', '')
    
    print(f"Calendly booking: {event_date}, URL: {event_url} for element {element_id}")
    app.send_generated_text(f"You scheduled a meeting for: {event_date}", is_generation_end=True)


@app.on("join")
def on_user_join(message):
    """Handle join event and demonstrate UI elements one by one"""
    logger.info(f"RECEIVED JOIN EVENT: {message}")
    connection_state["connected"] = True
    connection_state["authenticated"] = True
    
    try:
        # Handle various message formats
        meeting_id = None
        
        # Dictionary format
        if isinstance(message, dict):
            if 'content' in message and 'user_joined' in message['content']:
                meeting_id = message['content']['user_joined'].get('meeting_id')
            elif 'meeting_id' in message:
                meeting_id = message['meeting_id']
        
        # Model format
        elif hasattr(message, 'content'):
            if hasattr(message.content, 'user_joined'):
                meeting_id = message.content.user_joined.meeting_id
            elif hasattr(message.content, 'meeting_id'):
                meeting_id = message.content.meeting_id
        
        # Fall back to stored meeting ID if extraction fails
        if not meeting_id:
            meeting_id = connection_state.get("current_meeting_id", "unknown")
            
        logger.info(f"USER JOINED MEETING: {meeting_id}")
        app.send_generated_text(f"Welcome to meeting {meeting_id}!", is_generation_end=True)
        
        # Reset counters on join
        for element_type in sent_elements:
            sent_elements[element_type] = 0
            received_responses[element_type] = 0
            
        # Schedule the demonstration of UI elements with a delay between each
        logger.info("Scheduling demonstration of all UI elements")
        schedule_ui_element_demonstration()
        
    except Exception as e:
        logger.error(f"❌ Error handling join event: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Still try to show a welcome message
        app.send_generated_text("Welcome! I'll demonstrate some UI elements for you.", is_generation_end=True)


def schedule_ui_element_demonstration():
    """Schedule the demonstration of UI elements one by one with delays"""
    # Start a background thread to send UI elements with delays
    import threading
    
    def send_elements_sequence():
        # First, send an introduction
        app.send_generated_text("I'll demonstrate the various UI elements available.", is_generation_end=True)
        time.sleep(2)
        
        # 1. First, send a notification
        app.send_generated_text("1. Notification - Displays a temporary message", is_generation_end=True)
        time.sleep(1)
        send_notification_demo()
        time.sleep(3)  # Give time for notification to be seen
        
        # 2. Send MCQ question
        app.send_generated_text("2. Multiple Choice Question - Allows selecting from options", is_generation_end=True)
        time.sleep(1)
        send_mcq_demo()
        time.sleep(3)
        
        # 3. Send places autocomplete
        if check_element_availability("places_autocomplete"):
            app.send_generated_text("3. Places Autocomplete - Location search with Google Maps", is_generation_end=True)
            time.sleep(1)
            send_places_demo()
            time.sleep(3)
        
        # 4. Send file upload
        if check_element_availability("upload_file"):
            app.send_generated_text("4. File Upload - Allows uploading documents", is_generation_end=True) 
            time.sleep(1)
            send_upload_demo()
            time.sleep(3)
        
        # 5. Send text input
        if check_element_availability("textinput"):
            app.send_generated_text("5. Text Input - Allows entering free text", is_generation_end=True)
            time.sleep(1)
            send_text_input_demo()
            time.sleep(3)
        
        # 6. Send consent form
        if check_element_availability("consent_form"):
            app.send_generated_text("6. Consent Form - Requests user agreement", is_generation_end=True)
            time.sleep(1)
            send_consent_demo()
            time.sleep(3)
        
        # 7. Send Calendly
        if check_element_availability("calendly"):
            app.send_generated_text("7. Calendly - Schedule appointments", is_generation_end=True)
            time.sleep(1)
            send_calendly_demo()
            time.sleep(3)
        
        # Conclude the demonstration
        app.send_generated_text("That completes the demonstration of all UI elements!", is_generation_end=True)
        time.sleep(1)
        
        # Show the menu again
        app.send_generated_text("You can say 'show [element name]' to see a specific element again, or choose from this menu:", is_generation_end=False)
        send_ui_element_menu()
    
    # Start the sequence in a background thread
    demonstration_thread = threading.Thread(target=send_elements_sequence)
    demonstration_thread.daemon = True  # Thread will exit when main program exits
    demonstration_thread.start()
    logger.info("UI elements demonstration scheduled in background thread")


@app.on("join")
def on_user_join(message):
    """Handle join event with proper error handling for different message formats"""
    logger.info(f"RECEIVED JOIN EVENT: {message}")
    connection_state["connected"] = True
    connection_state["authenticated"] = True
    
    try:
        # Handle various message formats
        meeting_id = None
        
        # Dictionary format
        if isinstance(message, dict):
            if 'content' in message and 'user_joined' in message['content']:
                meeting_id = message['content']['user_joined'].get('meeting_id')
            elif 'meeting_id' in message:
                meeting_id = message['meeting_id']
        
        # Model format
        elif hasattr(message, 'content'):
            if hasattr(message.content, 'user_joined'):
                meeting_id = message.content.user_joined.meeting_id
            elif hasattr(message.content, 'meeting_id'):
                meeting_id = message.content.meeting_id
        
        # Fall back to stored meeting ID if extraction fails
        if not meeting_id:
            meeting_id = connection_state.get("current_meeting_id", "unknown")
            
        logger.info(f"USER JOINED MEETING: {meeting_id}")
        app.send_generated_text(f"Welcome to meeting {meeting_id}!", is_generation_end=False)
        app.send_generated_text("I can demonstrate various UI elements. Please say 'show ui elements' to see all, or choose one from the menu:", is_generation_end=True)
        
        # Reset counters on join
        for element_type in sent_elements:
            sent_elements[element_type] = 0
            received_responses[element_type] = 0
        
        # Show UI element menu on join
        send_ui_element_menu()
        
    except Exception as e:
        logger.error(f"❌ Error handling join event: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Still try to show menu even if there was an error
        app.send_generated_text("Welcome! I can demonstrate various UI elements.", is_generation_end=True)
        send_ui_element_menu()


@app.on_exit()
def on_user_exit(message):
    """Handle exit event with proper error handling"""
    try:
        meeting_id = None
        participant_id = None
        
        # Dictionary format
        if isinstance(message, dict):
            if 'content' in message and 'user_exited' in message['content']:
                content = message['content']['user_exited']
                meeting_id = content.get('meeting_id')
                participant_id = content.get('participant_id')
        
        # Model format
        elif hasattr(message, 'content') and hasattr(message.content, 'user_exited'):
            meeting_id = message.content.user_exited.meeting_id if hasattr(message.content.user_exited, 'meeting_id') else None
            participant_id = message.content.user_exited.participant_id if hasattr(message.content.user_exited, 'participant_id') else None
        
        if not meeting_id:
            meeting_id = connection_state.get("current_meeting_id", "unknown")
            
        logger.info(f"USER EXITED MEETING: {meeting_id} (Participant: {participant_id})")
        app.send_generated_text("User has left the meeting.", is_generation_end=True)
        
        # Update connection state
        connection_state["connected"] = False
        
    except Exception as e:
        logger.error(f"❌ Error handling exit event: {str(e)}")


@app.on_connection_rejected()
def on_reject(message):
    """Handle connection rejection without trying to create new meetings"""
    try:
        reason = "unknown"
        meeting_id = None
        
        # Extract reason based on message format
        if isinstance(message, dict):
            if 'content' in message:
                reason = message['content'].get('reason', reason)
                meeting_id = message['content'].get('meeting_id')
        elif hasattr(message, 'content'):
            reason = message.content.reason if hasattr(message.content, 'reason') else reason
            meeting_id = message.content.meeting_id if hasattr(message.content, 'meeting_id') else None
            
        logger.warning(f"CONNECTION REJECTED: {reason} for meeting {meeting_id}")
        
        # Update connection state
        connection_state["connected"] = False
        connection_state["authenticated"] = False
        connection_state["rejected_reason"] = reason
        
        # Simply retry the same meeting ID after a delay
        if "limit" in reason.lower():
            logger.info(f"Connection rejected due to listener limit. Will retry joining {MEETING_ID} again after a delay.")
            time.sleep(5)  # Wait 5 seconds before retrying
            app.join_meeting(meeting_id=MEETING_ID)
            
    except Exception as e:
        logger.error(f"Error handling connection rejection: {str(e)}")


def log_ui_element_stats():
    """Log statistics about sent and received UI elements"""
    logger.info("=== UI ELEMENT STATISTICS ===")
    for element_type in sent_elements:
        sent = sent_elements[element_type]
        received = received_responses[element_type]
        logger.info(f"{element_type}: {sent} sent, {received} responses received")


# Add a function to dump message structure for debugging
def dump_message_structure(message, prefix=""):
    """Recursively dump message structure for debugging"""
    if isinstance(message, dict):
        for key, value in message.items():
            if isinstance(value, (dict, list)):
                logger.debug(f"{prefix}{key}: {type(value).__name__}")
                dump_message_structure(value, prefix + "  ")
            else:
                logger.debug(f"{prefix}{key}: {value} ({type(value).__name__})")
    elif isinstance(message, list):
        for i, item in enumerate(message):
            if isinstance(item, (dict, list)):
                logger.debug(f"{prefix}[{i}]: {type(item).__name__}")
                dump_message_structure(item, prefix + "  ")
            else:
                logger.debug(f"{prefix}[{i}]: {item} ({type(item).__name__})")
    else:
        logger.debug(f"{prefix}Object type: {type(message).__name__}")
        for attr_name in dir(message):
            if not attr_name.startswith("_") and not callable(getattr(message, attr_name)):
                attr_value = getattr(message, attr_name)
                logger.debug(f"{prefix}{attr_name}: {attr_value} ({type(attr_value).__name__})")


if __name__ == "__main__":
    logger.info("=== STARTING UI ELEMENT DEMO ===")
    logger.info(f"Joined meeting {MEETING_ID}, waiting for connection...")
    logger.info("Say 'show ui elements' to see all UI elements, or select from the menu")
    
    # Run the app with debug logging enabled
    try:
        app.run(log_level="DEBUG")
    except KeyboardInterrupt:
        logger.info("Demo terminated by user")
    except Exception as e:
        logger.error(f"Error in demo: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Log final statistics at exit
        log_ui_element_stats()
        logger.info("=== UI ELEMENT DEMO ENDED ===")
