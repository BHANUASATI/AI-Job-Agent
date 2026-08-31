# 🚀 AI Job Agent v2.0

An intelligent AI-powered job application automation system that analyzes job descriptions, matches the best resume from your database, generates personalized application emails, and sends them via Gmail or Outlook automatically.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![React](https://img.shields.io/badge/React-19+-61DAFB.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎉 What's New in v2.0

- **✨ Modern Frontend**: React-based SPA with Vite for fast development
- **🔐 Full Authentication**: JWT-based auth with Google/Outlook OAuth support
- **📊 Analytics Dashboard**: Comprehensive job application tracking and analytics
- **🎯 Multi-Provider Email**: Support for both Gmail and Outlook email providers
- **🤖 Enhanced AI**: Improved job analysis and resume matching with better prompts
- **📝 JD File Upload**: Parse job descriptions from PDF, DOCX, and TXT files
- **🔌 Dynamic Port Assignment**: Automatic port detection to avoid conflicts
- **🛡️ Comprehensive Security**: Input validation, file type checking, and secure OAuth
- **📱 Responsive Design**: Mobile-friendly interface with modern UI components
- **🔧 Centralized Configuration**: Environment-based configuration management

## ✨ Features

### Core Functionality
- **🤖 Intelligent JD Analysis**: Uses AI to extract key information from job descriptions including company name, role, required skills, experience, recruiter email, and location
- **📄 Smart Resume Matching**: Leverages vector embeddings and semantic search to find the best-matching resume for each job from your database
- **✍️ Professional Email Generation**: Creates customized, HR-friendly application emails tailored to the specific job and candidate profile
- **🎯 Smart Subject Lines**: Generates attention-grabbing, professional email subject lines based on job requirements
- **📧 Automated Email Sending**: Integrates with Gmail API and Outlook API to automatically send applications with resume attachments
- **🎨 Modern Web Interface**: React-based SPA with beautiful UI and intuitive navigation

### Advanced Features
- **🔐 Multi-Provider Authentication**: Email/password login, Google OAuth, and Microsoft OAuth support
- **📊 Analytics Dashboard**: Track application statistics, success rates, and trends over time
- **📁 Resume Management**: Upload, manage, and organize multiple resumes through the web interface
- **🔍 RAG-Powered Search**: Uses Retrieval-Augmented Generation for accurate resume-job matching
- **📄 JD File Parsing**: Upload and parse job descriptions from PDF, DOCX, or TXT files
- **🤖 Resume Enhancement**: AI-powered resume enhancement to fill skill gaps
- **🌐 Web Scraping**: Built-in scrapers for Internshala and Wellfound job platforms
- **📝 Overleaf Integration**: Automated resume editing via Overleaf platform
- **📧 Multi-Email Support**: Send applications via Gmail or Outlook based on user preference
- **💾 Persistent Storage**: SQLite database for user data, applications, and resume tracking

### Developer Features
- **🖥️ Full CLI Support**: Command-line interface with dry-run and interactive modes
- **📝 Input Validation**: Robust validation for all user inputs and file uploads
- **🛡️ Error Handling**: Comprehensive error handling and structured logging throughout
- **🔧 Configuration Management**: Centralized configuration via environment variables
- **🚀 Fast API Performance**: Async FastAPI backend for high-performance operations
- **📖 Well-Documented**: Comprehensive documentation and code comments

## 🏗️ Architecture

### System Architecture Diagram

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

### Project Structure

```
ai-job-agent/
├── agents/                    # AI agents for specific tasks
│   ├── jd_analyzer.py        # Job description analysis
│   ├── resume_loader.py      # PDF resume loading
│   ├── resume_splitter.py    # Document chunking
│   ├── vector_store.py       # Vector database creation
│   ├── resume_retriever.py   # Semantic search
│   ├── resume_selector.py    # Best resume selection
│   ├── email_generator.py    # Email generation
│   ├── subject_generator.py  # Subject line generation
│   ├── resume_enhancer.py    # AI resume enhancement
│   ├── jd_resume_comparator.py # JD vs resume comparison
│   ├── chatbot.py            # AI chatbot interface
│   ├── link_scraper.py       # Job link scraping
│   └── post_parser.py        # Job post parsing
├── automation/               # Browser automation
│   ├── browser_manager.py   # Selenium browser management
│   ├── overleaf/            # Overleaf automation
│   │   ├── login.py         # Overleaf authentication
│   │   ├── editor.py        # Resume editing
│   │   ├── downloader.py    # PDF download
│   │   └── project_manager.py # Project management
│   ├── visual_logger.py     # Visual debugging
│   └── config.py            # Automation configuration
├── backend/                  # FastAPI backend
│   ├── main.py              # API endpoints
│   └── auth.py              # Authentication logic
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── utils/           # Utility functions
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
├── services/                 # External service integrations
│   ├── llm_service.py       # LLM configuration
│   ├── gmail_service.py     # Gmail API integration
│   ├── outlook_service.py   # Outlook API integration
│   ├── database_service.py  # Database operations
│   ├── jd_parser.py         # Job description parsing
│   ├── latex_resume_service.py # LaTeX resume generation
│   ├── pdf_generator.py     # PDF generation
│   └── captcha_solver.py    # CAPTCHA solving
├── scrapers/                 # Web scrapers
│   ├── internshala_scraper.py
│   └── wellfound_scraper.py
├── utils/                    # Utility functions
│   ├── config_loader.py     # Configuration loading
│   ├── logger.py            # Logging configuration
│   ├── exceptions.py        # Custom exceptions
│   ├── validators.py        # Input validation
│   ├── port_utils.py        # Port management
│   └── helpers.py           # Helper functions
├── config/                   # Configuration files
│   ├── settings.py          # Centralized configuration
│   └── user_profile.json    # User profile data
├── data/                     # Runtime data
│   ├── resumes/             # User resume storage
│   └── users.db             # SQLite database
├── logs/                     # Application logs
├── database/                 # Legacy database files
├── vector_db/               # Vector database storage
├── generated_resumes/       # Enhanced resume storage
├── resume_templates/       # LaTeX resume templates
├── app.py                   # CLI application
├── app_ui.py               # Streamlit UI (legacy)
├── app_dashboard.py        # Streamlit dashboard (legacy)
├── run_ui.py              # Dynamic UI launcher
├── run_dashboard.py       # Dynamic dashboard launcher
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 🔄 Working Model

### Application Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        USER APPLICATION WORKFLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

1. AUTHENTICATION FLOW
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  User → Login Page → Choose Auth Method → Authenticate → JWT Token → Dashboard│
│                                                                               │
│  Auth Methods:                                                                │
│  - Email/Password → Backend validation → JWT generation                      │
│  - Google OAuth → Google consent → Token exchange → User creation → JWT       │
│  - Outlook OAuth → Microsoft consent → Token exchange → User creation → JWT  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

2. RESUME MANAGEMENT FLOW
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  User → Upload Resume → File Validation → Store in data/resumes/{user_id}/   │
│       → Database Record → Display in Resume List                              │
│                                                                               │
│  Resume Operations:                                                           │
│  - Upload: PDF validation → User directory → Database insertion               │
│  - List: Query database → Check file existence → Return metadata             │
│  - Delete: Remove file → Database deletion → Update UI                        │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

3. JOB APPLICATION WORKFLOW
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  User → Enter JD (text/file) → Analyze Job → Review Results → Apply         │
│                                                                               │
│  Step-by-Step Process:                                                        │
│                                                                               │
│  3.1 JOB DESCRIPTION ANALYSIS                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Input: JD text or uploaded file                                         │  │
│  │ Process: LLM analysis (OpenRouter/Gemini)                              │  │
│  │ Output: Structured data (company, role, skills, experience, email, etc.)│  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  3.2 RESUME MATCHING                                                       │  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Process:                                                                │  │
│  │ 1. Load user's resumes from data/resumes/{user_id}/                    │  │
│  │ 2. Extract text from PDFs using PyPDF2                                 │  │
│  │ 3. Split documents into chunks (configurable size/overlap)              │  │
│  │ 4. Create vector embeddings using sentence-transformers                │  │
│  │ 5. Build vector store (FAISS/Chroma)                                   │  │
│  │ 6. Semantic search with job query (role + skills + keywords)          │  │
│  │ 7. Score resumes based on:                                              │  │
│  │    - Chunk similarity (40%)                                             │  │
│  │    - Skill matching (30%)                                               │  │
│  │    - Keyword matching (15%)                                             │  │
│  │    - Role relevance (10%)                                               │  │
│  │    - Experience match (5%)                                               │  │
│  │ Output: Best resume with match score and content                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  3.3 GAP ANALYSIS                                                        │  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Process: Compare JD requirements vs resume content                      │  │
│  │ Output:                                                                 │  │
│  │ - Match score (percentage)                                             │  │
│  │ - Missing skills (critical/optional)                                  │  │
│  │ - Strengths and strong areas                                          │  │
│  │ - Experience alignment                                                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  3.4 RESUME ENHANCEMENT (Optional)                                         │  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ If enabled and gaps found:                                              │  │
│  │ 1. Generate enhanced resume content using LLM                          │  │
│  │ 2. Create LaTeX version with missing skills integrated                │  │
│  │ 3. Compile to PDF using LaTeX service                                  │  │
│  │ 4. Save to generated_resumes/                                          │  │
│  │ Output: Enhanced resume PDF path                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  3.5 EMAIL GENERATION                                                     │  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Subject Line Generation:                                                │  │
│  │ 1. Priority: JD-suggested subject → LLM-generated → Fallback          │  │
│  │ 2. Format: Professional, attention-grabbing, personalized              │  │
│  │                                                                        │  │
│  │ Email Body Generation:                                                  │  │
│  │ 1. Incorporate candidate profile, job details, resume highlights        │  │
│  │ 2. 4-paragraph structure: Opening, qualifications, fit, closing         │  │
│  │ 3. Professional tone, HR-friendly language                             │  │
│  │ 4. Word count: 90-140 words (configurable)                             │  │
│  │ 5. Customizable signature with social links                             │  │
│  │ Output: Subject line and email body                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  3.6 EMAIL SENDING (Optional)                                              │  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ If auto-send enabled:                                                   │  │
│  │ 1. User selects email provider (Gmail/Outlook)                         │  │
│  │ 2. Backend retrieves OAuth token from database                         │  │
│  │ 3. Send email with resume attachment via respective API                │  │
│  │ 4. Update application status in database                               │  │
│  │ Output: Success confirmation or error message                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  3.7 DATABASE RECORDING                                                   │  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Store application record:                                               │  │
│  │ - Company, role, location                                               │  │
│  │ - Skills and experience requirements                                    │  │
│  │ - Resume used and match score                                           │  │
│  │ - Application status and timestamp                                      │  │
│  │ - Email provider and recipient                                          │  │
│  │ Output: Application saved to database                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

4. DASHBOARD ANALYTICS
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  Real-time Statistics:                                                       │
│  - Total applications count                                                  │
│  - Sent applications count                                                   │
│  - Total resumes count                                                       │
│  - Recent applications (last 5)                                             │
│  - OAuth connection status                                                   │
│  - Application success rate                                                  │
│  - Popular companies and roles                                               │
│                                                                               │
│  Visualizations:                                                             │
│  - Application trends over time                                              │
│  - Success rate by company                                                   │
│  - Resume performance metrics                                                │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

USER INPUT
    │
    ├─── Job Description (Text/File)
    │       │
    │       ├─── Text Input → Direct to JD Analyzer
    │       └─── File Upload → JD Parser → Extracted Text → JD Analyzer
    │
    ├─── Resume Upload
    │       │
    │       └─── PDF File → Validation → Store → Database Record
    │
    └─── Authentication
            │
            └─── Credentials → Validation → JWT Token → Session

PROCESSING LAYER
    │
    ├─── JD Analysis Agent
    │       │
    │       └─── LLM Service → Structured JD Data
    │
    ├─── Resume Processing Pipeline
    │       │
    │       ├─── Resume Loader → PDF Text Extraction
    │       ├─── Resume Splitter → Document Chunking
    │       ├─── Vector Store → Embedding Generation
    │       └─── Resume Retriever → Semantic Search & Scoring
    │
    ├─── Gap Analysis Agent
    │       │
    │       └─── JD vs Resume Comparison → Gap Report
    │
    ├─── Email Generation Agent
    │       │
    │       ├─── Subject Generator → Professional Subject
    │       └─── Email Generator → Personalized Email Body
    │
    └─── Resume Enhancement (Optional)
            │
            └─── AI Enhancement → LaTeX Generation → PDF Compilation

STORAGE LAYER
    │
    ├─── SQLite Database (data/users.db)
    │       │
    │       ├─── Users table (auth profiles)
    │       ├─── Resumes table (file metadata)
    │       ├─── Job_applications table (application records)
    │       └── OAuth_tokens table (provider tokens)
    │
    ├─── File System
    │       │
    │       ├─── data/resumes/{user_id}/ (user resume files)
    │       ├─── generated_resumes/ (enhanced resumes)
    │       ├─── vector_db/ (vector embeddings)
    │       └── logs/ (application logs)
    │
    └─── Vector Database
            │
            └─── FAISS/Chroma (semantic search indexes)

EXTERNAL SERVICES
    │
    ├─── LLM APIs
    │       │
    │       ├─── OpenRouter (NVIDIA Nemotron)
    │       └─── Google Gemini
    │
    ├─── Email Providers
    │       │
    │       ├─── Gmail API (OAuth 2.0)
    │       └───── Outlook API (Microsoft Graph)
    │
    └─── Job Platforms
            │
            ├─── Internshala (web scraping)
            └───── Wellfound (web scraping)
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.9 or higher**
- **Node.js 16 or higher** (for frontend development)
- **Google Gemini API Key** or **OpenRouter API Key**
- **Gmail account with API access** (optional, for email sending)
- **Microsoft Azure account** (optional, for Outlook integration)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai-job-agent
```

2. **Set up Python environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

3. **Set up frontend environment**
```bash
cd frontend
npm install
cd ..
```

4. **Configure environment variables**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

5. **Configure required API keys in `.env`**

```env
# LLM Configuration (choose one)
LLM_PROVIDER=openrouter
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
OPENROUTER_API_KEY=your_openrouter_api_key_here
# OR
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your_gemini_api_key_here

# Email Provider Configuration (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
OUTLOOK_CLIENT_ID=your_outlook_client_id
OUTLOOK_CLIENT_SECRET=your_outlook_client_secret

# Application Configuration
APP_NAME=AI Job Agent
APP_VERSION=2.0.0
DEBUG=false

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///data/users.db

# Frontend Configuration
FRONTEND_URL=http://localhost:5173
```

6. **Configure user profile**
```bash
# Edit config/user_profile.json with your information
cat > config/user_profile.json << EOF
{
  "name": "Your Name",
  "email": "your.email@example.com",
  "phone": "+1-234-567-8900",
  "location": "Your Location",
  "github": "https://github.com/yourusername",
  "linkedin": "https://linkedin.com/in/yourprofile",
  "portfolio": "https://yourportfolio.com"
}
EOF
```

7. **Initialize database**
```bash
# The database will be automatically created on first run
# Manual initialization (optional):
python -c "from backend.auth import init_db; init_db()"
```

### Running the Application

#### Development Mode (Recommended)

**Terminal 1 - Start Backend:**
```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI backend
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
# Start React frontend
cd frontend
npm run dev
```

Access the application at `http://localhost:5173`

#### Production Mode

**Build Frontend:**
```bash
cd frontend
npm run build
cd ..
```

**Run Backend (serves frontend):**
```bash
source venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Access the application at `http://localhost:8000`

#### Legacy Streamlit Interface

For the original Streamlit-based interface:

```bash
# UI
python run_ui.py

# Dashboard
python run_dashboard.py
```

#### CLI Mode

For command-line usage:

```bash
# Direct job description
python app.py --jd "Job description text here"

# From file
python app.py --jd-file path/to/job_description.txt

# Dry run (generate email without sending)
python app.py --jd "Job description" --dry-run

# Interactive mode
python app.py --interactive

# With resume enhancement
python app.py --jd "Job description" --enhance-resume
```

## 🔧 Configuration

### Environment Variables

The application uses a comprehensive configuration system via environment variables. Key configurations:

#### LLM Configuration
```env
LLM_PROVIDER=openrouter              # openrouter, gemini, openai
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
OPENROUTER_API_KEY=your_key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_TEMPERATURE=0.3
LLM_MAX_RETRIES=2
```

#### Email Provider Configuration
```env
# Gmail OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Outlook OAuth
OUTLOOK_CLIENT_ID=your_client_id
OUTLOOK_CLIENT_SECRET=your_client_secret
```

#### Database Configuration
```env
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///data/users.db
```

#### Processing Configuration
```env
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

#### Email Configuration
```env
EMAIL_WORD_COUNT_MIN=90
EMAIL_WORD_COUNT_MAX=140
EMAIL_SIGNATURE_FORMAT=professional
```

### User Profile

Edit `config/user_profile.json` with your personal information:

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-123-4567",
  "location": "San Francisco, CA",
  "github": "https://github.com/johndoe",
  "linkedin": "https://linkedin.com/in/johndoe",
  "portfolio": "https://johndoe.dev"
}
```

## 📖 Usage Guide

### Web Interface Usage

1. **Authentication**
   - Navigate to the application URL
   - Choose authentication method (Email/Password, Google, or Outlook)
   - Complete authentication process
   - Access dashboard

2. **Upload Resumes**
   - Go to "Resumes" tab
   - Click "Upload Resume" or drag & drop PDF files
   - Wait for upload confirmation
   - View uploaded resumes in the list

3. **Job Application**
   - Go to "Auto Apply" tab
   - Enter job description text OR upload JD file (PDF/DOCX/TXT)
   - Click "Analyze Job" to extract job details
   - Review analysis results (company, role, skills, etc.)
   - Click "Find Best Resume" to match resumes
   - Review match scores and gap analysis
   - Generate and review email
   - Toggle "Auto-send" to send immediately
   - Click "Send Application" or save as draft

4. **Dashboard Analytics**
   - View application statistics
   - Track success rates
   - Monitor recent applications
   - View OAuth connection status

### CLI Usage Examples

**Basic Job Application:**
```bash
python app.py --jd "Senior Python Developer at TechCorp with 5+ years experience in Django, React, and AWS"
```

**From File:**
```bash
python app.py --jd-file job_description.txt
```

**Dry Run (Preview Only):**
```bash
python app.py --jd "Job description" --dry-run
```

**With Resume Enhancement:**
```bash
python app.py --jd "Job description" --enhance-resume
```

**Interactive Mode:**
```bash
python app.py --interactive
# Then paste your job description when prompted
```

## 🔐 Security & Privacy

### Data Security
- **API Keys**: Never commit `.env` or credentials to version control
- **Token Storage**: OAuth tokens stored securely in SQLite database
- **Local Processing**: Resume data processed locally; only sent to LLM APIs
- **Input Validation**: All user inputs validated and sanitized
- **File Type Checking**: Strict validation for uploaded files
- **Path Traversal Prevention**: Sanitized filenames to prevent directory traversal

### Authentication
- **JWT Tokens**: Secure token-based authentication
- **OAuth 2.0**: Industry-standard OAuth for Google/Outlook
- **Password Hashing**: Bcrypt hashing for user passwords
- **Token Expiration**: Configurable token lifetimes
- **Secure Headers**: CORS and security headers configured

### Privacy
- **User Data**: User-specific data isolation
- **Resume Storage**: User-specific directories
- **Database**: Per-user data segmentation
- **Logs**: No sensitive data in logs
- **API Calls**: Minimal data sent to external APIs

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.100+
- **Language**: Python 3.9+
- **Database**: SQLite
- **Authentication**: JWT + OAuth 2.0
- **LLM Framework**: LangChain
- **Vector Database**: FAISS/Chroma
- **PDF Processing**: PyPDF2, python-docx
- **Email APIs**: Gmail API, Microsoft Graph API

### Frontend
- **Framework**: React 19+
- **Build Tool**: Vite 8+
- **Routing**: React Router 7+
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Language**: JavaScript (ES6+)

### AI/ML
- **LLM Providers**: OpenRouter, Google Gemini
- **Embeddings**: Sentence Transformers
- **Vector Search**: FAISS, ChromaDB
- **Text Processing**: LangChain

### DevOps
- **Package Manager**: pip, npm
- **Environment**: python-dotenv
- **Logging**: Python logging
- **Validation**: Pydantic

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_automation.py

# Run with coverage
pytest --cov=agents --cov=services --cov-report=html
```

### Test Files

- `test_automation.py` - Browser automation tests
- `test_complete_workflow.py` - End-to-end workflow tests
- `test_overleaf_*.py` - Overleaf integration tests
- `test_visual_*.py` - Visual mode tests

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --port 8001
```

**Database Locked**
```bash
# Remove database lock
rm data/users.db-wal
rm data/users.db-shm
```

**OAuth Authentication Fails**
```bash
# Check OAuth configuration
curl http://localhost:8000/api/auth/config

# Verify environment variables
echo $GOOGLE_CLIENT_ID
echo $OUTLOOK_CLIENT_ID
```

**LLM API Errors**
```bash
# Verify API key
echo $OPENROUTER_API_KEY

# Test API connection
python -c "from services.llm_service import get_llm; print(get_llm())"
```

**Frontend Build Issues**
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Debug Mode

Enable debug logging:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

Check logs:
```bash
tail -f logs/app.log
```

## 📚 API Documentation

### Authentication Endpoints

- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login with email/password
- `GET /api/auth/me` - Get current user
- `GET /api/auth/google` - Get Google OAuth URL
- `GET /api/auth/google/callback` - Google OAuth callback
- `GET /api/auth/outlook` - Get Outlook OAuth URL
- `GET /api/auth/outlook/callback` - Outlook OAuth callback

### Job Application Endpoints

- `POST /api/analyze-job` - Analyze job description
- `POST /api/upload-jd` - Upload job description file
- `POST /api/match-resume` - Find best matching resume
- `POST /api/auto-apply` - Complete job application
- `POST /api/send-email` - Send application email

### Resume Management Endpoints

- `POST /api/upload-resume` - Upload resume PDF
- `GET /api/resumes` - List user resumes
- `DELETE /api/resumes/{filename}` - Delete resume

### Dashboard Endpoints

- `GET /api/dashboard` - Get dashboard statistics
- `GET /api/applications` - List user applications
- `GET /api/applications/{id}` - Get application details

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions
- Write tests for new features
- Update documentation as needed
- Keep commits small and focused

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google for the Gemini AI API
- OpenRouter for accessible LLM APIs
- LangChain for the excellent LLM framework
- FastAPI for the modern web framework
- React for the frontend library
- The open-source community for amazing tools

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

## 🗺️ Roadmap

### v2.1 (Planned)
- [ ] Email template system
- [ ] Bulk job application
- [ ] Interview scheduling integration
- [ ] Advanced analytics and reporting
- [ ] Mobile app (React Native)

### v2.2 (Future)
- [ ] Multi-language support
- [ ] Additional job platform integrations
- [ ] AI-powered interview preparation
- [ ] Salary negotiation assistance
- [ ] Application workflow automation

---

**Made with ❤️ by Bhanu Asati**

**Version**: 2.0.0  
**Last Updated**: 2026-08-31
