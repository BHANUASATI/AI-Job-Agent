# AI Job Agent - Complete Workflow Diagram

## Project Overview

AI Job Agent is an automated job application system that uses AI to analyze job descriptions, match resumes, generate personalized application emails, and send them via Gmail or Outlook. The system consists of a React frontend, FastAPI backend, and multiple AI-powered agents.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI JOB AGENT SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐         ┌──────────────────┐         ┌──────────────┐ │
│  │   React Frontend │◄────────┤  FastAPI Backend │◄────────┤   AI Agents  │ │
│  │   (Vite + React) │         │   (Python)       │         │  (LangChain) │ │
│  └──────────────────┘         └──────────────────┘         └──────────────┘ │
│           │                           │                           │          │
│           │                           │                           │          │
│  ┌────────▼────────┐         ┌────────▼────────┐         ┌────────▼─────┐ │
│  │  Authentication │         │   Database      │         │  External    │ │
│  │  (JWT + OAuth)  │         │   (SQLite)      │         │  APIs        │ │
│  └─────────────────┘         └─────────────────┘         └──────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow - Step by Step

### Phase 1: User Authentication & Setup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 1: AUTHENTICATION                               │
└─────────────────────────────────────────────────────────────────────────────┘

User Action: Access Application
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Frontend: React App loads (App.jsx)                                        │
│  - Checks for existing JWT token in localStorage                            │
│  - If token exists: validates via /api/auth/me                              │
│  - If no token: redirects to /login                                          │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ├─── Token Exists ──► /api/auth/me ──► Dashboard
         │
         └─── No Token ──► Login Page
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Login Options:     │
                    │  1. Email/Password  │
                    │  2. Google OAuth    │
                    │  3. Outlook OAuth   │
                    └─────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Email/Password   │  │  Google OAuth    │  │  Outlook OAuth   │
│ Login            │  │  Flow            │  │  Flow            │
└──────────────────┘  └──────────────────┘  └──────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ POST /api/auth/  │  │ GET /api/auth/   │  │ GET /api/auth/   │
│ login            │  │ google           │  │ outlook          │
└──────────────────┘  └──────────────────┘  └──────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ backend/auth.py  │  │ Redirect to      │  │ Redirect to      │
│ - authenticate_  │  │ Google OAuth     │  │ Microsoft OAuth  │
│   user()         │  │ consent page     │  │ consent page     │
│ - create_access_ │  └──────────────────┘  └──────────────────┘
│   token()        │           │                    │
└──────────────────┘           │                    │
         │                    ▼                    ▼
         ▼          ┌──────────────────┐  ┌──────────────────┐
┌──────────────────┐│ GET /api/auth/   │  │ GET /api/auth/   │
│ Return JWT +     ││ google/callback  │  │ outlook/callback │
│ User object      │└──────────────────┘  └──────────────────┘
└──────────────────┘           │                    │
         │                    ▼                    ▼
         ▼          ┌──────────────────┐  ┌──────────────────┐
┌──────────────────┐│ Exchange code    │  │ Exchange code    │
│ Store JWT in     ││ for tokens       │  │ for tokens       │
│ localStorage     │└──────────────────┘  └──────────────────┘
└──────────────────┘           │                    │
         │                    ▼                    ▼
         ▼          ┌──────────────────┐  ┌──────────────────┐
┌──────────────────┐│ Fetch user info  │  │ Fetch user info  │
│ Redirect to      ││ from Google      │  │ from Microsoft   │
│ Dashboard        │└──────────────────┘  └──────────────────┘
└──────────────────┘           │                    │
                              └──────────┬─────────┘
                                         ▼
                              ┌──────────────────┐
                              │ get_or_create_   │
                              │ oauth_user()    │
                              │ - Create user if │
                              │   new            │
                              │ - Update OAuth   │
                              │   token if exists│
                              │ - Return JWT     │
                              └──────────────────┘
                                         │
                                         ▼
                              ┌──────────────────┐
                              │ Redirect to      │
                              │ /auth/callback?  │
                              │ token=<JWT>      │
                              └──────────────────┘
                                         │
                                         ▼
                              ┌──────────────────┐
                              │ OAuthCallback    │
                              │ - Store JWT      │
                              │ - Refresh user   │
                              │ - Redirect to    │
                              │   Dashboard      │
                              └──────────────────┘
