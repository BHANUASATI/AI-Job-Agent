"""
Outlook email service module.

Handles Outlook OAuth authentication and email sending using Microsoft Graph API.
"""

import os
import base64
from pathlib import Path
from utils.logger import get_logger
from utils.exceptions import EmailGenerationError

logger = get_logger(__name__)


def send_email(to_email: str, subject: str, body: str, resume_file: str = None, access_token: str = None):
    """
    Send email using Microsoft Graph API (Outlook).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        resume_file: Full path to resume PDF file
        access_token: Microsoft OAuth access token
        
    Returns:
        dict with send status and message ID
        
    Raises:
        EmailGenerationError: If email sending fails
    """
    try:
        import requests
        
        logger.info(f"Sending Outlook email to {to_email}")
        
        # Read resume file if provided
        resume_content = None
        resume_filename = None
        if resume_file:
            resume_path = Path(resume_file)
            if not resume_path.exists():
                raise EmailGenerationError(f"Resume file not found: {resume_file}")
            
            resume_filename = resume_path.name
            with open(resume_path, "rb") as f:
                resume_content = base64.b64encode(f.read()).decode()
        
        # Microsoft Graph API endpoint for sending emails
        url = "https://graph.microsoft.com/v1.0/me/sendMail"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Construct email message
        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body.replace("\n", "<br>")
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            }
        }
        
        # Add attachment if resume file is provided
        if resume_content and resume_filename:
            email_data["message"]["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": resume_filename,
                    "contentType": "application/pdf",
                    "contentBytes": resume_content
                }
            ]
        
        response = requests.post(url, headers=headers, json=email_data)
        
        if response.status_code == 202:
            logger.info(f"Outlook email sent successfully to {to_email}")
            return {
                "status": "sent",
                "message": "Email sent successfully via Outlook",
                "provider": "outlook"
            }
        else:
            error_msg = f"Outlook API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise EmailGenerationError(error_msg)
            
    except Exception as e:
        logger.error(f"Error sending Outlook email: {e}", exc_info=True)
        raise EmailGenerationError(f"Failed to send Outlook email: {str(e)}")


def get_auth_url(redirect_uri: str) -> str:
    """
    Generate Microsoft OAuth authorization URL.
    
    Args:
        redirect_uri: OAuth redirect URI
        
    Returns:
        Authorization URL
    """
    client_id = os.getenv("OUTLOOK_CLIENT_ID")
    tenant_id = os.getenv("OUTLOOK_TENANT_ID", "common")
    
    if not client_id:
        raise EmailGenerationError("OUTLOOK_CLIENT_ID not configured")
    
    scopes = ["https://graph.microsoft.com/Mail.Send"]
    
    auth_url = (
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"scope={' '.join(scopes)}&"
        f"response_mode=query"
    )
    
    return auth_url


def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    """
    Exchange authorization code for access token.
    
    Args:
        code: Authorization code from OAuth callback
        redirect_uri: OAuth redirect URI
        
    Returns:
        dict with access token and refresh token
    """
    import requests
    
    client_id = os.getenv("OUTLOOK_CLIENT_ID")
    client_secret = os.getenv("OUTLOOK_CLIENT_SECRET")
    tenant_id = os.getenv("OUTLOOK_TENANT_ID", "common")
    
    if not client_id or not client_secret:
        raise EmailGenerationError("Outlook OAuth credentials not configured")
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise EmailGenerationError(f"Token exchange failed: {response.text}")
