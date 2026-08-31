from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from services.llm_service import get_llm
from utils.logger import get_logger

logger = get_logger(__name__)
llm = get_llm()


class ResumeGapAnalysis(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    critical_missing_skills: List[str]  # Must-have skills missing
    optional_missing_skills: List[str]  # Good-to-have skills missing
    missing_keywords: List[str]
    suggested_projects: List[str]
    match_score: float
    strengths: List[str]
    weaknesses: List[str]
    strong_areas: List[str]  # Areas where candidate excels
    weak_areas: List[str]  # Areas needing improvement

    model_config = ConfigDict(arbitrary_types_allowed=True)


parser = PydanticOutputParser(pydantic_object=ResumeGapAnalysis)

comparison_prompt = PromptTemplate.from_template("""
You are an expert resume analyzer comparing a job description with a candidate's resume.

JOB DESCRIPTION:
Role: {role}
Company: {company}
Required Skills: {skills}
Experience Required: {experience}
Keywords: {keywords}

RESUME CONTENT:
{resume_content}

Analyze and provide:
1. Matched Skills - Skills present in both JD and resume
2. Missing Skills - All skills required in JD but not found in resume
3. Critical Missing Skills - Must-have skills that are missing (high priority)
4. Optional Missing Skills - Good-to-have skills that are missing (lower priority)
5. Missing Keywords - Important keywords from JD not in resume
6. Suggested Projects - Project ideas that would strengthen the resume for this role
7. Match Score - A score from 0.0 to 1.0 indicating how well the resume matches the JD
8. Strengths - What makes this candidate a good fit
9. Weaknesses - What gaps need to be addressed
10. Strong Areas - Technical or professional areas where candidate excels
11. Weak Areas - Technical or professional areas needing improvement

CRITICAL RULES:
- Only identify skills/keywords that are TRULY missing - verify by checking resume content thoroughly
- Be realistic about project suggestions - suggest achievable, relevant projects
- Match score must be based on ACTUAL skill overlap, experience level, and relevance
- Categorize missing skills: Critical = core requirements, Optional = nice-to-have
- Never hallucinate - base EVERYTHING on the provided content only
- If a skill appears in resume in any form (acronym, full name, related term), it's NOT missing
- Strong areas should be specific technical domains or competencies
- Weak areas should be actionable improvement areas

Return ONLY valid JSON. No markdown, no explanation.

{format_instructions}
""")


def compare_jd_resume(jd_details, resume_content):
    """
    Compare job description with resume to identify gaps with categorization.
    
    Args:
        jd_details: JobDetails object with company, role, skills, experience, keywords
        resume_content: Full text content of the resume
    
    Returns:
        ResumeGapAnalysis object with detailed gap analysis
    """
    try:
        logger.info(f"Comparing JD for {jd_details.company} - {jd_details.role} against resume")
        
        skills_str = ", ".join(jd_details.skills) if jd_details.skills else "None specified"
        keywords_str = ", ".join(jd_details.keywords) if jd_details.keywords else "None specified"
        
        prompt = comparison_prompt.format(
            role=jd_details.role,
            company=jd_details.company,
            skills=skills_str,
            experience=jd_details.experience,
            keywords=keywords_str,
            resume_content=resume_content,
            format_instructions=parser.get_format_instructions()
        )
        
        response = llm.invoke(prompt)
        raw_output = response.content.strip()
        
        # Clean up markdown if present
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()
        
        parsed_output = parser.parse(raw_output)
        
        logger.info(f"Gap analysis completed. Match score: {parsed_output.match_score:.2f}")
        return parsed_output
        
    except Exception as e:
        logger.error(f"Error comparing JD and resume: {e}", exc_info=True)
        
        # Fallback: Perform basic keyword matching
        resume_lower = resume_content.lower()
        matched_skills = []
        missing_skills = []
        
        if jd_details.skills:
            for skill in jd_details.skills:
                if skill.lower() in resume_lower:
                    matched_skills.append(skill)
                else:
                    missing_skills.append(skill)
        
        # Calculate basic match score
        if jd_details.skills:
            basic_score = len(matched_skills) / len(jd_details.skills)
        else:
            basic_score = 0.5
        
        logger.warning(f"Using fallback gap analysis. Basic score: {basic_score:.2f}")
        
        return ResumeGapAnalysis(
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            critical_missing_skills=missing_skills[:3] if missing_skills else [],
            optional_missing_skills=missing_skills[3:] if len(missing_skills) > 3 else [],
            missing_keywords=[],
            suggested_projects=[],
            match_score=basic_score,
            strengths=["Basic analysis performed due to LLM error"],
            weaknesses=["Full analysis unavailable"],
            strong_areas=[],
            weak_areas=[]
        )
