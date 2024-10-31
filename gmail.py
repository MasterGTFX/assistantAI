from dotenv import load_dotenv
import logging
import base64
from email.mime.text import MIMEText

from common import authenticate_gmail

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_emails(context_variables, unread: bool, number_of_emails: int = 30, date_filter: str = None):
    """
    Read emails based on the specified criteria.

    Args:
        context_variables (dict): A dictionary containing context information.
        unread (bool): If True, only fetch unread emails. If False, fetch all emails.
        number_of_emails (int): The maximum number of emails to retrieve, based on the query. Minimum is 30, set to higher if needed.
        date_filter (str, optional): Date filter in Gmail format i.e. 'newer_than:2d', 'older_than:1w'
    """
    logging.info(
        f"Function called: read_emails(context_variables={context_variables}, unread={unread}, number_of_emails={number_of_emails}, date_filter={date_filter})")

    service, _ = authenticate_gmail()
    try:
        query = 'is:unread' if unread else ''
        if date_filter:
            query += ' ' + date_filter
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=number_of_emails
        ).execute()
        messages = results.get('messages', [])

        if not messages:
            return f"<result><message>No {'unread ' if unread else ''}emails found.</message></result>"

        email_info = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg['payload']
            headers = payload['headers']

            email_id = message['id']
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No subject')
            sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown sender')

            # Use the snippet instead of the full body
            snippet = msg.get('snippet', 'No snippet available')

            # Escape special characters in snippet
            snippet = snippet.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            email_info.append(
                f"<email><id>{email_id}</id><from>{sender}</from><subject>{subject}</subject><snippet>{snippet}</snippet></email>")

        result = f"<result>\n{'\n'.join(email_info)}\n</result>"
        logging.info(f"Function read_emails() returned: {len(email_info)} emails")
        return result
    except Exception as e:
        error_message = f"<result><error>Error reading emails: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message


def search_for_emails(context_variables, query: str, max_results: int = 30, date_filter: str = None):
    """
    Search for emails based on the specified query.

    Args:
        context_variables (dict): A dictionary containing context information.
        query (str): The search query to filter emails.
        max_results (int): The maximum number of emails to retrieve, based on the query. Minimum is 30, set to higher if needed.
        date_filter (str, optional): Date filter in Gmail format i.e. 'newer_than:2d', 'older_than:1w'
    """
    logging.info(
        f"Function called: search_for_emails(context_variables={context_variables}, query='{query}', max_results={max_results}, date_filter={date_filter})")

    service, _ = authenticate_gmail()
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        messages = results.get('messages', [])

        if not messages:
            return f"<result><message>No emails found matching the query: '{query}'</message></result>"

        email_info = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg['payload']
            headers = payload['headers']

            email_id = message['id']
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No subject')
            sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown sender')

            # Use the snippet instead of the full body
            snippet = msg.get('snippet', 'No snippet available')

            # Escape special characters in snippet
            snippet = snippet.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            email_info.append(
                f"<email><id>{email_id}</id><from>{sender}</from><subject>{subject}</subject><snippet>{snippet}</snippet></email>")

        result = f"<result>\n{''.join(email_info)}\n</result>"
        logging.info(f"Function search_for_emails() returned: {len(email_info)} emails")
        return result
    except Exception as e:
        error_message = f"<result><error>Error searching emails: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message


def write_email(context_variables, to: str, subject: str, body: str):
    """
    Write and send a new email.

    Args:
        context_variables (dict): A dictionary containing context information.
        to (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): The content of the email.
    """
    logging.info(
        f"Function called: write_email(context_variables={context_variables}, to='{to}', subject='{subject}', body='{body[:20]}...')")

    user_name = context_variables.get("user_name", "User")
    user_email = context_variables.get("email", "unknown@example.com")

    service, _ = authenticate_gmail()
    try:
        message = MIMEText(body)
        message['to'] = to
        message['from'] = user_email
        message['subject'] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        result = f"<result><message>Email sent successfully. Message ID: {message['id']}</message></result>"
        logging.info(f"Function write_email() returned: {result}")
        return result
    except Exception as e:
        error_message = f"<result><error>Error sending email: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message


def get_email_by_id(context_variables, email_id: str):
    """
    Retrieve a specific email by its ID.

    Args:
        context_variables (dict): A dictionary containing context information.
        email_id (str): The unique identifier of the email to retrieve.
    """
    logging.info(f"Function called: get_email_by_id(context_variables={context_variables}, email_id='{email_id}')")

    service, _ = authenticate_gmail()
    try:
        msg = service.users().messages().get(userId='me', id=email_id).execute()
        payload = msg['payload']
        headers = payload['headers']

        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No subject')
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown sender')
        date = next((header['value'] for header in headers if header['name'].lower() == 'date'), 'Unknown date')

        # Handle different payload structures
        body = "No content"
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode()
                    break
        elif payload.get('body', {}).get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode()

        # Escape special characters in body
        body = body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        email_info = f"""<email>
  <id>{email_id}</id>
  <from>{sender}</from>
  <subject>{subject}</subject>
  <date>{date}</date>
  <body>{body}</body>
</email>"""

        result = f"<result>\n{email_info}\n</result>"
        logging.info(f"Function get_email_by_id() returned: Email with ID {email_id}")
        return result
    except Exception as e:
        error_message = f"<result><error>Error retrieving email with ID {email_id}: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message


if __name__ == "__main__":
    logging.info("Generating Gmail token...")
    authenticate_gmail()
    logging.info("Token generated successfully. You can now use this script with agents.")
