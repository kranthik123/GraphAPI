import requests
import json
from datetime import datetime, timedelta
import pytz

# Replace with your tenant ID, client ID, and client secret
tenant_id = "<tenant_id>"
client_id = "<client_id>"
client_secret = "<client_secret>"
scope = "https://graph.microsoft.com/.default"

token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_payload = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": scope
}

# Requesting Microsoft Graph API access token
token_response = requests.request("POST", token_url, data=token_payload, verify=False)
token_response.raise_for_status()  # Raise an exception if the request was unsuccessful
token_data = token_response.json()
access_token = token_data.get('access_token')


#Step 2: Get the List of Meeting Rooms and Their Reservations

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Define the date range (previous day)
cst = pytz.timezone('CST6CDT')
end_date = datetime.now(cst).replace(hour=0, minute=0, second=0, microsecond=0)
start_date = end_date - timedelta(days=1)

start_date_str = start_date.isoformat()
end_date_str = end_date.isoformat()

# Get the list of meeting rooms
rooms_url = "https://graph.microsoft.com/v1.0/places/microsoft.graph.room"
rooms_response = requests.request("GET", rooms_url, headers=headers, verify=False)
rooms_response.raise_for_status()
rooms_data = rooms_response.json()

meeting_rooms = []

for room in rooms_data['value']:
    room_name = room['displayName']
    room_capacity = room.get('capacity', 'Unknown')
    room_id = room['id']

    # Get the events for each room for the previous day
    events_url = f"https://graph.microsoft.com/v1.0/places/{room_id}/calendarView?startDateTime={start_date_str}&endDateTime={end_date_str}"
    events_response = requests.request("GET", events_url, headers=headers, verify=False)
    events_response.raise_for_status()
    events_data = events_response.json()

    for event in events_data['value']:
        meeting_rooms.append({
            'room_name': room_name,
            'room_capacity': room_capacity,
            'event_id': event['id'],
            'event_start': event['start']['dateTime'],
            'event_end': event['end']['dateTime']
        })


#Step 3: Get the Number of Attendees from Verge Sense API
# Replace with your Verge Sense API key
vs_api_key = "<vs_api_key>"

vs_headers = {
    'Accept': 'application/json',
    'vs-api-key': vs_api_key
}

# Add attendance data to meeting rooms
for meeting in meeting_rooms:
    event_id = meeting['event_id']
    vs_attendance_url = f"https://api.vergesense.com/v1/meetings/{event_id}/attendance"
    
    vs_response = requests.request("GET", vs_attendance_url, headers=vs_headers, verify=False)
    vs_response.raise_for_status()
    vs_data = vs_response.json()
    
    meeting['attendees'] = vs_data.get('attendees', 'Unknown')

# Display the results in a table format
import pandas as pd

df = pd.DataFrame(meeting_rooms, columns=['room_name', 'room_capacity', 'event_start', 'event_end', 'attendees'])
print(df)