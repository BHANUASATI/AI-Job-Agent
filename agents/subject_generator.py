"""
Subject line generator module.

Generates professional, attention-grabbing email subject lines for job applications.
"""

from langchain.prompts import PromptTemplate
from services.llm_service import get_llm
from utils.logger import get_logger
from utils.exceptions import EmailGenerationError

logger = get_logger(__name__)
llm = get_llm()

subject_prompt = PromptTemplate.from_template("""
You are an expert in writing email subject lines that get opened by HR professionals and hiring managers.

CANDIDATE INFORMATION:
Name: {candidate_name}
Key Strengths: {candidate_strengths}

JOB DETAILS:
Company: {company}
Role: {role}

INSTRUCTIONS:
Generate a professional, compelling email subject line that:

1. **Clarity**: Clearly states the purpose (job application)
2. **Professionalism**: Uses business-appropriate language
3. **Personalization**: Includes the candidate's name
4. **Relevance**: Mentions the specific role and company when appropriate
5. **Differentiation**: Highlights key strengths or experience level when relevant
6. **Length**: Keep under 70 characters for best mobile display
7. **Format**: Use pipe (|) or dash (-) to separate elements

EXCELLENT EXAMPLES:
- Application for Senior Software Engineer | John Doe
- Full Stack Developer Role at Atlassian | Jane Smith
- Experienced Python Developer - Backend Engineer Application
- Senior Data Scientist Position | Application - Alex Johnson
- Application: ML Engineer at Google - Sarah Williams
- DevOps Engineer Role | 5 Years Experience - Michael Brown

GOOD EXAMPLES:
- Application for Senior Software Engineer | John Doe
- Senior Data Scientist Application - Jane Smith
- Experienced Python Developer | Application - Alex Johnson
- Full Stack Engineer Role | Application - Sarah Williams
- Application: Backend Engineer Position - Michael Brown

BAD EXAMPLES:
- Job Application
- Applying for job
- [Your Name] - Application
- I want this job
- Please hire me
- Resume attached

Generate 3 different subject line options, each on a new line.
Prioritize subjects that include company name and highlight candidate strengths.
Return ONLY the subject lines, no numbering, no explanation.
""")