```

---

### Phase 2: Dashboard & Resume Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: DASHBOARD & RESUMES                               │
└─────────────────────────────────────────────────────────────────────────────┘

User Action: Access Dashboard
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Frontend: Dashboard.jsx loads                                               │
│  - Fetches user data via /api/auth/me                                        │
│  - Fetches dashboard stats via /api/dashboard                                 │
│  - Displays tabs: Overview, Resumes, Auto Apply, Email, History              │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  GET /api/dashboard                                                           │
│  - Fetches total applications count                                           │
│  - Fetches sent applications count                                           │
│  - Fetches total resumes count                                                │
│  - Fetches recent applications (last 5)                                      │
│  - Returns user OAuth connection status (Google/Outlook)                     │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Database Query (SQLite)                                                      │
│  - SELECT COUNT(*) FROM job_applications WHERE user_id = ?                   │
│  - SELECT COUNT(*) FROM job_applications WHERE user_id = ? AND email_sent=1  │
│  - SELECT COUNT(*) FROM resumes WHERE user_id = ?                            │
│  - SELECT company, role, status, created_at FROM job_applications            │
│    WHERE user_id = ? ORDER BY created_at DESC LIMIT 5                         │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Display Dashboard Statistics                                                 │
│  - Total applications card                                                    │
│  - Sent applications card                                                    │
│  - Total resumes card                                                        │
│  - Recent applications table                                                  │
│  - OAuth connection status indicators                                         │
└─────────────────────────────────────────────────────────────────────────────┘

User Action: Upload Resume
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Frontend: Resume Upload (Resumes Tab)                                        │
│  - Drag & drop or file selection                                             │
│  - Validates PDF format                                                      │
│  - Calls POST /api/upload-resume                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  POST /api/upload-resume                                                      │
│  - Validates user JWT token                                                   │
│  - Creates user-specific directory: data/resumes/{user_id}/                   │
│  - Saves uploaded PDF file                                                   │
│  - Inserts record into SQLite resumes table                                  │
│  - Returns filename, size, and success message                              │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Database Operation                                                           │
│  INSERT INTO resumes (user_id, filename, file_path) VALUES (?, ?, ?)       │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Update Frontend: Resume List                                                 │
│  - Calls GET /api/resumes                                                     │
│  - Displays uploaded resumes with delete option                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 3: Job Application Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  PHASE 3: JOB APPLICATION WORKFLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

User Action: Start Job Application (Auto Apply Tab)
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Frontend: Auto Apply Form                                                    │
│  - Input: Job description text OR upload JD file (PDF/DOCX/TXT)               │
│  - Toggle: Auto-send email (default: false)                                  │
│  - Button: "Analyze & Apply"                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ├─── Text Input ──┐
         │                 │
         └─── File Upload ──┤
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│ POST /api/       │              │ POST /api/       │
│ analyze-job      │              │ upload-jd        │
└──────────────────┘              └──────────────────┘
         │                                   │
         ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│ agents/jd_       │              │ services/jd_     │
│ analyzer.py      │              │ parser.py        │
│ - analyze_jd()   │              │ - parse_jd_file()│
└──────────────────┘              └──────────────────┘
         │                                   │
         ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│ LLM Service      │              │ File Parser      │
│ (OpenRouter)     │              │ - PDF extraction │
│ - Extracts:      │              │ - DOCX extraction│
│   - Company      │              │ - TXT extraction │
│   - Role         │              └──────────────────┘
│   - Skills       │                       │
│   - Experience   │                       ▼
│   - Email        │              ┌──────────────────┐
│   - Location     │              │ Return extracted │
│   - Keywords     │              │ text to frontend │
│   - Suggested    │              └──────────────────┘
│     Subject      │                       │
└──────────────────┘                       │
         │                                 │
         └─────────────┬───────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Frontend displays│
              │ JD analysis      │
              │ results          │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ User reviews     │
              │ and confirms     │
              │ application      │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ POST /api/       │
              │ auto-apply       │
              └──────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKEND: Auto-Apply Workflow (backend/main.py)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ STEP 1: Analyze  │
              │ Job Description  │
              │ - analyze_jd()   │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ STEP 2: Find     │
              │ Best Resume      │
              │ - find_best_     │
              │   resume()       │
              └──────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RESUME MATCHING PROCESS (agents/resume_retriever.py)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Load all PDFs    │
              │ from user's      │
              │ resume directory │
              │ data/resumes/    │
              │ {user_id}/       │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Extract text     │
              │ from PDFs using  │
              │ PyPDFLoader      │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Split documents  │
              │ into chunks     │
              │ (resume_splitter │
              │  .py)           │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Create vector    │
              │ store from       │
              │ chunks           │
              │ (vector_store.py)│
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Vector similarity│
              │ search with      │
              │ query:           │
              │ "Role + Skills + │
              │  Keywords"       │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Score resumes:   │
              │ - Base score:    │
              │   40%            │
              │ - Skill match:   │
              │   30%            │
              │ - Keywords: 15%  │
              │ - Role match:    │
              │   10%            │
              │ - Experience: 5% │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Return best     │
              │ resume with:    │
              │ - filename      │
              │ - match score   │
              │ - resume content│
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ STEP 3: Generate │
              │ Email & Subject  │
              └──────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ agents/email_    │        │ agents/subject_  │
│ generator.py     │        │ generator.py     │
│ - generate_      │        │ - generate_      │
│   email()        │        │   subject()      │
└──────────────────┘        └──────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ LLM Service     │        │ Priority:         │
│ - Personalized  │        │ 1. JD-suggested  │
│   email body     │        │    subject       │
│ - 4 paragraphs  │        │ 2. LLM-generated │
│ - Professional  │        │    subject       │
│   tone          │        │ 3. Fallback      │
└──────────────────┘        └──────────────────┘
         │                           │
         └─────────────┬─────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ STEP 4: Send     │
              │ Email (if auto-  │
              │ send enabled)    │
              └──────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ services/gmail_  │        │ services/        │
│ service.py       │        │ outlook_service  │
│ - send_email()   │        │ .py              │
│ - Uses OAuth     │        │ - send_email()   │
│   token from DB  │        │ - Uses OAuth     │
└──────────────────┘        │   token from DB  │
                            └──────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ Gmail API        │        │ Microsoft Graph  │
│ - Attach resume  │        │ API              │
│ - Send email     │        │ - Attach resume  │
└──────────────────┘        │ - Send email     │
                            └──────────────────┘
         │                           │
         └─────────────┬─────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ STEP 5: Save     │
              │ to Database      │
              └──────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Database Operation (SQLite)                                                  │
│  INSERT INTO job_applications                                                │
│  (user_id, company, role, resume_file, match_score, status,                  │
│   email_sent, email_subject, email_body, recipient_email)                    │
│  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Return results to │
              │ frontend:        │
              │ - Job analysis   │
              │ - Matched resume │
              │ - Email subject  │
              │ - Email body     │
              │ - Sent status    │
              └──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Frontend displays│
              │ application      │
              │ results          │
              └──────────────────┘
```

