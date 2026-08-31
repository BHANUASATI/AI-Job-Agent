"""
FastAPI backend for AI Job Agent.
Serves React frontend and provides API endpoints for job application automation.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Required for OAuth over plain HTTP on localhost (dev only)
import os
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil

from agents.jd_analyzer import analyze_jd
from agents.resume_retriever import find_best_resume
from agents.email_generator import generate_email
from agents.subject_generator import generate_subject
from services.gmail_service import send_email as send_gmail
from services.outlook_service import send_email as send_outlook
from services.jd_parser import get_jd_parser
from utils.logger import get_logger
from backend.auth import (
    User, UserCreate, Token, create_user, authenticate_user,
    create_access_token, verify_token, get_user_by_id,
    update_oauth_token, get_oauth_token,
    get_google_auth_url, exchange_google_code,
    get_outlook_auth_url, exchange_outlook_code,
    get_google_user_info, get_microsoft_user_info,
    get_or_create_oauth_user,
    GOOGLE_CLIENT_ID, OUTLOOK_CLIENT_ID,
    FRONTEND_URL,
)

logger = get_logger(__name__)

app = FastAPI(title="AI Job Agent API", version="2.0.0")

# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    user = get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# Serve React frontend
frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(frontend_path / "index.html"))

# Pydantic models
class JobAnalysisRequest(BaseModel):
    job_description: str
    job_url: Optional[str] = None

class EmailRequest(BaseModel):
    job_details: dict
    resume_content: str
    user_profile: dict
    email_provider: str  # "gmail" or "outlook"
    access_token: Optional[str] = None  # not used; backend fetches from DB

class ResumeUploadResponse(BaseModel):
    filename: str
    size: int
    message: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AutoApplyRequest(BaseModel):
    job_description: str
    job_url: Optional[str] = None
    auto_send: bool = False

class JDUploadResponse(BaseModel):
    filename: str
    size: int
    extracted_text: str
    message: str

# API Endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

@app.get("/api/auth/config")
async def auth_config():
    """Tell the frontend which OAuth providers are actually configured."""
    placeholder_values = {"", "your-google-client-id", "your-outlook-client-id"}
    return {
        "google_oauth_enabled":  bool(GOOGLE_CLIENT_ID  and GOOGLE_CLIENT_ID  not in placeholder_values),
        "outlook_oauth_enabled": bool(OUTLOOK_CLIENT_ID and OUTLOOK_CLIENT_ID not in placeholder_values),
    }

# Authentication Endpoints
@app.post("/api/auth/signup", response_model=User)
async def signup(user: UserCreate):
    """Register a new user."""
    try:
        new_user = create_user(user)
        return new_user
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@app.get("/api/auth/google")
async def google_auth():
    """Get Google OAuth authorization URL."""
    if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID in ("your-google-client-id", ""):
        raise HTTPException(
            status_code=400,
            detail="Google OAuth is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file."
        )
    try:
        auth_url = get_google_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Google auth error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/google/callback")
async def google_callback(code: str, state: Optional[str] = None, error: Optional[str] = None):
    """
    Google redirects here after the user grants/denies permission.
    1. Exchange code for tokens
    2. Fetch user profile from Google
    3. Upsert user in DB
    4. Issue our own JWT
    5. Redirect to frontend /auth/callback?token=<jwt>
    """
    import urllib.parse
    import os
    # Required for OAuth over plain HTTP on localhost
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    if error:
        logger.warning(f"Google OAuth denied by user: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?error={urllib.parse.quote(error)}")

    try:
        logger.info(f"Google callback received, exchanging code (state={state})")
        token_data = exchange_google_code(code)
        logger.info("Code exchanged successfully, fetching user info")

        user_info = get_google_user_info(token_data["access_token"])
        logger.info(f"Got user info: email={user_info.get('email')}")

        email = user_info.get("email")
        name  = user_info.get("name") or (email.split("@")[0] if email else "User")

        if not email:
            raise ValueError("Google did not return an email address")

        user = get_or_create_oauth_user(email, name, "google", token_data)
        access_token = create_access_token(data={"sub": str(user.id)})

        logger.info(f"Google OAuth success for {email} (user_id={user.id})")
        redirect_url = f"{FRONTEND_URL}/auth/callback?token={access_token}&provider=google"
        logger.info(f"Redirecting to frontend: {FRONTEND_URL}/auth/callback?provider=google&token=<hidden>")
        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as e:
        logger.error(f"Google callback error: {type(e).__name__}: {e}", exc_info=True)
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?error={urllib.parse.quote(str(e))}",
            status_code=302,
        )

@app.get("/api/auth/outlook")
async def outlook_auth():
    """Get Outlook OAuth authorization URL."""
    if not OUTLOOK_CLIENT_ID or OUTLOOK_CLIENT_ID in ("your-outlook-client-id", ""):
        raise HTTPException(
            status_code=400,
            detail="Outlook OAuth is not configured. Add OUTLOOK_CLIENT_ID and OUTLOOK_CLIENT_SECRET to your .env file."
        )
    try:
        auth_url = get_outlook_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Outlook auth error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/outlook/callback")
async def outlook_callback(code: str, state: Optional[str] = None, error: Optional[str] = None):
    """
    Microsoft redirects here after the user grants/denies permission.
    1. Exchange code for tokens
    2. Fetch user profile from Microsoft Graph
    3. Upsert user in DB
    4. Issue our own JWT
    5. Redirect to frontend /auth/callback?token=<jwt>
    """
    if error:
        logger.warning(f"Microsoft OAuth denied: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?error={error}")

    try:
        token_data   = exchange_outlook_code(code)
        access_token = token_data.get("access_token")
        user_info    = get_microsoft_user_info(access_token)

        email = (
            user_info.get("mail")
            or user_info.get("userPrincipalName")
            or ""
        )
        name = user_info.get("displayName") or email.split("@")[0]

        if not email:
            raise ValueError("Microsoft did not return an email address")

        user = get_or_create_oauth_user(email, name, "outlook", token_data)
        jwt_token = create_access_token(data={"sub": str(user.id)})

        logger.info(f"Microsoft OAuth success for {email} (user_id={user.id})")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}&provider=outlook"
        )

    except Exception as e:
        logger.error(f"Outlook callback error: {e}", exc_info=True)
        import urllib.parse
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?error={urllib.parse.quote(str(e))}"
        )

@app.post("/api/auth/connect/{provider}")
async def connect_provider(provider: str, code: str, current_user: User = Depends(get_current_user)):
    """Connect OAuth provider to user account."""
    try:
        if provider == "google":
            token_data = exchange_google_code(code)
            update_oauth_token(current_user.id, "google", token_data)
        elif provider == "outlook":
            token_data = exchange_outlook_code(code)
            update_oauth_token(current_user.id, "outlook", token_data)
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        return {"message": f"{provider.capitalize()} connected successfully"}
    except Exception as e:
        logger.error(f"Connect provider error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/analyze-job")
async def analyze_job(request: JobAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Analyze job description and extract structured information."""
    try:
        logger.info(f"Analyzing job description: {request.job_description[:100]}...")
        
        result = analyze_jd(request.job_description)
        
        return {
            "success": True,
            "data": {
                "company": result.company,
                "role": result.role,
                "skills": result.skills,
                "experience": result.experience,
                "email": result.email,
                "location": result.location,
                "keywords": result.keywords
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload and store resume PDF."""
    try:
        user_resumes_dir = Path(__file__).parent.parent / "data" / "resumes" / str(current_user.id)
        user_resumes_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = user_resumes_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Resume uploaded for user {current_user.id}: {file.filename}")
        
        # Insert record into database
        import sqlite3
        db_path = Path(__file__).parent.parent / "data" / "users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ensure resumes table exists
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
        
        cursor.execute(
            "INSERT INTO resumes (user_id, filename, file_path) VALUES (?, ?, ?)",
            (current_user.id, file.filename, str(file_path))
        )
        conn.commit()
        conn.close()
        
        return ResumeUploadResponse(
            filename=file.filename,
            size=file_path.stat().st_size,
            message="Resume uploaded successfully"
        )
    except Exception as e:
        logger.error(f"Error uploading resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes")
async def list_resumes(current_user: User = Depends(get_current_user)):
    """List all available resumes for user."""
    try:
        import sqlite3
        db_path = Path(__file__).parent.parent / "data" / "users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ensure resumes table exists
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
        
        cursor.execute(
            "SELECT filename, file_path, created_at FROM resumes WHERE user_id = ?",
            (current_user.id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        resumes = []
        for row in rows:
            file_path = Path(row[1])
            if file_path.exists():
                resumes.append({
                    "filename": row[0],
                    "size": file_path.stat().st_size,
                    "uploaded": row[2]
                })
        
        return {"success": True, "data": resumes}
    except Exception as e:
        logger.error(f"Error listing resumes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-jd")
async def upload_jd(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload and parse job description file (PDF, DOCX, TXT)."""
    try:
        # Sanitize filename to prevent path traversal
        original_filename = file.filename
        if not original_filename or '..' in original_filename or '/' in original_filename or '\\' in original_filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename"
            )
        
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.txt'}
        file_ext = Path(original_filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Validate MIME type
        allowed_mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain'
        }
        
        if file.content_type not in list(allowed_mime_types.values()):
            logger.warning(f"Suspicious MIME type: {file.content_type} for file: {original_filename}")
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size / (1024*1024)}MB"
            )
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Parse the JD file
        jd_parser = get_jd_parser()
        extracted_text = jd_parser.parse_jd_file(file_content, original_filename)
        
        logger.info(f"JD file uploaded and parsed successfully for user {current_user.id}: {original_filename}")
        
        return JDUploadResponse(
            filename=original_filename,
            size=len(file_content),
            extracted_text=extracted_text,
            message="Job description parsed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading JD file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse job description file: {str(e)}")

