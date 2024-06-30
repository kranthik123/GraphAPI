import requests
import urllib3
from datetime import datetime, timedelta
import pytz
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Set date range for the previous calendar day
cst = pytz.timezone('America/Chicago')
today = datetime.now(cst).replace(hour=0, minute=0, second=0, microsecond=0)
start_date = today - timedelta(days=1)
end_date = today

logging.info(f"Fetching data for: {start_date.date()}")

meeting_data = []
rooms_processed = 0
rooms_with_data = 0

# Process each room
for room in rooms:
    room_id = room['id']
    room_name = room['displayName']
    room_capacity = room.get('capacity', 'Unknown')

    logging.info(f"Processing room: {room_name}")
    rooms_processed += 1

    # Get room events
    events_url = f"https://graph.microsoft.com/v1.0/places/{room_id}/calendarView"
    params = {
        'startDateTime': start_date.isoformat(),
        'endDateTime': end_date.isoformat(),
        '$select': 'id,subject,start,end,attendees'
    }
    
    try:
        events_response = requests.get(events_url, headers=headers, params=params, verify=False)
        events_response.raise_for_status()
        events = events_response.json()['value']
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred for room {room_name}: {e}")
        continue
    except Exception as e:
        logging.error(f"An error occurred for room {room_name}: {e}")
        continue

    if not events:
        logging.info(f"No events found for room: {room_name}")
        continue

    rooms_with_data += 1

    # Process each event
    for event in events:
        event_id = event['id']
        event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
        event_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
        
        # Only process events that occurred on the previous day
        if start_date <= event_start.astimezone(cst) < end_date:
            invited_attendees = len(event.get('attendees', []))

            # Get meeting attendance from Verge Sense API
            vs_headers = {
                'Accept': 'application/json',
                'vs-api-key': vs_api_key
            }
            attendance_url = f"https://api.vergesense.com/v1/meetings/{event_id}/attendance"
            try:
                attendance_response = requests.get(attendance_url, headers=vs_headers, verify=False)
                attendance_response.raise_for_status()
                actual_attendees = attendance_response.json().get('attendees', 'Unknown')
            except requests.exceptions.RequestException as e:
                logging.warning(f"Error getting attendance for event {event_id}: {e}")
                actual_attendees = 'Error'

            # Add meeting data
            meeting_data.append({
                'room_name': room_name,
                'room_capacity': room_capacity,
                'event_start': event_start.astimezone(cst),
                'event_end': event_end.astimezone(cst),
                'invited_attendees': invited_attendees,
                'actual_attendees': actual_attendees
            })

# Create and display DataFrame
df = pd.DataFrame(meeting_data)
if not df.empty:
    df['event_date'] = df['event_start'].dt.date
    df = df.sort_values('event_start')
    print(df)
    
    # Optional: Save to CSV
    # df.to_csv(f"meeting_data_{start_date.date()}.csv", index=False)
else:
    logging.warning("No meeting data collected.")

logging.info(f"Script execution completed. Processed {rooms_processed} rooms, {rooms_with_data} had data.")
