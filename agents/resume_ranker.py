"""
Resume ranker module.

Ranks resumes based on semantic relevance and skill matching using weighted scoring.
Implements proper 0-100 normalization with weighted scoring.
"""

from collections import defaultdict
from typing import List, Dict, Tuple
from config.settings import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_skill_match_score(jd_skills: List[str], resume_text: str) -> Tuple[float, List[str], List[str]]:
    """
    Calculate skill match score between JD skills and resume.
    
    Args:
        jd_skills: List of skills from job description
        resume_text: Full resume text
    
    Returns:
        Tuple of (match_score, matched_skills, missing_skills)
    """
    if not jd_skills:
        return 0.0, [], []
    
    # Normalize skills to lowercase for comparison
    jd_skills_normalized = [skill.lower().strip() for skill in jd_skills]
    resume_text_lower = resume_text.lower()
    
    # Remove duplicates from JD skills
    jd_skills_unique = list(set(jd_skills_normalized))
    
    matched_skills = []
    missing_skills = []
    
    for skill in jd_skills_unique:
        if skill in resume_text_lower:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)
    
    # Calculate match score (0-100)
    if jd_skills_unique:
        match_score = (len(matched_skills) / len(jd_skills_unique)) * 100
    else:
        match_score = 0.0
    
    return match_score, matched_skills, missing_skills


def rank_resumes(resume_groups: Dict[str, List], jd_skills: List[str] = None, 
                jd_experience: str = None) -> List[Tuple[str, float, Dict]]:
    """
    Rank resumes based on weighted scoring with proper 0-100 normalization.
    
    Scoring Weights:
    - Must-have skills: 50%
    - Preferred skills: 20%
    - Experience relevance: 15%
    - Projects relevance: 15%
    
    Args:
        resume_groups: Dict mapping resume paths to list of document chunks
        jd_skills: List of skills from job description (optional)
        jd_experience: Experience required from JD (optional)
    
    Returns:
        List of tuples (resume_path, score, details) sorted by score descending
        details dict contains: matched_skills, missing_skills, skill_score, experience_score, project_score
    """
    resume_scores = []
    
    for resume_path, chunks in resume_groups.items():
        # Combine chunks into full resume text
        resume_text = " ".join([chunk.page_content for chunk in chunks])
        resume_text_lower = resume_text.lower()
        
        # 1. Skill Matching Score (50% weight)
        skill_score, matched_skills, missing_skills = calculate_skill_match_score(jd_skills, resume_text)
        
        # 2. Experience Relevance Score (15% weight)
        experience_score = 0.0
        if jd_experience:
            # Simple heuristic: check if experience keywords match
            exp_keywords = {
                'entry': ['0-1', '0-2', 'fresh', 'junior', 'entry'],
                'mid': ['2-5', '3-5', 'mid', 'intermediate'],
                'senior': ['5+', '5-10', 'senior', 'lead', 'principal'],
                'expert': ['10+', 'expert', 'staff', 'architect']
            }
            
            jd_exp_lower = jd_experience.lower()
            for level, keywords in exp_keywords.items():
                if any(kw in jd_exp_lower for kw in keywords):
                    # Check if resume has similar experience level
                    if any(kw in resume_text_lower for kw in keywords):
                        experience_score = 15.0
                    break
        
        # 3. Projects Relevance Score (15% weight)
        project_score = 0.0
        if jd_skills:
            # Count how many JD skills appear in project-related sections
            project_keywords = ['project', 'built', 'developed', 'created', 'implemented', 'launched']
            project_sections = []
            
            for chunk in chunks:
                chunk_lower = chunk.page_content.lower()
                if any(pk in chunk_lower for pk in project_keywords):
                    project_sections.append(chunk.page_content)
            
            if project_sections:
                project_text = ' '.join(project_sections).lower()
                project_matches = sum(1 for skill in jd_skills if skill.lower() in project_text)
                if jd_skills:
                    project_score = (project_matches / len(jd_skills)) * 15
        
        # 4. Semantic Relevance Score (20% weight - from chunk count)
        # Normalize chunk count to 0-20 range
        chunk_count = len(chunks)
        semantic_score = min(chunk_count * 2, 20.0)  # Cap at 20
        
        # Calculate final weighted score (0-100)
        final_score = (
            (skill_score * 0.50) +      # 50% weight
            (semantic_score * 0.20) +    # 20% weight  
            (experience_score * 0.15) +  # 15% weight
            (project_score * 0.15)       # 15% weight
        )
        
        # Ensure score is within 0-100
        final_score = max(0.0, min(100.0, final_score))
        
        details = {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'skill_score': skill_score,
            'experience_score': experience_score,
            'project_score': project_score,
            'semantic_score': semantic_score
        }
        
        resume_scores.append((resume_path, final_score, details))
        
        logger.debug(f"Resume {resume_path}: Score={final_score:.2f}, Skills={skill_score:.2f}, Exp={experience_score:.2f}, Proj={project_score:.2f}")
    
    # Sort by score descending
    ranked_resumes = sorted(resume_scores, key=lambda x: x[1], reverse=True)
    
    logger.info(f"Ranked {len(ranked_resumes)} resumes")
    return ranked_resumes