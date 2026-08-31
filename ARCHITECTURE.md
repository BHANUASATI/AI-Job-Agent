# AI Job Agent - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Architecture](#component-architecture)
4. [Data Architecture](#data-architecture)
5. [Security Architecture](#security-architecture)
6. [Deployment Architecture](#deployment-architecture)
7. [Technology Stack](#technology-stack)
8. [API Design](#api-design)
9. [Database Schema](#database-schema)
10. [Monitoring & Logging](#monitoring--logging)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI JOB AGENT SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        PRESENTATION LAYER                             │  │
│  │  ┌──────────────────┐              ┌──────────────────┐              │  │
│  │  │   React SPA      │              │  Streamlit UI    │              │  │
│  │  │   (Vite + React) │              │  (Legacy)        │              │  │
│  │  └──────────────────┘              └──────────────────┘              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         API GATEWAY LAYER                             │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │              FastAPI Backend (uvicorn)                       │   │  │
│  │  │  - CORS Middleware                                           │   │  │
│  │  │  - Authentication Middleware                                 │   │  │
│  │  │  - Request Validation                                        │   │  │
│  │  │  - Error Handling                                           │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        BUSINESS LOGIC LAYER                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │   Agents     │  │  Services    │  │  Utils       │              │  │
│  │  │  - JD Analysis│  │  - LLM       │  │  - Config    │              │  │
│  │  │  - Resume    │  │  - Email     │  │  - Logger    │              │  │
│  │  │    Matching  │  │  - Database  │  │  - Validators│              │  │
│  │  │  - Email     │  │  - OAuth     │  │  - Helpers   │              │  │
│  │  │    Generation│  │              │  │              │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         DATA ACCESS LAYER                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │   SQLite     │  │  Vector DB   │  │  File System│              │  │
│  │  │  Database    │  │  (FAISS/     │  │  Storage    │              │  │
│  │  │              │  │   Chroma)    │  │              │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      EXTERNAL SERVICES LAYER                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │   LLM APIs   │  │  Email APIs  │  │  Job Sites  │              │  │
│  │  │  - OpenRouter│  │  - Gmail     │  │  - Scrapers │              │  │
│  │  │  - Gemini    │  │  - Outlook   │  │              │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### System Components

1. **Presentation Layer**
   - React SPA (Modern web interface)
   - Streamlit UI (Legacy interface)
   - CLI Interface (Command-line tool)

2. **API Gateway Layer**
   - FastAPI backend
   - Authentication & authorization
   - Request validation & routing
   - CORS & security middleware

3. **Business Logic Layer**
   - AI Agents (Job analysis, resume matching, email generation)
   - Services (LLM, email, database, OAuth)
   - Utilities (Configuration, logging, validation)

4. **Data Access Layer**
   - SQLite database (User data, applications)
   - Vector database (Resume embeddings)
   - File system (Resume storage, logs)

5. **External Services Layer**
   - LLM APIs (OpenRouter, Gemini)
   - Email APIs (Gmail, Outlook)
   - Job sites (Web scrapers)

---

## Architecture Patterns

### 1. Layered Architecture

The system follows a classic layered architecture pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                             │
│  (React SPA, Streamlit UI, CLI)                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                              │
│  (FastAPI, Authentication, Routing, Validation)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                           │
│  (AI Agents, Services, Domain Logic)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Access Layer                              │
│  (SQLite, Vector DB, File System)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services Layer                         │
│  (LLM APIs, Email APIs, Web Scrapers)                            │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Agent-Based Architecture

The core business logic uses an agent-based pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Coordinator                            │
│  (Orchestrates agent execution and data flow)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  JD Analyzer  │    │ Resume Agent  │    │  Email Agent  │
│  Agent        │    │  (Match,      │    │  Generator    │
│               │    │   Enhance)    │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌───────────────┐
                    │  Shared State │
                    │  (Vector DB,  │
                    │   Database)  │
                    └───────────────┘
```

### 3. Service-Oriented Architecture

Services are loosely coupled and independently testable:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Service Registry                             │
│  (Discovers and manages service dependencies)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  LLM Service  │    │ Email Service │    │  Database     │
│  (OpenRouter, │    │  (Gmail,      │    │  Service      │
│   Gemini)     │    │   Outlook)    │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌───────────────┐
                    │  OAuth Service│
                    │  (Google,     │
                    │   Microsoft)  │
                    └───────────────┘
```

### 4. Repository Pattern

Data access abstracted through repository pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                            │
│  (Uses repository interfaces)                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Repository Interfaces                           │
│  (IUserRepository, IResumeRepository, etc.)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  SQLite       │    │  Vector DB    │    │  File System  │
│  Repository   │    │  Repository   │    │  Repository   │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## Component Architecture

### Frontend Components

```
frontend/src/
├── components/
│   ├── common/
│   │   ├── Button.jsx
│   │   ├── Input.jsx
│   │   ├── Card.jsx
│   │   └── Modal.jsx
│   ├── auth/
│   │   ├── LoginForm.jsx
│   │   ├── OAuthButton.jsx
│   │   └── ProtectedRoute.jsx
│   ├── dashboard/
│   │   ├── StatCard.jsx
│   │   ├── ApplicationTable.jsx
│   │   └── Chart.jsx
│   ├── resume/
│   │   ├── ResumeUpload.jsx
│   │   ├── ResumeList.jsx
│   │   └── ResumeCard.jsx
│   └── job/
│       ├── JDInput.jsx
│       ├── JDAnalysis.jsx
│       ├── ResumeMatch.jsx
│       └── EmailPreview.jsx
├── pages/
│   ├── Home.jsx
│   ├── Login.jsx
│   ├── Dashboard.jsx
│   ├── Resumes.jsx
│   ├── AutoApply.jsx
│   └── History.jsx
├── services/
│   ├── api.js
│   ├── authService.js
│   └── jobService.js
└── utils/
    ├── validators.js
    └── helpers.js
```

### Backend Components

```
backend/
├── main.py                    # FastAPI application & routes
├── auth.py                    # Authentication logic
└── middleware.py              # Custom middleware

agents/
├── jd_analyzer.py            # Job description analysis
├── resume_loader.py          # PDF resume loading
├── resume_splitter.py        # Document chunking
├── vector_store.py           # Vector database operations
├── resume_retriever.py       # Semantic search
├── resume_selector.py        # Best resume selection
├── email_generator.py        # Email generation
├── subject_generator.py      # Subject line generation
├── resume_enhancer.py        # AI resume enhancement
├── jd_resume_comparator.py   # JD vs resume comparison
├── chatbot.py                # AI chatbot
├── link_scraper.py           # Job link scraping
└── post_parser.py            # Job post parsing

services/
├── llm_service.py            # LLM API integration
├── gmail_service.py          # Gmail API integration
├── outlook_service.py        # Outlook API integration
├── database_service.py       # Database operations
├── jd_parser.py              # Job description parsing
├── latex_resume_service.py   # LaTeX resume generation
├── pdf_generator.py          # PDF generation
└── captcha_solver.py         # CAPTCHA solving

automation/
├── browser_manager.py        # Selenium browser management
├── overleaf/
│   ├── login.py             # Overleaf authentication
│   ├── editor.py            # Resume editing
│   ├── downloader.py        # PDF download
│   └── project_manager.py   # Project management
├── visual_logger.py         # Visual debugging
└── config.py                # Automation configuration

utils/
├── config_loader.py         # Configuration loading
├── logger.py                # Logging configuration
├── exceptions.py           # Custom exceptions
├── validators.py           # Input validation
├── port_utils.py           # Port management
└── helpers.py              # Helper functions
```

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPONENT INTERACTIONS                         │
└─────────────────────────────────────────────────────────────────┘

React Frontend          FastAPI Backend          AI Agents
      │                        │                       │
      │─── HTTP Request ──────▶│                       │
      │                        │─── Call Agent ────────▶│
      │                        │                       │
      │                        │◀─── Return Data ───────│
      │◀─── JSON Response ─────│                       │
      │                        │                       │
      │                        │                       │
      │─── Upload Resume ──────▶│                       │
      │                        │─── Store File ─────────▶│
      │                        │                       │
      │◀─── Confirmation ──────│                       │
      │                        │                       │
      │─── Job Description ────▶│                       │
      │                        │─── Analyze JD ─────────▶│
      │                        │                       │
      │                        │─── Match Resume ──────▶│
      │                        │                       │
      │                        │─── Generate Email ─────▶│
      │                        │                       │
      │◀─── Results ────────────│                       │
      │                        │                       │
      │─── Send Email ─────────▶│                       │
      │                        │─── Call Email API ─────▶│
      │                        │                       │
      │◀─── Status ─────────────│                       │
```

---

## Data Architecture

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### OAuth Tokens Table
```sql
CREATE TABLE oauth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,  -- 'google' or 'outlook'
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Resumes Table
```sql
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Job Applications Table
```sql
CREATE TABLE job_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    location TEXT,
    skills TEXT,  -- JSON array
    experience TEXT,
    recruiter_email TEXT,
    resume_used TEXT NOT NULL,
    match_score REAL,
    gap_score REAL,
    status TEXT DEFAULT 'draft',  -- draft, sent, failed
    email_provider TEXT,
    applied_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA FLOW ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────┘

User Input
    │
    ├─── Job Description
    │       │
    │       ├─── Text → JD Analyzer → Structured Data
    │       └─── File → JD Parser → Text → JD Analyzer
    │
    ├─── Resume Upload
    │       │
    │       └─── PDF → Validation → File Storage → Database Record
    │
    └─── Authentication
            │
            └─── Credentials → Auth Service → JWT Token

Processing Pipeline
    │
    ├─── JD Analysis
    │       │
    │       └─── LLM Service → Parsed JD Data
    │
    ├─── Resume Processing
    │       │
    │       ├─── Load PDFs → Text Extraction
    │       ├─── Chunk Documents → Text Chunks
    │       ├─── Generate Embeddings → Vector Data
    │       └─── Semantic Search → Match Results
    │
    ├─── Gap Analysis
    │       │
    │       └─── JD vs Resume → Gap Report
    │
    └─── Email Generation
            │
            ├─── Subject Generation → Subject Line
            └─── Email Generation → Email Body

Storage
    │
    ├─── SQLite Database
    │       │
    │       ├─── Users (auth data)
    │       ├─── OAuth Tokens (provider tokens)
    │       ├─── Resumes (file metadata)
    │       └─── Job Applications (application records)
    │
    ├─── Vector Database
    │       │
    │       └─── Resume Embeddings (FAISS/Chroma)
    │
    └─── File System
            │
            ├─── data/resumes/{user_id}/ (PDF files)
            ├─── generated_resumes/ (enhanced resumes)
            └── logs/ (application logs)
```

### Entity Relationship Diagram

```
┌──────────────┐
│     User     │
├──────────────┤
│ id (PK)      │
│ email        │
│ password_hash│
│ name         │
│ created_at   │
└──────┬───────┘
       │ 1
       │
       │ N
┌──────▼─────────┐         ┌──────────────┐
│  OAuth Tokens  │         │   Resumes    │
├────────────────┤         ├──────────────┤
│ id (PK)        │         │ id (PK)      │
│ user_id (FK)   │         │ user_id (FK) │
│ provider       │         │ filename     │
│ access_token   │         │ file_path    │
│ refresh_token  │         │ file_size    │
│ expires_at     │         │ created_at   │
└────────────────┘         └──────┬───────┘
                                  │ 1
                                  │
                                  │ N
                          ┌───────▼──────────┐
                          │ Job Applications │
                          ├──────────────────┤
                          │ id (PK)          │
                          │ user_id (FK)     │
                          │ company          │
                          │ role             │
                          │ resume_used (FK) │
                          │ match_score      │
                          │ status           │
                          │ applied_date     │
                          └──────────────────┘
```

---

## Security Architecture

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                            │
└─────────────────────────────────────────────────────────────────┘

1. Email/Password Login
┌─────────────────────────────────────────────────────────────────┐
│ User → Enter Credentials → POST /api/auth/login                 │
│ Backend → Validate Password → Generate JWT → Return Token        │
│ Frontend → Store Token → Use in Authorization Header             │
└─────────────────────────────────────────────────────────────────┘

2. Google OAuth Flow
┌─────────────────────────────────────────────────────────────────┐
│ User → Click Google Login → GET /api/auth/google                │
│ Backend → Generate Auth URL → Redirect to Google                 │
│ User → Grant Permission → Google Callback → /api/auth/callback  │
│ Backend → Exchange Code → Get User Info → Create/Update User     │
│ Backend → Generate JWT → Redirect to Frontend with Token         │
└─────────────────────────────────────────────────────────────────┘

3. Outlook OAuth Flow
┌─────────────────────────────────────────────────────────────────┐
│ User → Click Outlook Login → GET /api/auth/outlook              │
│ Backend → Generate Auth URL → Redirect to Microsoft             │
│ User → Grant Permission → Microsoft Callback → /api/auth/callback│
│ Backend → Exchange Code → Get User Info → Create/Update User    │
│ Backend → Generate JWT → Redirect to Frontend with Token        │
└─────────────────────────────────────────────────────────────────┘
```

### Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                               │
└─────────────────────────────────────────────────────────────────┘

1. Network Security
   ├── HTTPS/TLS Encryption
   ├── CORS Configuration
   └── Rate Limiting

2. Application Security
   ├── JWT Authentication
   ├── OAuth 2.0 Authorization
   ├── Input Validation
   ├── SQL Injection Prevention
   └── XSS Protection

3. Data Security
   ├── Password Hashing (Bcrypt)
   ├── Token Encryption
   ├── Secure File Storage
   └── Environment Variable Protection

4. API Security
   ├── API Key Management
   ├── Request Validation
   ├── Error Handling
   └── Audit Logging
```

### Security Middleware Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                  SECURITY MIDDLEWARE STACK                        │
└─────────────────────────────────────────────────────────────────┘

Request
    │
    ▼
┌──────────────────┐
│ CORS Middleware  │  ← Cross-Origin Resource Sharing
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Rate Limiter     │  ← Request Rate Limiting
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Auth Middleware  │  ← JWT Verification
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Validator        │  ← Input Validation
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Sanitizer        │  ← Input Sanitization
└──────────────────┘
    │
    ▼
Business Logic
```

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────────────┐
│                  DEVELOPMENT ENVIRONMENT                          │
└─────────────────────────────────────────────────────────────────┘

Local Machine
    │
    ├─── Frontend Dev Server (Vite)
    │       │
    │       └─── http://localhost:5173
    │
    ├─── Backend Dev Server (uvicorn --reload)
    │       │
    │       └─── http://localhost:8000
    │
    ├─── SQLite Database (data/users.db)
    │
    └─── Vector Database (vector_db/)
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────────┐
│                  PRODUCTION ENVIRONMENT                           │
└─────────────────────────────────────────────────────────────────┘

Load Balancer (Nginx)
    │
    ├─── Frontend Server (Nginx/CDN)
    │       │
    │       └─── Static React Build
    │
    └─── Backend Server (Gunicorn/uWSGI)
            │
            ├─── FastAPI Application
            │
            ├─── PostgreSQL Database
            │
            ├─── Redis Cache
            │
            └─── Vector Database (ChromaDB)
```

### Container Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTAINER ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────┘

Docker Compose
    │
    ├─── Frontend Container
    │       │
    │       ├─── Nginx
    │       └─── React Build
    │
    ├─── Backend Container
    │       │
    │       ├─── FastAPI
    │       ├─── Python Dependencies
    │       └─── Application Code
    │
    ├─── Database Container
    │       │
    │       └── PostgreSQL
    │
    └─── Redis Container
            │
            └─── Redis Cache
```

---

## Technology Stack

### Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2+ | UI Framework |
| Vite | 8.2+ | Build Tool |
| React Router | 7.18+ | Routing |
| Axios | 1.19+ | HTTP Client |
| Lucide React | 1.34+ | Icons |

### Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.9+ | Runtime |
| FastAPI | 0.100+ | Web Framework |
| Uvicorn | Latest | ASGI Server |
| LangChain | Latest | LLM Framework |
| Pydantic | Latest | Data Validation |

### Database Stack

| Technology | Purpose |
|------------|---------|
| SQLite | Primary Database |
| FAISS | Vector Search |
| ChromaDB | Alternative Vector DB |

### AI/ML Stack

| Technology | Purpose |
|------------|---------|
| OpenRouter | LLM API |
| Google Gemini | LLM API |
| Sentence Transformers | Embeddings |
| LangChain | AI Framework |

### Integration Stack

| Technology | Purpose |
|------------|---------|
| Gmail API | Email Service |
| Microsoft Graph | Email Service |
| Selenium | Browser Automation |
| PyPDF2 | PDF Processing |

---

## API Design

### RESTful API Principles

The API follows RESTful design principles:

- **Resource-based URLs**: `/api/resumes`, `/api/applications`
- **HTTP Methods**: GET, POST, PUT, DELETE
- **Status Codes**: Proper HTTP status codes
- **JSON Format**: Request/response in JSON
- **Authentication**: JWT Bearer tokens

### API Endpoint Categories

```
/api/
├── /auth/              # Authentication endpoints
│   ├── /signup         # Register new user
│   ├── /login          # User login
│   ├── /me             # Get current user
│   ├── /google         # Google OAuth
│   ├── /outlook        # Outlook OAuth
│   └── /connect/{provider}  # Connect provider
├── /resumes/           # Resume management
│   ├── POST /          # Upload resume
│   ├── GET /           # List resumes
│   └── DELETE /{filename}  # Delete resume
├── /jobs/              # Job application
│   ├── /analyze        # Analyze job description
│   ├── /upload-jd      # Upload JD file
│   ├── /match-resume   # Match resume to job
│   ├── /auto-apply     # Complete application
│   └── /send-email     # Send email
└── /dashboard/         # Analytics
    ├── GET /           # Dashboard stats
    └── /applications/  # Application history
```

### Request/Response Format

**Standard Response Format:**
```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation successful",
  "errors": []
}
```

**Error Response Format:**
```json
{
  "success": false,
  "data": null,
  "message": "Error occurred",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

---

## Monitoring & Logging

### Logging Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOGGING ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────┘

Application Components
    │
    ├─── Structured Logging (Python logging)
    │       │
    │       ├─── File Logging (logs/app.log)
    │       ├─── Console Logging (stdout)
    │       └──── Error Logging (logs/error.log)
    │
    ├─── Request Logging (FastAPI middleware)
    │       │
    │       ├─── Access Logs
    │       ├─── Performance Logs
    │       └──── Error Logs
    │
    └──── Business Event Logging
            │
            ├─── User Actions
            ├─── API Calls
            └──── Application Events
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors requiring immediate attention

### Monitoring Metrics

Key metrics to monitor:

1. **Application Metrics**
   - Request rate
   - Response time
   - Error rate
   - Active users

2. **Business Metrics**
   - Applications sent
   - Success rate
   - Resume matches
   - Email delivery rate

3. **System Metrics**
   - CPU usage
   - Memory usage
   - Disk usage
   - Network I/O

---

## Scalability Considerations

### Horizontal Scaling

```
┌─────────────────────────────────────────────────────────────────┐
│                  HORIZONTAL SCALING                               │
└─────────────────────────────────────────────────────────────────┘

Load Balancer
    │
    ├─── Backend Instance 1
    │       │
    │       ├─── FastAPI
    │       └──── Shared Database
    │
    ├─── Backend Instance 2
    │       │
    │       ├─── FastAPI
    │       └──── Shared Database
    │
    └─── Backend Instance N
            │
            ├─── FastAPI
            └──── Shared Database
```

### Vertical Scaling

- **CPU**: Multi-core processing for parallel operations
- **Memory**: Increased RAM for larger vector databases
- **Storage**: SSD for faster file operations
- **Network**: Higher bandwidth for API calls

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHING STRATEGY                              │
└─────────────────────────────────────────────────────────────────┘

Application
    │
    ├─── LLM Response Cache (Redis)
    │       │
    │       ├─── JD Analysis Results
    │       ├─── Email Generation
    │       └──── Resume Enhancement
    │
    ├─── Vector Embedding Cache (Redis)
    │       │
    │       └──── Resume Embeddings
    │
    └──── Database Query Cache (Redis)
            │
            ├─── User Data
            ├─── Resume Metadata
            └──── Application History
```

---

## Performance Optimization

### Database Optimization

1. **Indexing**
   - User email index
   - Resume user_id index
   - Application user_id index
   - Application status index

2. **Query Optimization**
   - Use prepared statements
   - Implement pagination
   - Optimize JOIN operations
   - Use connection pooling

3. **Caching**
   - Redis for frequently accessed data
   - Application-level caching
   - Database query caching

### API Optimization

1. **Async Operations**
   - Async/await for I/O operations
   - Concurrent API calls
   - Background task processing

2. **Response Optimization**
   - Compression (gzip)
   - Minimal response size
   - Selective field loading

3. **Rate Limiting**
   - Per-user rate limits
   - API endpoint throttling
   - Burst protection

---

## Backup & Recovery

### Backup Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKUP STRATEGY                                │
└─────────────────────────────────────────────────────────────────┘

Daily Backups
    │
    ├─── Database Backup (SQLite dump)
    │       │
    │       ├─── Full backup
    │       └──── Incremental backup
    │
    ├─── File System Backup
    │       │
    │       ├─── Resume files
    │       ├─── Generated resumes
    │       └──── Configuration files
    │
    └──── Vector Database Backup
            │
            └──── FAISS/ChromaDB exports
```

### Recovery Plan

1. **Database Recovery**
   - Restore from latest backup
   - Apply transaction logs
   - Verify data integrity

2. **File Recovery**
   - Restore from backup
   - Verify file integrity
   - Update database references

3. **Disaster Recovery**
   - Off-site backup storage
   - Recovery time objectives
   - Recovery point objectives

---

## Future Architecture Improvements

### Planned Enhancements

1. **Microservices Architecture**
   - Separate user service
   - Resume processing service
   - Email service
   - Analytics service

2. **Event-Driven Architecture**
   - Message queue (RabbitMQ/Kafka)
   - Event sourcing
   - CQRS pattern

3. **Advanced Caching**
   - Distributed caching
   - CDN integration
   - Edge computing

4. **Enhanced Security**
   - Multi-factor authentication
   - Advanced threat detection
   - Compliance certifications

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-31  
**Maintained By**: Development Team