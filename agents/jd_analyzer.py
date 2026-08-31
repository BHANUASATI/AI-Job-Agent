"""
Job description analyzer module.

Extracts structured information from job descriptions using LLM.
"""

import re  # top-level import — must be here before any try/except uses it

from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from services.llm_service import get_llm
from utils.logger import get_logger
from utils.exceptions import JDAnalysisError

logger = get_logger(__name__)
llm = get_llm()


class JobDetails(BaseModel):
    company: str
    role: str
    skills: List[str]
    experience: str
    email: str
    location: Optional[str] = None
    keywords: Optional[List[str]] = None
    suggested_subject: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


parser = PydanticOutputParser(pydantic_object=JobDetails)

jd_prompt = PromptTemplate.from_template("""
You are an expert job description analyzer with deep experience in parsing technical job postings.

TASK: Extract structured information from the job description below.

REQUIRED FIELDS:
1. Company Name - The company hiring (extract from text or use "Unknown" if not found)
2. Job Role - The specific position title (e.g., "Senior Software Engineer", "Data Scientist")
3. Required Skills - List of technical and soft skills required (as a list)
4. Experience Required - Experience level or years required (e.g., "3-5 years", "Senior level")
5. Recruiter Email - Contact email for applications (extract email address or use empty string)
6. Location - Job location (city, remote, hybrid, or "Not specified")
7. Important Keywords - Key terms, technologies, or concepts mentioned (as a list)
8. Suggested Subject - If the JD mentions a specific email subject line, extract it exactly; otherwise create a professional subject line

CRITICAL RULES:
- Return ONLY valid JSON - no markdown, no code blocks, no explanation
- Skills should be individual items in a list (e.g., ["Python", "AWS", "Machine Learning"])
- Extract the most specific and relevant skills mentioned
- If a field is not found in the JD, use a sensible default (empty string, empty list, or "Not specified")
- Email should be a valid email format or empty string
- Keywords should be relevant to the role and technology stack
- Company name should be the actual company, not "we" or "our company"
- Role should be the specific job title, not generic terms
- For suggested subject: look for phrases like "Suggested Email Subject", "Subject Line", "Application Subject" and use that exact text
- If no subject is mentioned, create a professional one like "Application for [Role] – [Your Name]"

{format_instructions}

JOB DESCRIPTION:
{job_description}
""")