@app.delete("/api/resumes/{filename}")
async def delete_resume(filename: str, current_user: User = Depends(get_current_user)):
    """Delete a resume."""
    try:
        user_resumes_dir = Path(__file__).parent.parent / "data" / "resumes" / str(current_user.id)
        file_path = user_resumes_dir / filename
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Resume deleted: {filename}")
            
            # Delete record from database
            import sqlite3
            db_path = Path(__file__).parent.parent / "data" / "users.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Ensure resumes table exists
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
            
            cursor.execute(
                "DELETE FROM resumes WHERE user_id = ? AND filename = ?",
                (current_user.id, filename)
            )
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "Resume deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Resume not found")
    except Exception as e:
        logger.error(f"Error deleting resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match-resume")
async def match_resume(job_details: dict, current_user: User = Depends(get_current_user)):
    """Find best matching resume for job."""
    try:
        logger.info(f"Matching resume for job: {job_details.get('role')}")
        
        # Update resume retriever to use user-specific directory
        best_resume = find_best_resume(job_details)
        
        return {
            "success": True,
            "data": {
                "resume_file": best_resume.get("filename"),
                "match_score": best_resume.get("score"),
                "resume_content": best_resume.get("resume_content")
            }
        }
    except Exception as e:
        logger.error(f"Error matching resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-email")