---

### Phase 4: Email Draft & Manual Send

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PHASE 4: EMAIL DRAFT & MANUAL SEND                               │
└─────────────────────────────────────────────────────────────────────────────┘

User Action: Review Draft Email (Email Tab)
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Frontend: Email Draft Editor                                                  │
│  - Displays generated subject line                                           │
│  - Displays generated email body                                              │
│  - Allows editing of both subject and body                                   │
│  - Select email provider: Gmail or Outlook                                   │
│  - Button: "Send Email"                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  POST /api/send-email                                                          │
│  - Validates user JWT token                                                   │
│  - Checks OAuth token for selected provider                                   │
│  - Calls appropriate email service                                            │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ├─── Gmail ──► services/gmail_service.py
         │
         └─── Outlook ──► services/outlook_service.py
                           │
                           ▼
                  ┌──────────────────┐
                  │ Get OAuth token  │
                  │ from database    │
                  │ (get_oauth_token)│
                  └──────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Refresh token if │
                  │ expired (Google) │
                  └──────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Send email via   │
                  │ provider API     │
                  │ with resume      │
                  │ attachment       │
                  └──────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Update database  │
                  │ status to "sent" │
                  └──────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Return success   │
                  │ response         │
                  └──────────────────┘
```

---

### Phase 5: Application History & Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PHASE 5: APPLICATION HISTORY                                     │
└─────────────────────────────────────────────────────────────────────────────┘

User Action: View Application History (History Tab)
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Frontend: Application History Table                                         │
│  - Fetches all applications from database                                     │
│  - Displays: Company, Role, Status, Match Score, Date                        │
│  - Status badges: Sent, Draft, Failed, Pending                               │
│  - Actions: View details, Delete                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  GET /api/dashboard (includes recent applications)                           │
│  - Queries job_applications table                                             │
│  - Returns paginated results                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Database Query                                                               │
│  SELECT company, role, status, created_at, match_score, email_sent           │
│  FROM job_applications                                                       │
│  WHERE user_id = ?                                                            │
│  ORDER BY created_at DESC                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Display Applications with Status Pills                                       │
│  - Sent: Green checkmark                                                     │
│  - Draft: Gray document icon                                                 │
│  - Failed: Red X icon                                                        │
│  - Pending: Yellow clock icon                                                │
└─────────────────────────────────────────────────────────────────────────────┘

User Action: Delete Application
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  DELETE /api/applications/{id}                                                │
│  - Validates user JWT token                                                   │
│  - Deletes application from database                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Frontend Components

```
src/
├── App.jsx                    # Main app with routing
├── authContext.jsx           # Authentication context & API client
├── main.jsx                   # React entry point
├── index.css                  # Global styles
├── App.css                    # App-specific styles
├── components/
│   └── Toast.jsx             # Toast notification component
└── pages/
    ├── Login.jsx             # Login page
    ├── Signup.jsx            # Signup page
    ├── Dashboard.jsx         # Main dashboard (1318 lines)
    ├── Dashboard.css         # Dashboard styles
    └── OAuthCallback.jsx     # OAuth callback handler
