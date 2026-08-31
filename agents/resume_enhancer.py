"""
Resume enhancer module.

Automatically adds missing skills to resume based on job description analysis.
"""

from langchain.prompts import PromptTemplate
from services.llm_service import get_llm
from utils.logger import get_logger
import os
from typing import List

logger = get_logger(__name__)
llm = get_llm()

enhancement_prompt = PromptTemplate.from_template("""
You are an expert resume writer and career coach specializing in skill enhancement.

ORIGINAL RESUME CONTENT:
{resume_content}

MISSING SKILLS TO ADD:
{missing_skills}

JOB CONTEXT:
Role: {role}
Company: {company}
Required Skills: {skills}

TASK:
Enhance the resume by adding the missing skills in a realistic and professional manner.

RULES:
1. Add missing skills to the most appropriate sections (Skills section, Experience, Projects, etc.)
2. For each missing skill, add a brief, realistic bullet point or description showing how the candidate has this skill
3. Keep the additions realistic and plausible - don't invent entire fake work experiences
4. Add skills in a way that maintains the resume's existing structure and tone
5. If a skill is technical, add it to a technical skills section or relevant project
6. If a skill is soft skill, add it to relevant experience or summary
7. Maintain the original resume's formatting and structure
8. Only add the skills listed in MISSING SKILLS - don't add others
9. Keep the enhanced resume professional and concise
10. Ensure the additions sound natural and not forced

OUTPUT FORMAT:
Return the complete enhanced resume content as plain text.
Maintain the original structure and formatting as much as possible.
Only add the missing skills where they naturally fit.
""")


def enhance_resume(resume_content: str, missing_skills: List[str], role: str, company: str, skills: List[str]) -> str:
    """
    Enhance resume by adding missing skills in a realistic way.
    
    Args:
        resume_content: Original resume content
        missing_skills: List of missing skills to add
        role: Job role from JD
        company: Company name from JD
        skills: All required skills from JD
    
    Returns:
        Enhanced resume content as string
    """
    try:
        if not missing_skills:
            logger.info("No missing skills to add")
            return resume_content
        
        logger.info(f"Enhancing resume with {len(missing_skills)} missing skills")
        
        missing_str = ", ".join(missing_skills)
        skills_str = ", ".join(skills) if skills else "None specified"
        
        prompt = enhancement_prompt.format(
            resume_content=resume_content,
            missing_skills=missing_str,
            role=role,
            company=company,
            skills=skills_str
        )
        
        response = llm.invoke(prompt)
        enhanced_content = response.content.strip()
        
        logger.info("Resume enhanced successfully")
        return enhanced_content
        
    except Exception as e:
        logger.error(f"Error enhancing resume: {e}", exc_info=True)
        # Return original content on error
        return resume_content


def generate_enhanced_resume_text(resume_content: str, gap_analysis, jd_details) -> str:
    """
    Generate enhanced resume text based on gap analysis.
    
    Args:
        resume_content: Original resume content
        gap_analysis: ResumeGapAnalysis object from comparator
        jd_details: JobDetails object
    
    Returns:
        Enhanced resume content
    """
    try:
        # Combine critical and optional missing skills
        missing_skills = []
        
        if hasattr(gap_analysis, 'critical_missing_skills') and gap_analysis.critical_missing_skills:
            missing_skills.extend(gap_analysis.critical_missing_skills)
        
        if hasattr(gap_analysis, 'optional_missing_skills') and gap_analysis.optional_missing_skills:
            missing_skills.extend(gap_analysis.optional_missing_skills)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_missing_skills = []
        for skill in missing_skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_missing_skills.append(skill)
        
        logger.info(f"Enhancing resume with {len(unique_missing_skills)} unique missing skills")
        
        enhanced_content = enhance_resume(
            resume_content=resume_content,
            missing_skills=unique_missing_skills,
            role=jd_details.role,
            company=jd_details.company,
            skills=jd_details.skills if jd_details.skills else []
        )
        
        return enhanced_content
        
    except Exception as e:
        logger.error(f"Error generating enhanced resume: {e}", exc_info=True)
        return resume_content
