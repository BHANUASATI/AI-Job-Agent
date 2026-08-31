from agents.resume_retriever import retrieve_best_matches
from agents.resume_ranker import rank_resumes
from typing import List, Dict, Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


def compare_all_resumes(vector_store, query, jd_skills=None, jd_experience=None, k=10) -> List[Dict]:
    """
    Compare ALL available resumes against the job description.
    
    Args:
        vector_store: FAISS vector store
        query: Search query string
        jd_skills: List of skills from job description (optional)
        jd_experience: Experience required from JD (optional)
        k: Number of results to retrieve
    
    Returns:
        List of dicts with resume comparison results:
        [
            {
                'resume_path': str,
                'resume_name': str,
                'score': float,
                'matched_skills': List[str],
                'missing_skills': List[str],
                'matched_count': int,
                'missing_count': int,
                'details': Dict
            },
            ...
        ]
    """
    # Retrieve grouped results
    resume_groups = retrieve_best_matches(vector_store, query, k=k)
    
    if not resume_groups:
        logger.warning("No resumes found for comparison")
        return []
    
    # Rank resumes with detailed scoring
    ranked_resumes = rank_resumes(resume_groups, jd_skills, jd_experience)
    
    # Build comparison results
    comparison_results = []
    for resume_path, score, details in ranked_resumes:
        resume_name = resume_path.split('/')[-1] if '/' in resume_path else resume_path
        
        comparison_results.append({
            'resume_path': resume_path,
            'resume_name': resume_name,
            'score': score,
            'matched_skills': details.get('matched_skills', []),
            'missing_skills': details.get('missing_skills', []),
            'matched_count': len(details.get('matched_skills', [])),
            'missing_count': len(details.get('missing_skills', [])),
            'details': details
        })
    
    logger.info(f"Compared {len(comparison_results)} resumes against JD")
    return comparison_results


def select_best_resume(vector_store, query, jd_skills=None, jd_experience=None, k=3) -> Tuple[Optional[str], Optional[str], float]:
    """
    Select the best matching resume for a job description.
    
    Args:
        vector_store: FAISS vector store
        query: Search query string
        jd_skills: List of skills from job description (optional)
        jd_experience: Experience required from JD (optional)
        k: Number of results to retrieve
    
    Returns:
        Tuple (best_resume_path, resume_content, score)
    """
    # Retrieve grouped results
    resume_groups = retrieve_best_matches(vector_store, query, k=k)
    
    if not resume_groups:
        logger.warning("No resumes found for selection")
        return None, None, 0.0
    
    # Rank resumes
    ranked_resumes = rank_resumes(resume_groups, jd_skills, jd_experience)
    
    if not ranked_resumes:
        logger.warning("No resumes ranked")
        return None, None, 0.0
    
    # Get best resume
    best_resume_path, score, details = ranked_resumes[0]
    best_chunks = resume_groups[best_resume_path]
    
    # Combine chunks into full content
    resume_content = "\n\n".join([chunk.page_content for chunk in best_chunks])
    
    logger.info(f"Selected best resume: {best_resume_path} with score {score:.2f}")
    return best_resume_path, resume_content, score