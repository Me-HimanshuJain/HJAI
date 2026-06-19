import datetime
import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class CalendarClient:
    def __init__(self, credentials_file="credentials.json", token_file="token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
                
        return build('calendar', 'v3', credentials=creds)

    def get_todays_meetings(self):
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        end_of_day = (datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat() + 'Z'
        
        logger.info("Fetching today's meetings from Google Calendar.")
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now, timeMax=end_of_day,
            maxResults=10, singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        meeting_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            title = event.get('summary', 'Untitled Event')
            description = event.get('description', '')
            
            # Check for meeting links
            link = None
            if 'hangoutLink' in event:
                link = event['hangoutLink']
            elif 'zoom.us' in description:
                # Extract zoom link logic here
                pass
                
            # Filter private meetings
            is_private = any(keyword in title.lower() or keyword in description.lower() 
                             for keyword in ['1:1 medical', 'hr confidential', 'personal', 'private'])
                             
            if link and not is_private:
                meeting_list.append({
                    "title": title,
                    "start_time": start,
                    "link": link
                })
                
        return meeting_list