async def generate_application_email(request: EmailRequest, current_user: User = Depends(get_current_user)):
    """Generate personalized application email."""
    try:
        logger.info(f"Generating email for {request.job_details.get('role')}")
        
        email_content = generate_email(
            request.job_details,
            request.resume_content,
            request.user_profile
        )
        
        subject = generate_subject(
            request.job_details,
            request.user_profile
        )
        
        return {
            "success": True,
            "data": {
                "subject": subject,
                "body": email_content
            }
        }
    except Exception as e:
        logger.error(f"Error generating email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send-email")
async def send_application_email(request: EmailRequest, current_user: User = Depends(get_current_user)):
    """Send application email via selected provider."""
    try:
        logger.info(f"Sending email via {request.email_provider}")
        
        # Get OAuth token from user's connected provider
        token_data = get_oauth_token(current_user.id, request.email_provider)
        
        if not token_data:
            raise HTTPException(
                status_code=400,
                detail=f"{request.email_provider.capitalize()} not connected. Please connect your account first."
            )
        
        access_token = token_data.get("access_token")

        to_email = request.job_details.get("email")
        if not to_email:
            raise HTTPException(
                status_code=400,
                detail="No recipient email found in the job details. Make sure the job description includes a recruiter email address."
            )

        if request.email_provider == "gmail":
            # Construct full path to resume file
            resume_filename = request.job_details.get("resume_file")
            resume_path = None
            if resume_filename:
                resume_path = str(Path(__file__).parent.parent / "data" / "resumes" / str(current_user.id) / resume_filename)
            
            result = send_gmail(
                to_email=to_email,
                subject=request.job_details.get("subject"),
                body=request.job_details.get("body"),
                resume_file=resume_path,
                access_token=access_token
            )
        elif request.email_provider == "outlook":
            # Construct full path to resume file
            resume_filename = request.job_details.get("resume_file")
            resume_path = None
            if resume_filename:
                resume_path = str(Path(__file__).parent.parent / "data" / "resumes" / str(current_user.id) / resume_filename)
            
            result = send_outlook(
                to_email=to_email,
                subject=request.job_details.get("subject"),
                body=request.job_details.get("body"),
                resume_file=resume_path,
                access_token=access_token
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid email provider")
        
        return {"success": True, "data": result}
    except HTTPException:
        raise  # pass through our own 400s cleanly
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-apply")
async def auto_apply(request: AutoApplyRequest, current_user: User = Depends(get_current_user)):
    """Automatic job application workflow."""
    try:
        logger.info(f"Auto-apply for user {current_user.id}")

        # Step 1: Analyze job description
        analysis_result = analyze_jd(request.job_description)
        job_details = {
            "company":    analysis_result.company,
            "role":       analysis_result.role,
            "skills":     analysis_result.skills,
            "experience": analysis_result.experience,
            "email":      analysis_result.email,
            "location":   analysis_result.location,
            "keywords":   analysis_result.keywords,
        }

        # Step 2: Find best resume from user-specific upload directory
        user_resumes_dir = Path(__file__).parent.parent / "data" / "resumes" / str(current_user.id)
        user_resumes_dir.mkdir(parents=True, exist_ok=True)

        pdf_files = list(user_resumes_dir.glob("*.pdf"))
        if not pdf_files:
            raise HTTPException(
                status_code=400,
                detail="No resumes uploaded yet. Please upload at least one resume PDF first."
            )

        best_resume = find_best_resume(job_details, resumes_dir=str(user_resumes_dir))
        # Step 3: Generate personalised email — generators expect the JobDetails object
        user_profile = {"name": current_user.name, "email": current_user.email}
        email_content = generate_email(analysis_result, best_resume.get("resume_content", ""))
        
        # Generate subject using the suggested subject from JD if available
        subject = generate_subject(
            candidate_name=current_user.name,
            company=analysis_result.company,
            role=analysis_result.role,
            candidate_strengths=analysis_result.skills[:5] if analysis_result.skills else [],
            suggested_subject=analysis_result.suggested_subject,
            jd_text=request.job_description
        )

        sent = False
        if request.auto_send:
            # Step 4: Send email via connected provider
            if current_user.google_connected:
                provider = "gmail"
            elif current_user.outlook_connected:
                provider = "outlook"
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No email provider connected. Connect Gmail or Outlook first."
                )

            token_data = get_oauth_token(current_user.id, provider)
            if not token_data:
                logger.error(f"{provider.capitalize()} token not available for user {current_user.id}")
                raise HTTPException(status_code=400, detail=f"{provider.capitalize()} token not available")

            if provider == "gmail":
                # Construct full path to resume file
                resume_filename = best_resume.get("filename")
                resume_path = None
                if resume_filename:
                    resume_path = str(Path(__file__).parent.parent / "data" / "resumes" / str(current_user.id) / resume_filename)
                
                send_gmail(
                    to_email=job_details.get("email"),
                    subject=subject,
                    body=email_content,
                    resume_file=resume_path,
                    access_token=token_data.get("access_token"),
                )
            else:
                # Construct full path to resume file
                resume_filename = best_resume.get("filename")
                resume_path = None
                if resume_filename:
                    resume_path = str(Path(__file__).parent.parent / "data" / "resumes" / str(current_user.id) / resume_filename)
                
                send_outlook(
                    to_email=job_details.get("email"),
                    subject=subject,
                    body=email_content,
                    resume_file=resume_path,
                    access_token=token_data.get("access_token"),
                )
            sent = True

        # Save application record to DB
        try:
            import sqlite3
            db_path = Path(__file__).parent.parent / "data" / "users.db"
            conn = sqlite3.connect(db_path)
            conn.execute(
                """INSERT INTO job_applications
                   (user_id, company, role, resume_file, match_score, status, email_sent,
                    email_subject, email_body, recipient_email)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    current_user.id,
                    job_details.get("company"),
                    job_details.get("role"),
                    best_resume.get("filename"),
                    best_resume.get("score", 0),
                    "sent" if sent else "draft",
                    sent,
                    subject,
                    email_content,
                    job_details.get("email"),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as db_err:
            logger.warning(f"Could not save application record: {db_err}")

        return {
            "success": True,
            "data": {
                "job_analysis": job_details,
                "matched_resume": {
                    "filename": best_resume.get("filename"),
                    "score":    best_resume.get("score"),
                },
                "email": {
                    "subject": subject,
                    "body":    email_content,
                },
                "sent": sent,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto-apply: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics."""
    try:
        import sqlite3
        from pathlib import Path
        
        db_path = Path(__file__).parent.parent / "data" / "users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get application statistics
        cursor.execute(
            "SELECT COUNT(*) FROM job_applications WHERE user_id = ?",
            (current_user.id,)
        )
        total_applications = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT COUNT(*) FROM job_applications WHERE user_id = ? AND email_sent = TRUE",
            (current_user.id,)
        )
        sent_applications = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT COUNT(*) FROM resumes WHERE user_id = ?",
            (current_user.id,)
        )
        total_resumes = cursor.fetchone()[0]
        
        # Get recent applications
        cursor.execute(
            """SELECT company, role, status, created_at 
               FROM job_applications 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT 5""",
            (current_user.id,)
        )
        recent_applications = [
            {
                "company": row[0],
                "role": row[1],
                "status": row[2],
                "created_at": row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "success": True,
            "data": {
                "user": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "name": current_user.name,
                    "google_connected": current_user.google_connected,
                    "outlook_connected": current_user.outlook_connected
                },
                "statistics": {
                    "total_applications": total_applications,
                    "sent_applications": sent_applications,
                    "total_resumes": total_resumes
                },
                "recent_applications": recent_applications
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applications")
async def get_applications(current_user: User = Depends(get_current_user)):
    """Get full application history for the current user — all records, all fields."""
    try:
        import sqlite3
        db_path = Path(__file__).parent.parent / "data" / "users.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, company, role, resume_file, match_score,
                      status, email_sent, email_subject, email_body,
                      recipient_email, created_at
               FROM job_applications
               WHERE user_id = ?
               ORDER BY created_at DESC""",
            (current_user.id,),
        )
        rows = cursor.fetchall()
        conn.close()
        applications = [
            {
                "id":              row[0],
                "company":         row[1],
                "role":            row[2],
                "resume_file":     row[3],
                "match_score":     row[4],
                "status":          row[5],
                "email_sent":      bool(row[6]),
                "email_subject":   row[7],
                "email_body":      row[8],
                "recipient_email": row[9],
                "created_at":      row[10],
            }
            for row in rows
        ]
        return {"success": True, "data": applications}
    except Exception as e:
        logger.error(f"Error fetching applications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── In-memory JD PDF store per user session  {user_id: Path} ──────────────
_user_jd_paths: dict = {}


class ChatRequest(BaseModel):
    message: str
    history: list = []  # [{"role": "user"/"assistant", "content": "..."}]


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """RAG chatbot: answer questions about resumes, JD, history, and the portal."""
    try:
        from agents.chatbot import chat

        resumes_dir = Path(__file__).parent.parent / "data" / "resumes" / str(current_user.id)
        resumes_dir.mkdir(parents=True, exist_ok=True)

        jd_pdf_path = _user_jd_paths.get(current_user.id)

        reply = chat(
            user_id=current_user.id,
            question=request.message,
            history=request.history,
            resumes_dir=resumes_dir,
            jd_pdf_path=jd_pdf_path,
        )
        return {"success": True, "data": {"reply": reply}}
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/upload-jd")
async def upload_jd_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a JD PDF so the chatbot can compare it against the user's resumes."""
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        # Save to a temp directory scoped to the user
        jd_dir = Path(__file__).parent.parent / "data" / "jd_uploads" / str(current_user.id)
        jd_dir.mkdir(parents=True, exist_ok=True)
        jd_path = jd_dir / "uploaded_jd.pdf"

        with open(jd_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Cache the path and invalidate the existing vector store so it rebuilds with the JD
        _user_jd_paths[current_user.id] = jd_path
        from agents.chatbot import invalidate_cache
        invalidate_cache(current_user.id)

        logger.info(f"JD PDF uploaded for user {current_user.id}: {file.filename}")
        return {"success": True, "data": {"filename": file.filename, "message": "JD uploaded. The chatbot will now use it for comparisons."}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JD upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/upload-jd")
async def remove_jd_pdf(current_user: User = Depends(get_current_user)):
    """Remove the uploaded JD PDF from the chatbot context."""
    _user_jd_paths.pop(current_user.id, None)
    from agents.chatbot import invalidate_cache
    invalidate_cache(current_user.id)
    return {"success": True, "data": {"message": "JD removed from context."}}


@app.get("/api/user-profile")
async def get_user_profile():
    """Get user profile configuration."""
    try:
        from utils.config_loader import load_user_profile
        profile = load_user_profile()
        return {"success": True, "data": profile}
    except Exception as e:
        logger.error(f"Error loading user profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Catch-all route to serve React frontend for SPA routing
@app.get("/{full_path:path}")
async def serve_frontend_spa(full_path: str):
    """Serve React frontend for all non-API routes (SPA routing)."""
    # Don't intercept API routes - let them return 404 normally
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    # Serve index.html for all frontend routes
    frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_path.exists():
        return FileResponse(str(frontend_path / "index.html"))
    else:
        raise HTTPException(status_code=404, detail="Frontend not built")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