```

### Backend Components

```
backend/
├── main.py                   # FastAPI application (1007 lines)
│   ├── Authentication endpoints
│   ├── Job analysis endpoints
│   ├── Resume management endpoints
│   ├── Email generation endpoints
│   ├── Auto-apply workflow
│   └── Dashboard endpoints
└── auth.py                   # Authentication module (615 lines)
    ├── JWT token management
    ├── OAuth flows (Google/Outlook)
    ├── User CRUD operations
    └── Database initialization
```

### AI Agents

```
agents/
├── jd_analyzer.py            # Job description analysis (294 lines)
├── resume_retriever.py       # Vector-based resume matching (210 lines)
├── email_generator.py        # Email generation (385 lines)
├── subject_generator.py      # Subject line generation (218 lines)
├── resume_splitter.py        # Document chunking
├── vector_store.py           # Vector embeddings
├── resume_selector.py        # Resume selection logic
├── jd_resume_comparator.py   # JD vs resume comparison
├── resume_enhancer.py        # Resume enhancement
├── resume_ranker.py          # Resume ranking
├── resume_loader.py          # Resume loading
├── chatbot.py                # Chatbot functionality
├── link_scraper.py           # Link scraping
└── post_parser.py            # Post parsing
```

### Services

```
services/
├── llm_service.py            # LLM integration with fallback (74 lines)
├── gmail_service.py          # Gmail API integration (139 lines)
├── outlook_service.py        # Outlook API integration
├── jd_parser.py              # JD file parsing (330 lines)
├── database_service.py       # Database operations (232 lines)
├── pdf_generator.py          # PDF generation
├── latex_resume_service.py   # LaTeX resume generation
├── captcha_solver.py         # CAPTCHA solving
└── ai_resume_editor.py       # AI resume editing
```

### Configuration & Utilities

```
config/
└── settings.py               # Configuration management (170 lines)

