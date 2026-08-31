"""
Gmail service module.

Handles Gmail authentication and email sending using configured paths.
"""

import os
import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import Config
from utils.logger import get_logger
from utils.exceptions import GmailServiceError

logger = get_logger(__name__)

SCOPES = Config.GMAIL_SCOPES


def get_gmail_service():
    """
    Get authenticated Gmail service instance.
    
    Returns:
        Gmail service instance
        
    Raises:
        GmailServiceError: If authentication fails
    """
    try:
        logger.info("Authenticating Gmail service")
        creds = None

        if Config.GMAIL_TOKEN_PATH.exists():
            logger.debug(f"Loading existing token from {Config.GMAIL_TOKEN_PATH}")
            creds = Credentials.from_authorized_user_file(
                str(Config.GMAIL_TOKEN_PATH), 
                SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired token")
                creds.refresh(Request())
            else:
                logger.info("Initiating OAuth flow")
                if not Config.GMAIL_CREDENTIALS_PATH.exists():
                    raise GmailServiceError(
                        f"Gmail credentials file not found: {Config.GMAIL_CREDENTIALS_PATH}. "
                        "Please download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(Config.GMAIL_CREDENTIALS_PATH), 
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(Config.GMAIL_TOKEN_PATH, "w") as token:
                token.write(creds.to_json())
                logger.info(f"Token saved to {Config.GMAIL_TOKEN_PATH}")

        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail service authenticated successfully")
        return service
        
    except Exception as e:
        logger.error(f"Error authenticating Gmail service: {e}", exc_info=True)
        raise GmailServiceError(f"Failed to authenticate Gmail: {e}")


def send_email(to_email, subject, body, resume_file=None, access_token=None):
    """
    Send email with optional PDF attachment.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body
        resume_file: Optional path to PDF attachment
        access_token: OAuth access token for Gmail API
        
    Returns:
        Gmail message send result
        
    Raises:
        GmailServiceError: If email sending fails
    """
    try:
        logger.info(f"Sending email to {to_email}")
        
        # Create credentials from access token
        from google.oauth2.credentials import Credentials
        creds = Credentials(token=access_token)
        
        # Build Gmail service
        service = build("gmail", "v1", credentials=creds)
        
        message = EmailMessage()

        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        if resume_file:
            logger.debug(f"Attaching file: {resume_file}")
            if not os.path.exists(resume_file):
                raise GmailServiceError(f"Attachment file not found: {resume_file}")
            
            with open(resume_file, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(resume_file)

            message.add_attachment(
                file_data,
                maintype="application",
                subtype="pdf",
                filename=file_name
            )

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        send_message = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )

        logger.info(f"Email sent successfully to {to_email}")
        return send_message
        
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        raise GmailServiceError(f"Failed to send email: {e}")