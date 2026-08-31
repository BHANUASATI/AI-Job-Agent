"""
Authentication module for AI Job Agent.

Handles user authentication, JWT tokens, and OAuth flows for Google and Outlook.
"""

import os
import json
import requests as _requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
import sqlite3
from utils.logger import get_logger
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# OAuth Configuration
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI",  "http://localhost:8000/api/auth/google/callback")

OUTLOOK_CLIENT_ID     = os.getenv("OUTLOOK_CLIENT_ID", "")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET", "")
OUTLOOK_REDIRECT_URI  = os.getenv("OUTLOOK_REDIRECT_URI",  "http://localhost:8000/api/auth/outlook/callback")
OUTLOOK_TENANT_ID     = os.getenv("OUTLOOK_TENANT_ID",     "common")

# Frontend base URL — where to redirect after OAuth
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "users.db"


class User(BaseModel):
    id: int
    email: str
    name: str
    google_connected: bool = False
    outlook_connected: bool = False
    created_at: str


class UserCreate(BaseModel):
    email: str
    password: str
    name: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class OAuthToken(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[int] = None


def init_database():
    """Initialize SQLite database for users."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            name TEXT NOT NULL,
            google_connected BOOLEAN DEFAULT FALSE,
            outlook_connected BOOLEAN DEFAULT FALSE,
            google_token TEXT,
            outlook_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            company TEXT,
            role TEXT,
            resume_file TEXT,
            match_score REAL,
            status TEXT DEFAULT 'pending',
            email_sent BOOLEAN DEFAULT FALSE,
            email_subject TEXT,
            email_body TEXT,
            recipient_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Migration: add new columns if they don't exist yet (for existing DBs)
    for col, coldef in [
        ("email_subject",   "TEXT"),
        ("email_body",      "TEXT"),
        ("recipient_email", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE job_applications ADD COLUMN {col} {coldef}")
        except Exception:
            pass  # column already exists
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_user(user: UserCreate) -> User:
    """Create new user in database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        password_hash = get_password_hash(user.password)
        cursor.execute(
            """
            INSERT INTO users (email, password_hash, name)
            VALUES (?, ?, ?)
            """,
            (user.email, password_hash, user.name)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        return User(
            id=row[0],
            email=row[1],
            name=row[3],
            google_connected=bool(row[4]),
            outlook_connected=bool(row[5]),
            created_at=str(row[8]) if row[8] else ""
        )
    except sqlite3.IntegrityError:
        raise ConfigurationError("User with this email already exists")
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    if not verify_password(password, row[2]):
        return None
    
    return User(
        id=row[0],
        email=row[1],
        name=row[3],
        google_connected=bool(row[4]),
        outlook_connected=bool(row[5]),
        created_at=str(row[8]) if row[8] else ""
    )


def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return User(
        id=row[0],
        email=row[1],
        name=row[3],
        google_connected=bool(row[4]),
        outlook_connected=bool(row[5]),
        created_at=str(row[8]) if row[8] else ""
    )


def update_oauth_token(user_id: int, provider: str, token_data: Dict):
    """Update OAuth token for user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Normalise: "gmail" is stored under the "google" column
    if provider in ("google", "gmail"):
        cursor.execute(
            """
            UPDATE users 
            SET google_token = ?, google_connected = TRUE 
            WHERE id = ?
            """,
            (json.dumps(token_data), user_id)
        )
    elif provider in ("outlook", "microsoft"):
        cursor.execute(
            """
            UPDATE users 
            SET outlook_token = ?, outlook_connected = TRUE 
            WHERE id = ?
            """,
            (json.dumps(token_data), user_id)
        )
    
    conn.commit()
    conn.close()
    logger.info(f"Updated {provider} OAuth token for user {user_id}")


def get_oauth_token(user_id: int, provider: str) -> Optional[Dict]:
    """Get OAuth token for user, refreshing if expired."""
    logger.info(f"Getting {provider} token for user {user_id}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Normalise: "gmail" maps to the google_token column
    is_google = provider in ("google", "gmail")

    if is_google:
        cursor.execute("SELECT google_token FROM users WHERE id = ?", (user_id,))
    else:
        cursor.execute("SELECT outlook_token FROM users WHERE id = ?", (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row[0]:
        logger.warning(f"No {provider} token found for user {user_id}")
        return None
    
    token_data = json.loads(row[0])
    logger.info(f"Retrieved {provider} token for user {user_id}, expires at {token_data.get('expires_at')}")
    
    # Always refresh Google tokens to ensure they're valid
    if is_google and token_data.get("refresh_token"):
        logger.info(f"Refreshing {provider} token for user {user_id} to ensure validity")
        token_data = refresh_google_token(token_data)
        # Update in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET google_token = ? WHERE id = ?",
            (json.dumps(token_data), user_id)
        )
        conn.commit()
        conn.close()
    
    return token_data


def refresh_google_token(token_data: Dict) -> Dict:
    """Refresh Google OAuth token using refresh token."""
    try:
        import requests
        
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            logger.warning("No refresh token available, cannot refresh")
            return token_data
        
        logger.info("Attempting to refresh Google token...")
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": token_data.get("client_id"),
                "client_secret": token_data.get("client_secret"),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )
        
        if response.status_code == 200:
            new_token_data = response.json()
            # Update existing token data with new access token
            token_data["access_token"] = new_token_data.get("access_token")
            if new_token_data.get("expires_in"):
                import time
                token_data["expires_at"] = time.time() + new_token_data.get("expires_in")
            logger.info(f"Google token refreshed successfully, new expires_at: {token_data['expires_at']}")
            return token_data
        else:
            logger.error(f"Failed to refresh Google token: {response.status_code} - {response.text}")
            return token_data
            
    except Exception as e:
        logger.error(f"Error refreshing Google token: {e}", exc_info=True)
        return token_data


def _google_flow(redirect_uri: str):
    """Build a Google OAuth Flow from the client secret JSON file or env vars."""
    from google_auth_oauthlib.flow import Flow

    # Prefer the downloaded credentials JSON file if it exists
    secret_file = Path(__file__).parent.parent / "credentials.json"
    # Fall back to old filename
    if not secret_file.exists():
        secret_file = Path(__file__).parent.parent / (
            "client_secret_335765392378-uoibo0cfst565sbmulv4qfvjkmja5erl.apps.googleusercontent.com.json"
        )

    scopes = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.send",
        "openid",
    ]

    if secret_file.exists():
        # Load from file and inject redirect_uri so Google accepts it
        with open(secret_file) as f:
            client_config = json.load(f)
        # Inject the redirect URI into the config so it matches what we send
        client_config["web"]["redirect_uris"] = [redirect_uri]
        flow = Flow.from_client_config(client_config, scopes=scopes)
    else:
        # Fall back to env vars
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            },
            scopes=scopes,
        )

    flow.redirect_uri = redirect_uri
    return flow


def get_google_auth_url() -> str:
    """Generate Google OAuth authorization URL."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ConfigurationError("Google OAuth credentials not configured")

    import urllib.parse
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         " ".join([
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/gmail.send",
            "openid",
        ]),
        "access_type":   "offline",
        "prompt":        "consent",
        "include_granted_scopes": "true",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)


def exchange_google_code(code: str) -> Dict:
    """Exchange Google authorization code for tokens (no PKCE / no flow object)."""
    import requests as _requests
    resp = _requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code":          code,
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri":  GOOGLE_REDIRECT_URI,
            "grant_type":    "authorization_code",
        },
        timeout=15,
    )
    if not resp.ok:
        raise ValueError(f"Token exchange failed: {resp.status_code} {resp.text}")
    token_data = resp.json()
    return {
        "access_token":  token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "token_uri":     "https://oauth2.googleapis.com/token",
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "scopes":        token_data.get("scope", "").split(),
        "expires_at":    None,
    }


