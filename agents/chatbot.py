"""
RAG-based chatbot agent.

Answers questions about:
  - The user's uploaded resumes (content, skills, experience)
  - An optionally attached job description PDF
  - Application history (stats pulled from DB and injected as context)
  - Portal information (how to use features)
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from services.llm_service import get_llm
from config.settings import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Embeddings (shared singleton — expensive to init)
# ---------------------------------------------------------------------------
_embeddings: Optional[HuggingFaceEmbeddings] = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": Config.EMBEDDING_DEVICE},
        )
    return _embeddings


# ---------------------------------------------------------------------------
# Per-user vector store cache  {user_id: FAISS}
# ---------------------------------------------------------------------------
_vs_cache: Dict[int, FAISS] = {}


def _load_pdf_chunks(pdf_path: Path, source_tag: str) -> list:
    """Load a PDF and return split LangChain Document chunks."""
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    for d in docs:
        d.metadata["source"] = source_tag
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    return splitter.split_documents(docs)


def build_user_vector_store(user_id: int, resumes_dir: Path, jd_pdf_path: Optional[Path] = None) -> FAISS:
    """
    Build (or rebuild) a FAISS vector store for the given user.

    Indexes:
      - All PDF resumes in resumes_dir
      - Optionally a JD PDF (tagged as 'job_description')
    """
    all_chunks = []

    pdf_files = list(resumes_dir.glob("*.pdf"))
    for pdf in pdf_files:
        try:
            chunks = _load_pdf_chunks(pdf, source_tag=f"resume:{pdf.name}")
            all_chunks.extend(chunks)
            logger.info(f"Indexed resume: {pdf.name} ({len(chunks)} chunks)")
        except Exception as e:
            logger.warning(f"Could not index {pdf.name}: {e}")

    if jd_pdf_path and jd_pdf_path.exists():
        try:
            chunks = _load_pdf_chunks(jd_pdf_path, source_tag="job_description")
            all_chunks.extend(chunks)
            logger.info(f"Indexed JD PDF: {jd_pdf_path.name} ({len(chunks)} chunks)")
        except Exception as e:
            logger.warning(f"Could not index JD PDF: {e}")

    if not all_chunks:
        raise ValueError("No content found to index. Please upload at least one resume.")

    vs = FAISS.from_documents(all_chunks, _get_embeddings())
    _vs_cache[user_id] = vs
    return vs


def get_or_build_vs(user_id: int, resumes_dir: Path, jd_pdf_path: Optional[Path] = None) -> FAISS:
    """Return cached vector store or build a fresh one."""
    if user_id not in _vs_cache or jd_pdf_path is not None:
        return build_user_vector_store(user_id, resumes_dir, jd_pdf_path)
    return _vs_cache[user_id]


def invalidate_cache(user_id: int):
    """Force rebuild next time (call after a new resume is uploaded)."""
    _vs_cache.pop(user_id, None)


# ---------------------------------------------------------------------------
# DB context helpers
# ---------------------------------------------------------------------------
def _get_stats_context(user_id: int) -> str:
    """Pull application stats from SQLite and format as plain text."""
    try:
        db_path = Config.BASE_DIR / "data" / "users.db"
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM job_applications WHERE user_id=?", (user_id,))
        total = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM job_applications WHERE user_id=? AND email_sent=1",
            (user_id,),
        )
        sent = cur.fetchone()[0]

        cur.execute(
            """SELECT company, role, status, created_at, resume_file, match_score,
                      email_subject, recipient_email
               FROM job_applications WHERE user_id=?
               ORDER BY created_at DESC LIMIT 10""",
            (user_id,),
        )
        rows = cur.fetchall()

        cur.execute(
            "SELECT COUNT(*) FROM resumes WHERE user_id=?", (user_id,)
        )
        resume_count = cur.fetchone()[0]

        conn.close()

        lines = [
            f"=== PORTAL STATISTICS ===",
            f"Total applications submitted: {total}",
            f"Emails sent: {sent}",
            f"Resumes uploaded (tracked in DB): {resume_count}",
            "",
            "=== RECENT APPLICATIONS (latest 10) ===",
        ]
        for r in rows:
            company, role, status, created_at, resume_file, score, subject, recipient = r
            score_str = f"{round(score * 100) if score and score <= 1 else round(score or 0)}%" if score else "N/A"
            lines.append(
                f"- {role} at {company} | Status: {status} | "
                f"Date: {created_at} | Resume: {resume_file} | "
                f"Match: {score_str} | To: {recipient or 'N/A'} | Subject: {subject or 'N/A'}"
            )

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Could not load stats context: {e}")
        return "Portal statistics are temporarily unavailable."


_PORTAL_GUIDE = """
=== AI JOB AGENT — PORTAL GUIDE ===

