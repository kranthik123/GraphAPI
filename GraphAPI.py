import requests
import urllib3
from datetime import datetime, timedelta
import pytz
import pandas as pd

# Disable insecure warning messages
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Replace with your actual credentials
tenant_id = "your_tenant_id"
client_id = "your_client_id"
client_secret = "your_client_secret"
vs_api_key = "your_verge_sense_api_key"

# Get access token
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_payload = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "https://graph.microsoft.com/.default"
}
token_response = requests.post(token_url, data=token_payload, verify=False)
token_response.raise_for_status()
access_token = token_response.json().get('access_token')

# Get rooms
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
rooms_url = "https://graph.microsoft.com/v1.0/places/microsoft.graph.room"
rooms_response = requests.get(rooms_url, headers=headers, verify=False)
rooms_response.raise_for_status()
rooms = rooms_response.json()['value']

# Set date range
cst = pytz.timezone('America/Chicago')
end_date = datetime.now(cst).replace(hour=0, minute=0, second=0, microsecond=0)
start_date = end_date - timedelta(days=1)

meeting_data = []

# Process each room
for room in rooms:
    room_id = room['id']
    room_name = room['displayName']
    room_capacity = room.get('capacity', 'Unknown')

    # Get room events
    events_url = f"https://graph.microsoft.com/v1.0/places/{room_id}/calendarView"
    params = {
        'startDateTime': start_date.isoformat(),
        'endDateTime': end_date.isoformat(),
        '$select': 'id,subject,start,end,attendees'
    }
    events_response = requests.get(events_url, headers=headers, params=params, verify=False)
    events_response.raise_for_status()
    events = events_response.json()['value']

    # Process each event
    for event in events:
        event_id = event['id']
        event_start = event['start']['dateTime']
        event_end = event['end']['dateTime']
        invited_attendees = len(event.get('attendees', []))

        # Get meeting attendance from Verge Sense API
        vs_headers = {
            'Accept': 'application/json',
            'vs-api-key': vs_api_key
        }
        attendance_url = f"https://api.vergesense.com/v1/meetings/{event_id}/attendance"
        attendance_response = requests.get(attendance_url, headers=vs_headers, verify=False)
        attendance_response.raise_for_status()
        actual_attendees = attendance_response.json().get('attendees', 'Unknown')

        # Add meeting data
        meeting_data.append({
            'room_name': room_name,
            'room_capacity': room_capacity,
            'event_start': event_start,
            'event_end': event_end,
            'invited_attendees': invited_attendees,
            'actual_attendees': actual_attendees
        })

# Create and display DataFrame
df = pd.DataFrame(meeting_data)
print(df)