def get_outlook_auth_url() -> str:
    """Generate Outlook OAuth authorization URL."""
    if not OUTLOOK_CLIENT_ID or not OUTLOOK_CLIENT_SECRET:
        raise ConfigurationError("Outlook OAuth credentials not configured")
    
    import msal
    
    config = {
        "authority": f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}",
        "client_id": OUTLOOK_CLIENT_ID,
        "client_secret": OUTLOOK_CLIENT_SECRET,
        "scope": ["https://graph.microsoft.com/Mail.Send", "https://graph.microsoft.com/User.Read"]
    }
    
    app = msal.ConfidentialClientApplication(
        config["client_id"],
        authority=config["authority"],
        client_credential=config["client_secret"]
    )
    
    auth_url = app.get_authorization_request_url(
        scopes=config["scope"],
        redirect_uri=OUTLOOK_REDIRECT_URI
    )
    
    return auth_url


def exchange_outlook_code(code: str) -> Dict:
    """Exchange Outlook authorization code for tokens."""
    import msal
    
    app = msal.ConfidentialClientApplication(
        OUTLOOK_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}",
        client_credential=OUTLOOK_CLIENT_SECRET
    )
    
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=["https://graph.microsoft.com/Mail.Send", "https://graph.microsoft.com/User.Read"],
        redirect_uri=OUTLOOK_REDIRECT_URI
    )
    
    if "error" in result:
        raise ConfigurationError(f"Outlook token exchange failed: {result.get('error_description')}")

    return result