def generate_subject(candidate_name, company, role, candidate_strengths=None, suggested_subject=None, jd_text=None):
    """
    Generate professional email subject lines for job application.
    
    Args:
        candidate_name: Candidate's full name
        company: Company name
        role: Job role/title
        candidate_strengths: Optional list of candidate strengths for personalization
        suggested_subject: Optional subject line suggested in the JD
        jd_text: Optional full JD text to search for subject line instructions
        
    Returns:
        Best subject line from generated options or suggested subject
        
    Raises:
        EmailGenerationError: If subject generation fails
    """
    try:
        logger.info(f"Generating subject line for {company} - {role}")
        
        if not candidate_name or not role:
            raise EmailGenerationError("Candidate name and role are required for subject generation")
        
        # First, try to extract subject line from JD text if provided
        if jd_text:
            import re
            logger.info(f"Attempting to extract subject from JD text (length: {len(jd_text)})")
            
            # Look for explicit subject line instructions - more comprehensive patterns
            subject_patterns = [
                # Match "Subject: Application for AI Engineer – [Your Name]" (stop at newline or period)
                r'Subject[:\s]+([^\n\.]+)',
                # Match "Suggested Email Subject: Application for AI Engineer – [Your Name]"
                r'(?:Suggested\s+Email\s+Subject|suggested\s+email\s+subject)[:\s]+([^\n\.]+)',
                # Match "subject line should be: Application for AI Engineer – [Your Name]"
                r'(?:subject\s+line\s+should\s+be)[:\s]+([^\n\.]+)',
                # Match "Email Subject: Application for AI Engineer – [Your Name]"
                r'(?:Email\s+Subject|email\s+subject)[:\s]+([^\n\.]+)',
                # Match "Application subject: Application for AI Engineer – [Your Name]"
                r'(?:Application\s+subject|application\s+subject)[:\s]+([^\n\.]+)',
                # Match "Send with subject: Application for AI Engineer – [Your Name]"
                r'(?:Send\s+with\s+subject|send\s+with\s+subject)[:\s]+([^\n\.]+)',
                # Match "Subject line format: Application for AI Engineer – [Your Name]"
                r'(?:Subject\s+line\s+format)[:\s]+([^\n\.]+)',
            ]
            
            for pattern in subject_patterns:
                subject_match = re.search(pattern, jd_text, re.IGNORECASE)
                if subject_match:
                    extracted_subject = subject_match.group(1).strip()
                    logger.info(f"Pattern matched: {pattern}")
                    logger.info(f"Raw extracted subject: {extracted_subject}")
                    
                    # Clean up the extracted subject
                    extracted_subject = extracted_subject.strip('\'"')
                    # Remove any trailing punctuation or extra whitespace
                    extracted_subject = extracted_subject.strip().rstrip('.,;:')
                    # Stop at first period if present (to avoid capturing instructions)
                    if '.' in extracted_subject:
                        extracted_subject = extracted_subject.split('.')[0].strip()
                    
                    # Remove common prefix words that might be captured
                    for prefix in ["line", "format", "should be", "application"]:
                        if extracted_subject.lower().startswith(prefix):
                            extracted_subject = extracted_subject[len(prefix):].strip()
                    
                    # Remove any remaining quotes around the subject
                    extracted_subject = extracted_subject.strip('"\'')
                    
                    # Replace placeholders
                    extracted_subject = extracted_subject.replace("[Your Name]", candidate_name)
                    extracted_subject = extracted_subject.replace("[YourName]", candidate_name)
                    extracted_subject = extracted_subject.replace("[name]", candidate_name)
                    extracted_subject = extracted_subject.replace("[YOUR NAME]", candidate_name)
                    
                    # Ensure it's not empty and reasonable length
                    if len(extracted_subject) <= 150 and extracted_subject:
                        logger.info(f"✓ Extracted subject from JD: {extracted_subject}")
                        return extracted_subject
        
        # If JD has a suggested subject, use it and replace placeholders
        if suggested_subject:
            logger.info(f"Using suggested_subject parameter: {suggested_subject}")
            # Replace common placeholders with candidate name
            final_subject = suggested_subject.replace("[Your Name]", candidate_name)
            final_subject = final_subject.replace("[Your Name]", candidate_name)
            final_subject = final_subject.replace("[YourName]", candidate_name)
            final_subject = final_subject.replace("[name]", candidate_name)
            final_subject = final_subject.replace("[YOUR NAME]", candidate_name)
            
            # Ensure it's not too long
            if len(final_subject) <= 150:
                logger.info(f"✓ Using suggested subject from JD: {final_subject}")
                return final_subject
        
        # Try to use LLM to generate subject if API is available
        try:
            logger.info("Attempting LLM-based subject generation")
            strengths_str = ", ".join(candidate_strengths[:3]) if candidate_strengths else "various technical skills"
            
            prompt = subject_prompt.format(
                candidate_name=candidate_name,
                company=company,
                role=role,
                candidate_strengths=strengths_str
            )

            response = llm.invoke(prompt)
            subjects = response.content.strip().split("\n")
            
            # Clean up and filter subjects
            clean_subjects = []
            for subject in subjects:
                subject = subject.strip()
                # Remove any numbering
                subject = subject.lstrip("0123456789.-) ")
                # Remove placeholders
                subject = subject.replace("[Your Name]", candidate_name)
                # Skip empty or too long subjects
                if subject and len(subject) <= 80:
                    clean_subjects.append(subject)
            
            # Select the best subject (prefer ones with company name and strengths)
            if clean_subjects:
                # Prioritize subjects that include company name
                best_subject = clean_subjects[0]
                for subject in clean_subjects:
                    # Prefer subjects with company name
                    if company.lower() in subject.lower():
                        if len(subject) <= 70:  # Prefer concise subjects
                            best_subject = subject
                            break
                    # Fallback to concise subject
                    elif len(subject) < len(best_subject) and len(subject) <= 70:
                        best_subject = subject
                
                logger.info(f"✓ Generated subject via LLM: {best_subject}")
                return best_subject
        except Exception as llm_err:
            logger.warning(f"LLM subject generation failed: {llm_err}, using fallback")
        
        # Fallback to simple format
        fallback = f"Application for {role} – {candidate_name}"
        logger.info(f"✓ Using fallback subject: {fallback}")
        return fallback
        
    except Exception as e:
        logger.error(f"Error generating subject: {e}", exc_info=True)
        # Fallback to simple format
        fallback = f"Application for {role} – {candidate_name}"
        logger.warning(f"Using fallback subject due to error: {fallback}")
        return fallback