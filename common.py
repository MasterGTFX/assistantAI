from dotenv import load_dotenv
import os
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Load environment variables
load_dotenv()


def authenticate_gmail():
    """Authenticate and return Gmail and Calendar services."""
    logging.info("Function called: authenticate_gmail()")
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/calendar',  # Full access to Calendar
        'https://www.googleapis.com/auth/calendar.events'  # Full access to Calendar events
    ]
    creds = None

    # Get the path to credentials.json from environment variable
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    token_path = os.path.join(os.path.dirname(credentials_path), "token.json")

    # Check if token.json exists and has all required fields
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except ValueError:
            # If the file exists but is invalid, we'll regenerate it
            os.remove(token_path)
            creds = None

    # If creds is None or invalid, we need to generate new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            
            # Configure for manual authorization with OOB
            flow.oauth2session.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            logging.info(f"Wating for user to visit the authorization URL: {auth_url}..")
            
            # Wait for the authorization code from user
            # TODO: wait for telegram message with the code
            auth_code = input("Enter the authorization code: ")
            
            # Exchange the authorization code for credentials
            flow.fetch_token(code=auth_code)
            creds = flow.credentials

            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

    service_gmail = build('gmail', 'v1', credentials=creds)
    service_calendar = build('calendar', 'v3', credentials=creds)
    logging.info("Function authenticate_gmail() returned: Gmail and Calendar service objects")
    return service_gmail, service_calendar
