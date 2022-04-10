from __future__ import print_function
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64
import os.path
from threading import Thread
from flask import current_app, render_template

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def send_async_email(message):
    try:
        service = get_api_service()
        send = (service.users().messages().send(userId='me', body=message)
               .execute())
        return send
    except HttpError as error:
        print(f'An error occurred: {error}')
        raise Exception("Something when wrong: {error}")


def send_email(to,subject,template,**kwargs):
    message = create_email_message('me',to,subject,
                render_template(template + ".txt", **kwargs))
    thr = Thread(target=send_async_email, args=(message,))
    thr.start()
    return thr


def get_api_service():
    """ Returns an Authorized Gmail API service instance."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        raise Exception(f"Access to Gmail API failed: {error}")


def create_email_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """

    app = current_app._get_current_object()
    message = MIMEText(message_text)
    print(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = app.config["MAIL_SUBJECT_PREFIX"] + subject
    b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': b64_bytes.decode()}
