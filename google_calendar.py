from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
from common import authenticate_gmail

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def list_upcoming_events(context_variables, max_results: int = 10, time_min: str = None):
    """
    List upcoming calendar events.

    Args:
        context_variables (dict): A dictionary containing context information.
        max_results (int): Maximum number of events to return.
        time_min (str, optional): Start time in ISO format. If None, uses current time.
    """
    logging.info(
        f"Function called: list_upcoming_events(context_variables={context_variables}, max_results={max_results}, time_min={time_min})")

    _, service = authenticate_gmail()
    try:
        if not time_min:
            time_min = datetime.utcnow().isoformat() + 'Z'
        else:
            # Convert the input time to datetime and ensure UTC format
            try:
                # Parse the input time
                dt = datetime.fromisoformat(time_min)
                # Convert to UTC and format with 'Z' suffix
                time_min = dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            except ValueError as e:
                return f"<result><error>Invalid time format: {str(e)}</error></result>"

        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return "<result><message>No upcoming events found.</message></result>"

        event_info = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            attendees = event.get('attendees', [])
            attendee_list = [attendee['email'] for attendee in attendees if 'email' in attendee]

            event_info.append(f"""<event>
    <id>{event['id']}</id>
    <summary>{event.get('summary', 'No title')}</summary>
    <start>{start}</start>
    <end>{end}</end>
    <location>{event.get('location', 'No location')}</location>
    <description>{event.get('description', 'No description')}</description>
    <attendees>{', '.join(attendee_list)}</attendees>
</event>""")

        result = f"<result>\n{''.join(event_info)}\n</result>"
        logging.info(f"Function list_upcoming_events() returned: {len(event_info)} events")
        return result
    except Exception as e:
        error_message = f"<result><error>Error listing events: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message


def create_event(context_variables, summary: str, start_time: str, end_time: str,
                 description: str = None, location: str = None, attendees: str = None):
    """
    Create a new calendar event.

    Args:
        context_variables (dict): A dictionary containing context information.
        summary (str): Title of the event.
        start_time (str): Start time in ISO format.
        end_time (str): End time in ISO format.
        description (str, optional): Description of the event.
        location (str, optional): Location of the event.
        attendees (str, optional): List of attendee email addresses, separated by commas (',').
    """
    logging.info(
        f"Function called: create_event(context_variables={context_variables}, summary='{summary}', start_time='{start_time}', end_time='{end_time}')")

    _, service = authenticate_gmail()
    try:
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }

        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees.split(',')]

        event = service.events().insert(calendarId='primary', body=event).execute()

        result = f"<result><message>Event created successfully. Event ID: {event['id']}</message></result>"
        logging.info(f"Function create_event() returned: {result}")
        return result
    except Exception as e:
        error_message = f"<result><error>Error creating event: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message


def delete_event(context_variables, event_id: str):
    """
    Delete a calendar event by ID.

    Args:
        context_variables (dict): A dictionary containing context information.
        event_id (str): The ID of the event to delete.
    """
    logging.info(f"Function called: delete_event(context_variables={context_variables}, event_id='{event_id}')")

    _, service = authenticate_gmail()
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        result = f"<result><message>Event {event_id} deleted successfully.</message></result>"
        logging.info(f"Function delete_event() returned: {result}")
        return result
    except Exception as e:
        error_message = f"<result><error>Error deleting event: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message


def update_event(context_variables, event_id: str, summary: str = None, start_time: str = None,
                 end_time: str = None, description: str = None, location: str = None,
                 attendees: str = None):
    """
    Update an existing calendar event.

    Args:
        context_variables (dict): A dictionary containing context information.
        event_id (str): The ID of the event to update.
        summary (str, optional): New title of the event.
        start_time (str, optional): New start time in ISO format.
        end_time (str, optional): New end time in ISO format.
        description (str, optional): New description of the event.
        location (str, optional): New location of the event.
        attendees (str, optional): List of attendee email addresses, separated by commas (',').
    """
    logging.info(f"Function called: update_event(context_variables={context_variables}, event_id='{event_id}')")

    _, service = authenticate_gmail()
    try:
        # Get the existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update the fields that are provided
        if summary:
            event['summary'] = summary
        if start_time:
            event['start']['dateTime'] = start_time
        if end_time:
            event['end']['dateTime'] = end_time
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees.split(',')]

        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()

        result = f"<result><message>Event {event_id} updated successfully.</message></result>"
        logging.info(f"Function update_event() returned: {result}")
        return result
    except Exception as e:
        error_message = f"<result><error>Error updating event: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message
