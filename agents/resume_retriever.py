"""
Resume retriever module.

Finds the best matching resume for a job using vector similarity search.
"""

from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from services.llm_service import get_llm
from utils.logger import get_logger
from utils.exceptions import ResumeRetrievalError

logger = get_logger(__name__)


def retrieve_best_matches(vector_store, query, k=3):
    """Retrieve best matching resume chunks from vector store."""
    results = vector_store.similarity_search(query, k=k)
    
    # Group results by resume file
    resume_groups = defaultdict(list)
    for doc in results:
        source = doc.metadata.get("source", "Unknown")
        resume_groups[source].append(doc)
    
    # Return grouped results with their source
    return resume_groups


def find_best_resume(job_details: Dict, resumes_dir: str = None) -> Dict:
    """
    Find the best matching resume for a job description using improved scoring.

    Args:
        job_details: Dictionary containing job information (company, role, skills, etc.)
        resumes_dir: Optional path to directory containing PDF resumes.
                     Falls back to Config.RESUME_DIR if not provided.

    Returns:
        Dictionary with resume filename, match score, and content

    Raises:
        ResumeRetrievalError: If resume retrieval fails
    """
    try:
        logger.info(f"Finding best resume for {job_details.get('role')} at {job_details.get('company')}")

        from agents.resume_splitter import split_documents
        from agents.vector_store import create_vector_store
        from langchain_community.document_loaders import PyPDFLoader
        from config.settings import Config

        # Determine which directory to scan
        scan_dir = Path(resumes_dir) if resumes_dir else Config.RESUME_DIR
        scan_dir.mkdir(parents=True, exist_ok=True)

        pdf_files = list(scan_dir.glob("*.pdf"))
        if not pdf_files:
            raise ResumeRetrievalError(f"No PDF resumes found in {scan_dir}")

        # Load all PDFs directly (bypasses Config.RESUME_DIR)
        documents = []
        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Loaded {pdf_path.name}")
            except Exception as load_err:
                logger.warning(f"Could not load {pdf_path.name}: {load_err}")

        if not documents:
            raise ResumeRetrievalError("Could not extract text from any resume PDF")

        # Split documents into chunks
        splits = split_documents(documents)

        # Create vector store
        vector_store = create_vector_store(splits)

        # Build improved search query with more context
        skills_str = " ".join(job_details.get("skills", []))
        role = job_details.get('role', '')
        company = job_details.get('company', '')
        keywords_str = " ".join(job_details.get("keywords", []))
        
        # Build a more comprehensive query
        query_parts = [role, company, skills_str, keywords_str]
        query = " ".join([part for part in query_parts if part])

        # Retrieve matches
        matches = retrieve_best_matches(vector_store, query, k=5)

        if not matches:
            # Fall back to first PDF if vector search returns nothing
            best_pdf = pdf_files[0]
            loader = PyPDFLoader(str(best_pdf))
            content = "\n".join(p.page_content for p in loader.load())
            return {
                "filename": best_pdf.name,
                "score": 0.5,
                "resume_file": str(best_pdf),
                "resume_content": content,
            }

        # Improved scoring algorithm
        best_match_path = None
        best_score = 0.0
        jd_skills = job_details.get("skills", [])
        jd_keywords = job_details.get("keywords", [])
        jd_role = job_details.get('role', '').lower()

        for source_path, docs in matches.items():
            # Base score from vector similarity (document count)
            base_score = len(docs) / max(len(splits), 1)
            
            # Skill matching score
            skill_score = 0.0
            matched_skills = []
            
            # Combine all document content for skill analysis
            full_content = " ".join(doc.page_content.lower() for doc in docs)
            
            for skill in jd_skills:
                skill_lower = skill.lower()
                if skill_lower in full_content:
                    # Weight skill matches based on importance
                    skill_score += 0.15  # Each matched skill adds 15%
                    matched_skills.append(skill)
                    
                    # Bonus for exact phrase matches
                    if skill_lower in full_content and len(skill_lower) > 3:
                        skill_score += 0.05
            
            # Keyword matching score
            keyword_score = 0.0
            for keyword in jd_keywords:
                if keyword.lower() in full_content:
                    keyword_score += 0.08  # Each matched keyword adds 8%
            
            # Role matching bonus
            role_score = 0.0
            if jd_role and jd_role in full_content:
                role_score += 0.2  # 20% bonus for role match
            
            # Experience matching (if mentioned in JD)
            experience_score = 0.0
            jd_experience = job_details.get('experience', '').lower()
            if jd_experience and any(exp in full_content for exp in ['year', 'experience', 'internship', 'fresher']):
                experience_score += 0.1
            
            # Calculate final weighted score
            # Base: 40%, Skills: 30%, Keywords: 15%, Role: 10%, Experience: 5%
            final_score = (
                base_score * 0.4 +
                skill_score * 0.3 +
                keyword_score * 0.15 +
                role_score * 0.1 +
                experience_score * 0.05
            )
            
            # Cap the score at 1.0
            final_score = min(final_score, 1.0)
            
            logger.debug(f"Resume {Path(source_path).name}: base={base_score:.2f}, skills={skill_score:.2f}, keywords={keyword_score:.2f}, role={role_score:.2f}, exp={experience_score:.2f}, final={final_score:.2f}")
            
            if final_score > best_score:
                best_score = final_score
                best_match_path = source_path

        # Extract full text from best resume
        best_pdf_path = Path(best_match_path)
        if best_pdf_path.exists():
            loader = PyPDFLoader(str(best_pdf_path))
            resume_content = "\n".join(p.page_content for p in loader.load())
            filename = best_pdf_path.name
        else:
            resume_content = "\n".join(
                doc.page_content for doc in matches.get(best_match_path, [])
            )
            filename = Path(best_match_path).name

        logger.info(f"Best match: {filename} (score={best_score:.2f})")

        # Generate match analysis for feedback
        match_analysis = {
            "matched_skills": matched_skills[:10] if 'matched_skills' in locals() else [],
            "score_breakdown": {
                "base_score": base_score if 'base_score' in locals() else 0,
                "skill_score": skill_score if 'skill_score' in locals() else 0,
                "keyword_score": keyword_score if 'keyword_score' in locals() else 0,
                "role_score": role_score if 'role_score' in locals() else 0,
                "experience_score": experience_score if 'experience_score' in locals() else 0
            }
        }

        return {
            "filename": filename,
            "score": best_score,
            "resume_file": str(best_match_path),
            "resume_content": resume_content,
            "match_analysis": match_analysis
        }

    except ResumeRetrievalError:
        raise
    except Exception as e:
        logger.error(f"Error finding best resume: {e}", exc_info=True)
        raise ResumeRetrievalError(f"Failed to find best resume: {str(e)}")