utils/
├── logger.py                 # Logging configuration
├── exceptions.py             # Custom exceptions
├── validators.py             # Input validation
├── config_loader.py          # Config loading
└── port_utils.py             # Port utilities
```

---

## Data Flow Diagrams

### Authentication Flow

```
┌──────────┐
│   User    │
└─────┬────┘
      │
      │ 1. Login request
      ▼
┌──────────────────┐
│  React Frontend  │
│  (authContext)   │
└─────┬────────────┘
      │
      │ 2. POST /api/auth/login
      ▼
┌──────────────────┐
│  FastAPI Backend │
│  (auth.py)       │
└─────┬────────────┘
      │
      │ 3. authenticate_user()
      ▼
┌──────────────────┐
│  SQLite Database │
│  (users table)   │
└─────┬────────────┘
      │
      │ 4. User data
      ▼
┌──────────────────┐
│  FastAPI Backend │
│  (auth.py)       │
└─────┬────────────┘
      │
      │ 5. create_access_token()
      ▼
┌──────────────────┐
│  JWT Token       │
│  Generation      │
└─────┬────────────┘
      │
      │ 6. JWT + User object
      ▼
┌──────────────────┐
│  React Frontend  │
│  (authContext)   │
└─────┬────────────┘
      │
      │ 7. Store JWT in localStorage
      ▼
┌──────────────────┐
│  Browser Storage │
└──────────────────┘
```

### Job Analysis Flow

```
┌──────────┐
│   User    │
└─────┬────┘
      │
      │ 1. Submit job description
      ▼
┌──────────────────┐
│  React Frontend  │
│  (Dashboard)    │
└─────┬────────────┘
      │
      │ 2. POST /api/analyze-job
      ▼
┌──────────────────┐
│  FastAPI Backend │
│  (main.py)       │
└─────┬────────────┘
      │
      │ 3. analyze_jd()
      ▼
┌──────────────────┐
│  JD Analyzer     │
│  Agent           │
└─────┬────────────┘
      │
      │ 4. LLM request
      ▼
┌──────────────────┐
│  LLM Service     │
│  (OpenRouter)    │
└─────┬────────────┘
      │
      │ 5. Structured JD data
      ▼
┌──────────────────┐
│  FastAPI Backend │
└─────┬────────────┘
      │
      │ 6. JSON response
      ▼
┌──────────────────┐
│  React Frontend  │
└──────────────────┘
```

### Resume Matching Flow

```
┌──────────────────┐
│  Job Details     │
│  (from JD)       │
└─────┬────────────┘
      │
      │ 1. find_best_resume()
      ▼
┌──────────────────┐
│  Resume Retriever│
│  Agent           │
└─────┬────────────┘
      │
      │ 2. Load PDFs from data/resumes/{user_id}/
      ▼
┌──────────────────┐
│  PyPDFLoader     │
│  (LangChain)     │
└─────┬────────────┘
      │
      │ 3. Document text
      ▼
┌──────────────────┐
│  Resume Splitter │
└─────┬────────────┘
      │
      │ 4. Document chunks
      ▼
┌──────────────────┐
│  Vector Store    │
│  (Embeddings)    │
└─────┬────────────┘
      │
      │ 5. Vector store
      ▼
┌──────────────────┐
│  Similarity      │
│  Search          │
└─────┬────────────┘
      │
      │ 6. Matched chunks
      ▼
┌──────────────────┐
│  Scoring Engine  │
│  - Skills: 30%   │
│  - Keywords: 15% │
│  - Role: 10%     │
│  - Exp: 5%       │
└─────┬────────────┘
      │
      │ 7. Best resume + score
      ▼
┌──────────────────┐
│  Return Result   │
└──────────────────┘
```

### Email Generation Flow

```
┌──────────────────┐      ┌──────────────────┐
│  Job Details     │      │  Resume Content  │
└─────┬────────────┘      └─────┬────────────┘
      │                          │
      └──────────┬───────────────┘
                 │
                 │ 1. generate_email()
                 ▼
        ┌──────────────────┐
        │  Email Generator │
        │  Agent           │
        └─────┬────────────┘
               │
               │ 2. Extract relevant skills
               ▼
