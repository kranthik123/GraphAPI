import requests
import json
from datetime import datetime, timedelta
import pytz

# Step 1: Get Access Token to access Graph API
def get_graph_api_token():
    token_url = "https://login.microsoftonline.com/<tenant_id>/oauth2/v2.0/token"
    token_payload = {
        'grant_type': 'client_credentials',
        'scope': 'https://graph.microsoft.com/.default',
        'client_id': '<client_id>',
        'client_secret': '<client_secret>'
    }
    token_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, headers=token_headers, data=token_payload)
    response_data = response.json()
    return response_data.get('access_token')

# Step 2: Retrieve all meeting rooms
def get_meeting_rooms(access_token):
    rooms_url = "https://graph.microsoft.com/v1.0/places/microsoft.graph.room"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    rooms_response = requests.get(rooms_url, headers=headers)
    rooms_data = rooms_response.json()
    return rooms_data.get('value', [])

# Step 3: Get attendance data from Verge Sense
def get_verge_sense_attendance(event_id, vs_api_key):
    vs_attendance_url = f"https://api.vergesense.com/v1/meetings/{event_id}/attendance"
    vs_headers = {
        'Accept': 'application/json',
        'vs-api-key': vs_api_key
    }
    attendance_response = requests.get(vs_attendance_url, headers=vs_headers)
    attendance_data = attendance_response.json()
    return attendance_data.get('attendees', 0)

# Main script
def main():
    # Get Microsoft Graph API token
    access_token = get_graph_api_token()
    if not access_token:
        raise SystemExit("Failed to get Microsoft Graph API access token")

    # Verge Sense API key
    vs_api_key = '<vs_api_key>'
    if not vs_api_key:
        raise SystemExit("Verge Sense API key is required")

    # Retrieve all meeting rooms
    rooms = get_meeting_rooms(access_token)

    # Define CST timezone
    cst = pytz.timezone('US/Central')

    # Get current time and time 24 hours ago in CST
    current_time_cst = datetime.now(cst)
    start_time_cst = current_time_cst - timedelta(days=1)

    # Format times in ISO 8601 format without timezone information
    current_time_str = current_time_cst.strftime("%Y-%m-%dT%H:%M:%S")
    start_time_str = start_time_cst.strftime("%Y-%m-%dT%H:%M:%S")

    # Iterate through each room to get events and attendance data
    for room in rooms:
        room_id = room.get('id')
        room_name = room.get('displayName')

        # URL to list calendar events for the room for the specified day
        events_url = (
            f"https://graph.microsoft.com/v1.0/places/{room_id}/calendar/events?"
            f"$filter=start/dateTime ge '{start_time_str}' and start/dateTime le '{current_time_str}'"
        )

        # Request list of calendar events (booked slots) for the room
        events_response = requests.get(events_url, headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })
        events_data = events_response.json()
        events = events_data.get('value', [])

        # Print room details and booked slots
        for event in events:
            event_id = event.get('id')
            event_subject = event.get('subject')
            event_start = event.get('start').get('dateTime')
            event_end = event.get('end').get('dateTime')

            # Get attendance data from Verge Sense
            attendees = get_verge_sense_attendance(event_id, vs_api_key)

            # Print meeting details and number of attendees
            print(f"{room_name}, {event_subject}, {event_start}, {event_end}, Attendees: {attendees}")

if __name__ == "__main__":
    main()