def analyze_jd(job_description):
    """
    Analyze job description and extract structured information.
    
    Args:
        job_description: Raw job description text
        
    Returns:
        JobDetails object with extracted information
        
    Raises:
        JDAnalysisError: If analysis fails
    """
    if not job_description or not job_description.strip():
        raise JDAnalysisError("Job description cannot be empty")
    
    try:
        logger.info("Starting job description analysis")
        
        prompt = jd_prompt.format(
            job_description=job_description,
            format_instructions=parser.get_format_instructions()
        )

        response = llm.invoke(prompt)
        raw_output = response.content.strip()

        logger.debug(f"Raw LLM output: {raw_output[:200]}...")

        # Remove markdown if present
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()

        parsed_output = parser.parse(raw_output)
        
        # Validate and clean the output
        if not parsed_output.company or parsed_output.company == "Unknown":
            # Try to extract company from first few lines
            lines = job_description.split("\n")[:5]
            for line in lines:
                if "at " in line.lower() and len(line) < 100:
                    possible_company = line.split("at")[-1].strip()
                    if possible_company and len(possible_company) < 50:
                        parsed_output.company = possible_company
                        break
        
        if not parsed_output.skills:
            # Try to extract skills using common patterns
            skill_patterns = [
                r'(?:skills|technologies|requirements|stack)[:\s]*([^.]+)',
                r'(?:proficient|experience|knowledge)\s+(?:in|with|of)\s+([^.]+)'
            ]
            extracted_skills = []
            for pattern in skill_patterns:
                matches = re.findall(pattern, job_description, re.IGNORECASE)
                for match in matches:
                    # Split by common delimiters and clean
                    skills = [s.strip() for s in re.split(r'[,;\/]', match) if s.strip()]
                    extracted_skills.extend(skills[:5])  # Limit to avoid noise
            if extracted_skills:
                parsed_output.skills = list(set(extracted_skills[:10]))  # Dedupe and limit
        
        logger.info(f"Successfully analyzed JD for {parsed_output.company} - {parsed_output.role}")
        return parsed_output

    except Exception as e:
        logger.error(f"Error analyzing JD: {e}", exc_info=True)
        
        # Enhanced regex fallback with better extraction
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', job_description)
        email = email_match.group(0) if email_match else ""

        company = "Unknown"
        role = "Unknown"
        location = "Not specified"
        experience = "Not specified"
        suggested_subject = None

        # Try to extract suggested subject
        subject_patterns = [
            r'(?:suggested\s+email\s+subject|subject\s+line|application\s+subject)[:\s]*([^\n]+)',
            r'(?:email\s+subject)[:\s]*([^\n]+)'
        ]
        for pattern in subject_patterns:
            subject_match = re.search(pattern, job_description, re.IGNORECASE)
            if subject_match:
                suggested_subject = subject_match.group(1).strip()
                break

        # Try to extract structured information with better patterns
        lines = job_description.split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            line_stripped = line.strip()
            
            # Company extraction - improved patterns
            if any(term in line_lower for term in ["company:", "organization:", "employer:", "company name:"]):
                company = line_stripped.split(":", 1)[-1].strip()
            elif " at " in line_lower and len(line_stripped) < 100 and company == "Unknown":
                # Extract company from phrases like "position at company"
                parts = line_stripped.split(" at ")
                if len(parts) > 1:
                    potential_company = parts[-1].strip()
                    if len(potential_company) < 50 and potential_company not in ["the", "a", "an", "unknown"]:
                        company = potential_company
            
            # Role extraction - significantly improved for messy PDFs
            elif any(term in line_lower for term in ["job title:", "role:", "position:", "designation:", "job role:"]):
                role = line_stripped.split(":", 1)[-1].strip()
            elif any(term in line_lower for term in ["engineer", "developer", "manager", "analyst", "scientist", "architect", "consultant", "specialist"]) and len(line_stripped) < 100 and role == "Unknown":
                # Try to extract role from first meaningful line
                if i < 10:  # Check first 10 lines for role
                    potential_role = line_stripped
                    # Clean up messy role text
                    if "|" in potential_role:
                        potential_role = potential_role.split("|")[0].strip()
                    # Remove common junk from beginning
                    for junk in ["job description", "role", "position", "title", "job role:", "position:", "job title:"]:
                        if potential_role.lower().startswith(junk):
                            potential_role = potential_role[len(junk):].strip()
                    # Remove common patterns from PDF artifacts
                    for junk in ["opportunity", "employment", "experience", "years", "full-time", "part-time", "contract"]:
                        if potential_role.lower().startswith(junk):
                            potential_role = potential_role[len(junk):].strip()
                    if len(potential_role) < 60 and potential_role and len(potential_role) > 3:
                        role = potential_role.title()
            
            # Location extraction
            elif "location:" in line_lower:
                location = line_stripped.split(":", 1)[-1].strip()
            elif any(term in line_lower for term in ["remote", "hybrid", "on-site", "onsite", "location:"]) and location == "Not specified":
                location = line_stripped.strip()
            
            # Experience extraction - improved patterns
            elif "experience:" in line_lower:
                experience = line_stripped.split(":", 1)[-1].strip()
            elif any(term in line_lower for term in ["years", "fresher", "entry", "senior", "mid", "lead", "0-2", "1-3", "2-5", "5+"]) and experience == "Not specified":
                # Only use if it's a short, meaningful experience description
                if len(line_stripped) < 60:
                    experience = line_stripped.strip()
            
            # Subject line extraction - for JD-suggested subjects
            elif any(term in line_lower for term in ["subject:", "suggested email subject:", "email subject:", "application subject:"]):
                # Extract subject line from JD - stop at period or newline
                potential_subject = line_stripped.split(":", 1)[-1].strip()
                # Stop at first period to avoid capturing instructions
                if '.' in potential_subject:
                    potential_subject = potential_subject.split('.')[0].strip()
                # Remove common prefix words that might be captured
                for prefix in ["line", "format", "should be", "application"]:
                    if potential_subject.lower().startswith(prefix):
                        potential_subject = potential_subject[len(prefix):].strip()
                # Remove any quotes around the subject
                potential_subject = potential_subject.strip('"\'')
                if len(potential_subject) < 150 and potential_subject:
                    suggested_subject = potential_subject

        # Extract skills using enhanced keyword matching with more AI-relevant terms
        ai_ml_skills = [
            "python", "java", "javascript", "react", "node", "angular", "vue", 
            "aws", "azure", "gcp", "docker", "kubernetes", "sql", "nosql", 
            "machine learning", "data science", "devops", "agile", "scrum",
            "tensorflow", "pytorch", "llm", "nlp", "generative ai", "rag",
            "langchain", "openai", "hugging face", "git", "github", "ci/cd",
            "fastapi", "flask", "django", "rest apis", "vector databases",
            "chroma", "faiss", "pinecone", "weaviate", "milvus",
            "prompt engineering", "embeddings", "transformers", "deep learning",
            "neural networks", "supervised learning", "unsupervised learning",
            "feature engineering", "model evaluation", "data preprocessing",
            "natural language processing", "computer vision", "big data",
            "spark", "hadoop", "kafka", "airflow", "microservices", "testing"
        ]
        found_skills = []
        jd_lower = job_description.lower()
        for skill in ai_ml_skills:
            if skill in jd_lower:
                found_skills.append(skill.title())
        
        # If still no skills found, try broader tech terms
        if not found_skills:
            broader_skills = ["programming", "development", "coding", "software", "technology", "analytics", "database", "cloud", "web", "mobile"]
            for skill in broader_skills:
                if skill in jd_lower:
                    found_skills.append(skill.title())

        # Clean up company and role if they're too long or contain too much text
        if len(company) > 50:
            company = "Unknown"
        if len(role) > 50:
            # Try to extract just the role part
            if "|" in role:
                role = role.split("|")[0].strip()
            # If still too long or contains junk, extract role from text
            if len(role) > 30 or "job description" in role.lower():
                # Look for actual role keywords
                role_keywords = ["engineer", "developer", "manager", "analyst", "scientist", "architect", "consultant", "specialist"]
                for keyword in role_keywords:
                    if keyword in role.lower():
                        # Extract a reasonable context around the keyword
                        words = role.split()
                        for i, word in enumerate(words):
                            if keyword in word.lower():
                                # Get surrounding words for context
                                start = max(0, i - 2)
                                end = min(len(words), i + 3)
                                potential_role = " ".join(words[start:end])
                                if len(potential_role) < 40:
                                    role = potential_role
                                    break
                        if len(role) < 30:
                            break
            if len(role) > 50:
                role = "Unknown"

        logger.warning(f"Using fallback parsing for JD: {company} - {role}")
        
        return JobDetails(
            company=company,
            role=role,
            skills=found_skills,
            experience=experience,
            email=email,
            location=location,
            keywords=found_skills[:5],
            suggested_subject=suggested_subject
        )