┌──────────────────┐
│  Skill Matching  │
└─────┬────────────┘
      │
      │ 3. Matched skills
      ▼
        ┌──────────────────┐
        │  Email Generator │
        │  Agent           │
        └─────┬────────────┘
               │
               │ 4. LLM request
               ▼
┌──────────────────┐
│  LLM Service     │
│  (OpenRouter)    │
└─────┬────────────┘
      │
      │ 5. Generated email
      ▼
        ┌──────────────────┐
        │  Email Generator │
        │  Agent           │
        └─────┬────────────┘
               │
               │ 6. Add signature
               ▼
┌──────────────────┐
│  Final Email     │
└──────────────────┘
```

---

## API Endpoints Reference

### Authentication Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | `/api/auth/config` | Get OAuth config | - | `{google_oauth_enabled, outlook_oauth_enabled}` |
| POST | `/api/auth/signup` | Register new user | `{email, password, name}` | `User` object |
| POST | `/api/auth/login` | Login user | `{email, password}` | `{access_token, token_type, user}` |
| GET | `/api/auth/me` | Get current user | - | `User` object |
| GET | `/api/auth/google` | Get Google OAuth URL | - | `{auth_url}` |
| GET | `/api/auth/google/callback` | Google OAuth callback | `code, state, error` | Redirect with JWT |
| GET | `/api/auth/outlook` | Get Outlook OAuth URL | - | `{auth_url}` |
| GET | `/api/auth/outlook/callback` | Outlook OAuth callback | `code, state, error` | Redirect with JWT |
| POST | `/api/auth/connect/{provider}` | Connect OAuth provider | `code` | Success message |

### Job Analysis Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| POST | `/api/analyze-job` | Analyze job description | `{job_description, job_url?}` | `{company, role, skills, experience, email, location, keywords}` |
| POST | `/api/upload-jd` | Upload JD file | `multipart/form-data` | `{filename, size, extracted_text, message}` |

### Resume Management Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| POST | `/api/upload-resume` | Upload resume PDF | `multipart/form-data` | `{filename, size, message}` |
| GET | `/api/resumes` | List user resumes | - | `[{filename, size, uploaded}]` |
| DELETE | `/api/resumes/{filename}` | Delete resume | - | `{success, message}` |

### Email & Application Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| POST | `/api/match-resume` | Find best matching resume | `{job_details}` | `{resume_file, match_score, resume_content}` |
| POST | `/api/generate-email` | Generate application email | `{job_details, resume_content, user_profile, email_provider}` | `{subject, body}` |
| POST | `/api/send-email` | Send application email | `{job_details, resume_content, user_profile, email_provider}` | Success result |
| POST | `/api/auto-apply` | Complete auto-apply workflow | `{job_description, job_url?, auto_send}` | Complete application data |

### Dashboard Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | `/api/dashboard` | Get dashboard statistics | - | `{user, statistics, recent_applications}` |
| GET | `/api/health` | Health check | - | `{status, version}` |

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
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
```

### Job Applications Table
```sql
CREATE TABLE job_applications (
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
```

### Resumes Table
```sql
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

---

## External Integrations

### LLM Integration (OpenRouter)
- **Primary Model**: `nvidia/nemotron-3-ultra-550b-a55b:free`
- **Fallback Models**: 
  - `meta-llama/llama-3.3-70b-instruct:free`
  - `nvidia/nemotron-3-super-120b-a12b:free`
  - `openrouter/free`
- **Service**: `services/llm_service.py`
- **Features**: Automatic fallback, retry logic, timeout handling

### Gmail Integration
- **API**: Gmail API
- **Scopes**: `https://www.googleapis.com/auth/gmail.send`
- **Service**: `services/gmail_service.py`
- **Features**: OAuth 2.0, token refresh, PDF attachments

### Outlook Integration
- **API**: Microsoft Graph API
- **Scopes**: `https://graph.microsoft.com/Mail.Send`, `https://graph.microsoft.com/User.Read`
- **Service**: `services/outlook_service.py`
- **Features**: OAuth 2.0, MSAL library, PDF attachments