# ─────────────────────────────────────────────────────────────
#  USER-INFO HELPERS  (called after code exchange)
# ─────────────────────────────────────────────────────────────

def get_google_user_info(access_token: str) -> Dict:
    """Fetch the authenticated user's profile from Google."""
    resp = _requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()   # keys: sub, email, name, picture, email_verified


def get_microsoft_user_info(access_token: str) -> Dict:
    """Fetch the authenticated user's profile from Microsoft Graph."""
    resp = _requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()   # keys: id, displayName, mail, userPrincipalName


# ─────────────────────────────────────────────────────────────
#  UPSERT USER  (create if new, update OAuth token if existing)
# ─────────────────────────────────────────────────────────────

def get_or_create_oauth_user(email: str, name: str, provider: str, token_data: Dict) -> "User":
    """
    Look up a user by email.
    - If they exist, update their OAuth token and mark the provider connected.
    - If they don't exist, create a new account (no password) and store the token.
    Returns a populated User object.
    """
    logger.info(f"get_or_create_oauth_user called for email={email}, provider={provider}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()

        token_json = json.dumps(token_data)

        if row:
            user_id = row[0]
            logger.info(f"Updating existing user {user_id}")
            
            if provider == "google":
                cursor.execute(
                    "UPDATE users SET google_token = ?, google_connected = TRUE, name = ? WHERE id = ?",
                    (token_json, name, user_id),
                )
            else:  # outlook
                cursor.execute(
                    "UPDATE users SET outlook_token = ?, outlook_connected = TRUE, name = ? WHERE id = ?",
                    (token_json, name, user_id),
                )
            conn.commit()
            logger.info("Database updated successfully")
            
            # Re-fetch so we get updated flags
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
        else:
            # Brand-new user — no password (OAuth-only account)
            logger.info("Creating new user")
            
            if provider == "google":
                cursor.execute(
                    """INSERT INTO users (email, password_hash, name, google_token, google_connected)
                       VALUES (?, NULL, ?, ?, TRUE)""",
                    (email, name, token_json),
                )
            else:
                cursor.execute(
                    """INSERT INTO users (email, password_hash, name, outlook_token, outlook_connected)
                       VALUES (?, NULL, ?, ?, TRUE)""",
                    (email, name, token_json),
                )
            conn.commit()
            logger.info(f"New user created with ID: {cursor.lastrowid}")
            
            cursor.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,))
            row = cursor.fetchone()

        return User(
            id=row[0],
            email=row[1],
            name=row[3],
            google_connected=bool(row[4]),
            outlook_connected=bool(row[5]),
            created_at=str(row[8]) if row[8] else "",
        )

    finally:
        conn.close()


# Initialize database on module load
init_database()