TABS AVAILABLE:
1. Overview    – Dashboard with stats: total applications, emails sent, resumes uploaded, connected accounts.
2. Resumes     – Upload PDF resumes (drag-and-drop or file picker). Delete resumes. Multiple resumes supported.
3. Auto Apply  – Paste a job description → AI analyses it, picks the best resume, drafts a personalised email.
                 Toggle "Auto Send" to send the email automatically via connected Gmail/Outlook.
                 Otherwise review and send the draft manually.
4. Email       – Connect Gmail (Google OAuth) or Outlook (Microsoft OAuth) for sending applications.
5. History     – Full application history: role, company, date/time, resume used, match score, email sent.
                 Click "View Email" on any card to see the full subject + body of what was sent.
6. Chatbot     – You are here! Ask anything about your resumes, job descriptions, application history, or the portal.
                 You can also upload a JD PDF to compare it against your resumes.

HOW AUTO APPLY WORKS:
  1. Paste job description text into the text area.
  2. The AI extracts: company, role, required skills, recruiter email.
  3. Your uploaded resumes are ranked by semantic similarity to the JD.
  4. A personalised cover email is generated using the best-matching resume.
  5. If "Auto Send" is on and an email provider is connected, the email is sent immediately.
  6. The application is saved to History with all details.

SUPPORTED EMAIL PROVIDERS:
  - Gmail via Google OAuth (no password needed — just click "Connect Google").
  - Outlook/Hotmail via Microsoft OAuth.
"""


# ---------------------------------------------------------------------------
# Core chat function
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are a helpful AI assistant embedded inside the AI Job Agent portal.
You have access to the user's resume content, any uploaded job description, 
application history statistics, and knowledge of how the portal works.

Always answer in a clear, concise, and friendly tone.
When referencing resume or JD content, cite which document it came from.
When asked about stats or history, use the provided statistics context.
If you do not know something, say so honestly.
"""


def chat(
    user_id: int,
    question: str,
    history: List[Dict[str, str]],
    resumes_dir: Path,
    jd_pdf_path: Optional[Path] = None,
) -> str:
    """
    Answer a question using RAG over resumes / JD + stats context.

    Args:
        user_id:     Authenticated user's ID.
        question:    The user's latest message.
        history:     List of {"role": "user"/"assistant", "content": "..."} dicts.
        resumes_dir: Path to the user's resume PDFs.
        jd_pdf_path: Optional path to an uploaded JD PDF for this session.

    Returns:
        Assistant reply string.
    """
    llm = get_llm()

    # ── 1. Retrieve relevant document chunks ──────────────────────────────
    rag_context = ""
    pdf_files = list(resumes_dir.glob("*.pdf")) if resumes_dir.exists() else []
    has_jd = jd_pdf_path and jd_pdf_path.exists()

    if pdf_files or has_jd:
        try:
            vs = get_or_build_vs(user_id, resumes_dir, jd_pdf_path if has_jd else None)
            docs = vs.similarity_search(question, k=5)
            chunks = []
            for d in docs:
                src = d.metadata.get("source", "unknown")
                chunks.append(f"[Source: {src}]\n{d.page_content}")
            rag_context = "\n\n---\n\n".join(chunks)
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            rag_context = "Could not retrieve document context."
    else:
        rag_context = "No resumes uploaded yet."

    # ── 2. Portal stats ───────────────────────────────────────────────────
    stats_context = _get_stats_context(user_id)

    # ── 3. Build conversation string ──────────────────────────────────────
    conv_lines = []
    for msg in history[-6:]:   # keep last 6 turns for context window
        role = "User" if msg["role"] == "user" else "Assistant"
        conv_lines.append(f"{role}: {msg['content']}")
    conversation = "\n".join(conv_lines)

    # ── 4. Compose final prompt ───────────────────────────────────────────
    prompt = f"""{SYSTEM_PROMPT}

=== DOCUMENT CONTEXT (retrieved from resumes / JD) ===
{rag_context}

=== APPLICATION STATISTICS & HISTORY ===
{stats_context}

=== PORTAL GUIDE ===
{_PORTAL_GUIDE}

=== CONVERSATION HISTORY ===
{conversation}

User: {question}
Assistant:"""

    response = llm.invoke(prompt)
    return response.content.strip()