### Vector Embeddings
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Framework**: LangChain
- **Storage**: In-memory vector store (Chroma)
- **Service**: `agents/vector_store.py`

---

## Security Features

### Authentication & Authorization
- JWT token-based authentication
- OAuth 2.0 for Google and Outlook
- Token expiration handling
- Automatic token refresh (Google)
- Protected routes with JWT verification

### Input Validation
- File type validation (PDF, DOCX, TXT)
- File size limits (10MB)
- Filename sanitization
- MIME type verification
- Path traversal prevention

### Data Security
- User-specific data isolation
- OAuth tokens stored securely in database
- Password hashing with bcrypt
- SQL injection prevention (parameterized queries)
- XSS prevention in frontend

---

## Error Handling

### Frontend Error Handling
- Error boundary component
- Toast notifications for user feedback
- Axios interceptors for 401 handling
- Automatic token refresh on expiry

### Backend Error Handling
- Custom exception classes
- Comprehensive logging
- Graceful degradation (LLM fallbacks)
- Validation error responses
- HTTP status codes for different error types

---

## Configuration Management

### Environment Variables
- `LLM_API_KEY`: OpenRouter API key
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `OUTLOOK_CLIENT_ID`: Microsoft OAuth client ID
- `OUTLOOK_CLIENT_SECRET`: Microsoft OAuth client secret
- `JWT_SECRET_KEY`: JWT signing key
- `FRONTEND_URL`: Frontend base URL

### Configuration Files
- `.env`: Environment variables
- `config/user_profile.json`: User profile data
- `credentials.json`: Google OAuth credentials
- `token.json`: Gmail OAuth token (legacy)

---

## Deployment Architecture

### Development
```
Frontend: Vite dev server (localhost:5173)
Backend: FastAPI with reload (localhost:8000)
Database: SQLite file (data/users.db)
```

### Production
```
Frontend: Built static files (nginx/Apache)
Backend: FastAPI (gunicorn/uvicorn)
Database: SQLite or PostgreSQL
```

---

## Monitoring & Logging

### Logging Levels
- DEBUG: Detailed debugging information
- INFO: General operational information
- WARNING: Warning messages
- ERROR: Error messages with stack traces

### Log Files
- Location: `logs/app.log`
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Rotation: Manual (configurable)

---

## Performance Optimizations

### Frontend
- Code splitting with React Router
- Lazy loading of components
- Axios request interceptors
- LocalStorage for JWT caching

### Backend
- Vector similarity search for resume matching
- LLM fallback mechanism
- Database connection pooling
- Async/await for I/O operations

### AI Processing
- Document chunking for efficient vector search
- Skill-based scoring algorithm
- Cached vector stores
- Batch processing for multiple resumes

---

## Future Enhancements

### Planned Features
- Real-time email tracking
- Resume versioning
- Bulk job application
- Interview scheduling
- Analytics dashboard
- Multi-language support
- Mobile app

### Technical Improvements
- PostgreSQL migration
- Redis caching
- Celery for background tasks
- Docker containerization
- CI/CD pipeline
- Automated testing

---

## Summary

The AI Job Agent system is a comprehensive job application automation platform that:

1. **Authenticates users** via JWT and OAuth (Google/Outlook)
2. **Analyzes job descriptions** using AI to extract key information
3. **Matches resumes** using vector similarity search and skill-based scoring
4. **Generates personalized emails** with professional tone and relevant content
5. **Sends emails** via Gmail or Outlook APIs with resume attachments
6. **Tracks applications** in a SQLite database with status updates
7. **Provides a dashboard** for managing resumes, applications, and settings

The system uses modern technologies:
- **Frontend**: React 19, Vite, React Router, Axios
- **Backend**: FastAPI, SQLite, OAuth 2.0
- **AI**: LangChain, OpenRouter, Sentence Transformers
- **Email**: Gmail API, Microsoft Graph API

All components are integrated through a well-defined API layer with proper authentication, validation, and error handling.
