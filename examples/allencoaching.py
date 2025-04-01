import logging
import uuid
import requests
import json
from datetime import datetime, timedelta
from framewise_meet_client.app import App
from framewise_meet_client.models.inbound import (
    TranscriptMessage,
    MCQSelectionMessage,
    JoinMessage,
    ExitMessage,
)
from framewise_meet_client.models.outbound import (
    PlacesAutocompleteData,
    PlacesAutocompleteElement,
    TextInputData,
    TextInputElement,
    UploadFileData,
    UploadFileElement,
    NotificationData,
    NotificationElement,
    ConsentFormData,
    ConsentFormElement,
    CalendlyData,
    CalendlyElement,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = App(api_key="1234567")

app.create_meeting("46234")
app.join_meeting(meeting_id="46234")

# Store student data during the onboarding process
student_data = {
    "name": "",
    "address": "",
    "nearest_center": "",
    "photo_filename": "",
    "consent_given": False,
    "meeting_scheduled": False
}

# Allen Center locations with detailed information
allen_centers = [
    {
        "name": "Allen Career Institute - Kota Main Center",
        "location": {"lat": 25.1461, "lng": 75.8506},
        "address": "CG Tower, A-46,47, Road Number 2, IPIA, Ranpur, Kota, Rajasthan 324005",
        "phone": "+91-744-2757575",
        "courses": ["JEE (Main & Advanced)", "NEET-UG", "KVPY", "Olympiads"],
        "faculty_strength": 250,
        "success_rate": "85% selection rate in JEE Advanced",
        "facilities": ["Digital Classrooms", "Library", "Hostel Facility", "Sports Complex"],
        "working_hours": "7:00 AM - 7:00 PM (Mon-Sat)"
    },
    {
        "name": "Allen Career Institute - Delhi",
        "location": {"lat": 28.6139, "lng": 77.2090},
        "address": "Plot No. 5, Sector-9, Dwarka, New Delhi, Delhi 110075",
        "phone": "+91-11-47062626",
        "courses": ["JEE (Main & Advanced)", "NEET-UG", "NTSE", "Olympiads"],
        "faculty_strength": 120,
        "success_rate": "78% selection rate in JEE Main",
        "facilities": ["Digital Classrooms", "Library", "Counseling Center"],
        "working_hours": "8:00 AM - 8:00 PM (Mon-Sat)"
    },
    {
        "name": "Allen Career Institute - Chandigarh",
        "location": {"lat": 30.7333, "lng": 76.7794},
        "address": "SCO 222-223, Sector 34-A, Chandigarh 160022",
        "phone": "+91-172-5211234",
        "courses": ["JEE (Main & Advanced)", "NEET-UG", "Foundation Courses"],
        "faculty_strength": 65,
        "success_rate": "77% selection rate in JEE Main",
        "facilities": ["Digital Classrooms", "Library", "Hostel Facility"],
        "working_hours": "8:00 AM - 7:30 PM (Mon-Sat)"
    }
]

# Google Maps API key
GMAPS_API_KEY = "AIzaSyAKx5CGoWkpxRFA9AMiuTcNq4Huwc5r_JI"

# Simple in-memory cache
distance_cache = {}
# Cache expiration time (24 hours)
CACHE_EXPIRY = 24 * 60 * 60  # seconds


def calculate_distances_with_api(origin_lat, origin_lng):
    """Calculate distances from student location to all centers using Google Distance Matrix API."""
    # Format origins and destinations
    origin = f"{origin_lat},{origin_lng}"
    destinations = "|".join(
        [f"{center['location']['lat']},{center['location']['lng']}" for center in allen_centers])

    # Check if we have a valid cache entry
    cache_key = f"distances_from_{origin}"
    if cache_key in distance_cache:
        cache_entry = distance_cache[cache_key]
        # Check if cache is still valid
        if datetime.now().timestamp() - cache_entry['timestamp'] < CACHE_EXPIRY:
            print(f"Using cached distance data for {origin}")
            return cache_entry['data']

    # API endpoint
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # Parameters
    params = {
        "origins": origin,
        "destinations": destinations,
        "mode": "driving",  # Can be changed to "transit", "walking", etc.
        "key": GMAPS_API_KEY
    }

    try:
        # Make the API request
        response = requests.get(url, params=params)
        data = response.json()

        if data['status'] == 'OK':
            # Store in cache
            distance_cache[cache_key] = {
                'timestamp': datetime.now().timestamp(),
                'data': data
            }
            return data
        else:
            print(f"Error from Distance Matrix API: {data['status']}")
            return None

    except Exception as e:
        print(f"Error calculating distances with API: {e}")
        return None


def find_nearest_center(student_location):
    """Find the nearest Allen center based on student's location using Google Distance Matrix API."""
    if not student_location or 'lat' not in student_location or 'lng' not in student_location:
        # Default to first center if location not available
        return allen_centers[0], None

    # Get distances using Google Distance Matrix API
    distance_data = calculate_distances_with_api(
        student_location['lat'],
        student_location['lng']
    )

    # Fall back to simple calculation if API fails
    if not distance_data or 'rows' not in distance_data or len(distance_data['rows']) == 0:
        print("Falling back to simple distance calculation")
        # Calculate simple Euclidean distances
        nearest_center = None
        min_distance = float('inf')

        for center in allen_centers:
            distance = ((center['location']['lat'] - student_location['lat'])**2 +
                        (center['location']['lng'] - student_location['lng'])**2)**0.5

            if distance < min_distance:
                min_distance = distance
                nearest_center = center

        return nearest_center, None

    # Process API response
    elements = distance_data['rows'][0]['elements']

    # Find center with shortest travel time
    nearest_index = 0
    min_duration = float('inf')
    travel_info = None

    for i, element in enumerate(elements):
        if element['status'] == 'OK':
            duration_seconds = element['duration']['value']
            if duration_seconds < min_duration:
                min_duration = duration_seconds
                nearest_index = i
                travel_info = {
                    'distance': element['distance']['text'],
                    'duration': element['duration']['text']
                }

    return allen_centers[nearest_index], travel_info


@app.on_transcript()
def on_transcript(message: TranscriptMessage):
    transcript = message.content.text
    is_final = message.content.is_final
    print(f"Received transcript: {transcript}")


@app.invoke
def process_final_transcript(message: TranscriptMessage):
    transcript = message.content.text
    print(f"Processing final transcript with invoke: {transcript}")

    app.send_generated_text(
        "Welcome to Allen Career Institute's Admission Portal! Let's get you registered for our coaching programs.",
        is_generation_end=True
    )

    # Start with student name input
    send_name_input()


def send_name_input():
    """Send a text input UI element to collect student name."""
    element_id = str(uuid.uuid4())

    # Create text input data
    text_input_data = TextInputData(
        id=element_id,
        prompt="What is your full name?",
        placeholder="Enter your full name",
        multiline=False
    )

    # Create text input element
    text_input_element = TextInputElement(
        type="textinput",
        data=text_input_data
    )

    # Send the text input UI element
    app.send_custom_ui_element(text_input_element)

    print(f"Sent student name input UI element with ID: {element_id}")


def send_places_autocomplete():
    """Send a places autocomplete UI element to collect student address."""
    element_id = str(uuid.uuid4())

    # Create places autocomplete data
    places_data = PlacesAutocompleteData(
        id=element_id,
        text="What is your home address?",
        placeholder="Enter your complete home address"
    )

    # Create places autocomplete element
    places_element = PlacesAutocompleteElement(
        type="places_autocomplete",
        data=places_data
    )

    # Send the custom UI element
    app.send_custom_ui_element(places_element)

    print(f"Sent places autocomplete UI element with ID: {element_id}")


def send_photo_upload():
    """Send a file upload UI element to collect student photo."""
    element_id = str(uuid.uuid4())

    # Create file upload data
    upload_data = UploadFileData(
        id=element_id,
        text="Please upload a recent passport-sized photo:",
        allowed_types=["image/*"],
        maxSizeMB=5
    )

    # Create file upload element
    upload_element = UploadFileElement(
        type="upload_file",
        data=upload_data
    )

    # Send the file upload UI element
    app.send_custom_ui_element(upload_element)

    print(f"Sent photo upload UI element with ID: {element_id}")


def send_consent_form():
    """Send a consent form UI element for photo usage."""
    element_id = str(uuid.uuid4())

    # Create consent form data
    consent_data = ConsentFormData(
        id=element_id,
        text="I hereby consent to Allen Career Institute using my photo for identification purposes during the admission process and on my student ID card.",
        required=True,
        checkboxLabel="I agree to the terms",
        submitLabel="Submit Consent"
    )

    # Create consent form element
    consent_element = ConsentFormElement(
        type="consent_form",
        data=consent_data
    )

    # Send the consent form UI element
    app.send_custom_ui_element(consent_element)

    print(f"Sent consent form UI element with ID: {element_id}")


def send_calendly():
    """Send a Calendly scheduling UI element for admission meeting."""
    element_id = str(uuid.uuid4())

    # Create Calendly data
    calendly_data = CalendlyData(
        id=element_id,
        url="https://calendly.com/allen-institute/admission-meeting",
        title="Schedule Your Admission Meeting",
        subtitle="Select a convenient time to meet with our admission counselor"
    )

    # Create Calendly element
    calendly_element = CalendlyElement(
        type="calendly",
        data=calendly_data
    )

    # Send the Calendly UI element
    app.send_custom_ui_element(calendly_element)

    print(f"Sent Calendly UI element with ID: {element_id}")


def send_notification(message, level="error"):
    """Send a notification UI element."""
    notification_id = str(uuid.uuid4())

    # Create notification data
    app.send_notification(
        notification_id=notification_id,
        text=message,
        duration=8000,
        level=level,

    )

    print(f"Sent notification UI element with ID", notification_id)


def format_center_details(center, travel_info=None):
    """Format center details in a readable format."""
    details = [ 
        f"🏫 **{center['name']}**",
        f"📍 {center['address']}",
        f"☎️ {center['phone']}"
    ]

    if travel_info:
        details.append(
            f"🚗 **{travel_info['distance']}** away ({travel_info['duration']} travel time)")

    details.extend([
        f"⏰ Working Hours: {center['working_hours']}",
        f"👨‍🏫 Faculty: {center['faculty_strength']} experienced teachers",
        f"📊 Success Rate: {center['success_rate']}",
        f"🎓 Available Courses:",
    ])

    # Add courses as a bullet list
    for course in center['courses']:
        details.append(f"  • {course}")

    details.append("🏢 Facilities:")
    for facility in center['facilities']:
        details.append(f"  • {facility}")

    return "\n".join(details)


@app.on_custom_ui_response()
def on_custom_ui_response(message_data):
    """General handler for custom UI responses."""
    try:
        # Log the entire message for debugging
        print(f"Received custom UI response: {message_data}")

        # Extract element type and data based on message format
        element_type = None
        data = None

        # Handle different message formats (dictionary or Pydantic model)
        if isinstance(message_data, dict):
            # Dictionary format
            if 'content' in message_data:
                content = message_data.get('content', {})
                element_type = content.get('type')
                data = content.get('data', {})
            elif 'type' in message_data:
                element_type = message_data.get('type')
                data = message_data.get('data', {})
        else:
            # Pydantic model format
            if hasattr(message_data, 'content'):
                content = message_data.content
                if hasattr(content, 'type'):
                    element_type = content.type
                    if hasattr(content, 'data'):
                        data = content.data

        print(
            f"Processing custom UI response for element type: {element_type}")

        # Handle text input response (student name)
        if element_type == "textinput":
            # Extract data based on format
            if isinstance(data, dict):
                element_id = data.get("id")
                student_name = data.get("text", "")
            else:
                element_id = data.id if hasattr(data, "id") else None
                student_name = data.text if hasattr(data, "text") else ""

            student_data["name"] = student_name

            print(
                f"Text input handler: Received student name '{student_name}'")

            app.send_generated_text(
                f"Thank you, {student_name}! Now, let's find the Allen Career Institute center nearest to your location.",
                is_generation_end=True
            )

            # Move to the next step: address collection
            send_places_autocomplete()

        # Handle places autocomplete response (student address)
        elif element_type == "places_autocomplete":
            # Extract data based on format
            if isinstance(data, dict):
                element_id = data.get("id")
                address = data.get("address", "No address provided")
                place_id = data.get("placeId", "Unknown place ID")
                coordinates = data.get("coordinates", {"lat": 0, "lng": 0})
            else:
                element_id = data.id if hasattr(data, "id") else None
                address = data.address if hasattr(
                    data, "address") else "No address provided"
                place_id = data.placeId if hasattr(
                    data, "placeId") else "Unknown place ID"
                coordinates = data.coordinates if hasattr(
                    data, "coordinates") else {"lat": 0, "lng": 0}

            # Store student address information
            student_data["address"] = address

            print(
                f"Places autocomplete handler: Student address '{address}' at {coordinates}")

            # Find nearest Allen center to the student's location
            nearest_center, travel_info = find_nearest_center(coordinates)
            student_data["nearest_center"] = nearest_center

            print(f"Nearest center: {nearest_center['name']}")
            if travel_info:
                print(
                    f"Travel info: {travel_info['distance']} away, {travel_info['duration']} travel time")

            # Format center details
            center_details = format_center_details(nearest_center, travel_info)

            app.send_generated_text(
                f"Based on your location at {address}, we've found the most convenient Allen Career Institute center for you:\n\n" +
                f"{center_details}\n\n" +
                f"This center will handle your admission process and will be your primary study location.",
                is_generation_end=True
            )

            # Move to the next step: photo upload
            send_photo_upload()

        # Handle file upload response (student photo)
        elif element_type == "upload_file":
            # Extract data based on format
            if isinstance(data, dict):
                element_id = data.get("id")
                file_name = data.get("fileName", "unknown file")
                file_type = data.get("fileType", "unknown type")
                file_size = data.get("fileSize", 0)
                file_data = data.get("fileData", "")
            else:
                element_id = data.id if hasattr(data, "id") else None
                file_name = data.fileName if hasattr(
                    data, "fileName") else "unknown file"
                file_type = data.fileType if hasattr(
                    data, "fileType") else "unknown type"
                file_size = data.fileSize if hasattr(data, "fileSize") else 0
                file_data = data.fileData if hasattr(data, "fileData") else ""

            # Store student photo information
            student_data["photo_filename"] = file_name

            print(
                f"File upload handler: Received student photo '{file_name}' ({file_type}, {file_size} bytes)")

            app.send_generated_text(
                f"Thank you for uploading your photo. We'll use this for your student ID card and admission documents.",
                is_generation_end=True
            )

            # Send a notification for the file upload
            send_notification("Photo uploaded successfully!")

            # Move to the next step: consent form
            send_consent_form()

        # Handle consent form response (photo usage consent)
        elif element_type == "consent_form":
            # Extract data based on format
            if isinstance(data, dict):
                element_id = data.get("id")
                consent_given = data.get("isChecked", False)
            else:
                element_id = data.id if hasattr(data, "id") else None
                consent_given = data.isChecked if hasattr(
                    data, "isChecked") else False

            # Store consent information
            student_data["consent_given"] = consent_given

            print(f"Consent form handler: Consent given: {consent_given}")

            if consent_given:
                app.send_generated_text(
                    "Thank you for providing your consent. This allows us to use your photo for your ID card and admission records.",
                    is_generation_end=True
                )
            else:
                app.send_generated_text(
                    "We've noted that you haven't provided consent for photo usage. Please note that a photo is required for your student ID card. You can discuss this with the admission counselor during your meeting.",
                    is_generation_end=True
                )

            # Move to the final step: scheduling an admission meeting
            send_calendly()

        # Handle Calendly response (admission meeting scheduling)
        elif element_type == "calendly":
            # Extract data based on format
            if isinstance(data, dict):
                element_id = data.get("id")
                scheduled_meeting = data.get("scheduledMeeting", False)
            else:
                element_id = data.id if hasattr(data, "id") else None
                scheduled_meeting = data.scheduledMeeting if hasattr(
                    data, "scheduledMeeting") else False

            # Store meeting scheduling information
            student_data["meeting_scheduled"] = scheduled_meeting

            print(f"Calendly handler: Meeting scheduled: {scheduled_meeting}")

            center_name = student_data.get(
                'nearest_center', {}).get('name', 'Not determined')
            center_address = student_data.get('nearest_center', {}).get(
                'address', 'Address not available')
            center_phone = student_data.get('nearest_center', {}).get(
                'phone', 'Phone not available')

            if scheduled_meeting:
                app.send_generated_text(
                    f"Thank you for scheduling your admission meeting with Allen Career Institute!\n\n" +
                    f"Here's a summary of your registration information:\n" +
                    f"🎓 Name: {student_data['name']}\n" +
                    f"Please bring your original academic documents to the meeting, including:\n" +
                    f"• Aadhar card or other government ID\n\n" +
                    f"We look forward to welcoming you to the Allen family!",
                    is_generation_end=True
                )
            else:
                app.send_generated_text(
                    f"We've received your registration information. To complete the admission process, please schedule a meeting with our counselor when you're ready.\n\n" +
                    f"Here's your registration summary so far:\n" +
                    f"🎓 Name: {student_data['name']}\n" +
                    f"🏠 Address: {student_data['address']}\n" +
                    f"☎️ Center Contact: {center_phone}",
                    is_generation_end=True
                )

            # End of sequence
            send_notification(
                "Registration process completed. Thank you!", "info")

    except Exception as e:
        print(f"Error in custom UI response handler: {e}")
        import traceback
        traceback.print_exc()
        app.send_generated_text(
            f"An error occurred while processing your information: {str(e)}. Please try again or contact our support team at support@allen.ac.in.",
            is_generation_end=True
        )


@app.on_exit()
def on_user_exit(message):
    try:
        if isinstance(message, dict):
            meeting_id = message.get("content", {}).get("user_exited")
            print(f"User exited meeting: {meeting_id}")
        else:
            meeting_id = message.content.user_exited
            print(f"User exited meeting: {meeting_id}")

    except Exception as e:
        print(f"Error in exit handler: {e}")


@app.on_connection_rejected()
def on_reject(message):
    print("Connection rejected")


if __name__ == "__main__":
    app.run(log_level="DEBUG")
