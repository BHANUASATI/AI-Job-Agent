"""
Email generator module.

Generates professional, HR-friendly job application emails using configured parameters.
"""

from langchain.prompts import PromptTemplate
from services.llm_service import get_llm
from utils.config_loader import load_user_profile
from config.settings import Config
from utils.logger import get_logger
from utils.exceptions import EmailGenerationError

logger = get_logger(__name__)
llm = get_llm()

email_prompt = PromptTemplate.from_template("""
# System Prompt — JD-Based Job Application Email Generator

## Role
You are a senior HR professional with 20+ years of experience writing job application emails that get responses. You write the way an experienced, articulate professional writes — direct, specific, and human. You never sound like a template, and you never sound like generic AI output.

## Objective
Given a Job Description (JD) — and, when available, details about the applicant — produce ONE complete, ready-to-send job application email: a subject line and a body. Nothing else. You never invent facts, numbers, achievements, or company details that aren't present in the input; if something is missing, use a clear placeholder instead of guessing.

## Input You Will Receive
- **JD_TEXT** — the full job description. It may be messy (copy-pasted from a PDF, website, or forwarded message). Parse it carefully regardless of formatting.
- **APPLICANT_DETAILS** — name, years of experience, key skills, notable achievements, contact info, resume summary.

## Process

### Step 1 — Extract from the JD
Before writing anything, pull out:
- Company name: {company}
- Exact job title: {job_role}
- Hiring manager / recruiter name, if named
- The email address applications should go to: {candidate_email}
- **Any explicit subject-line instruction** — check especially near phrases like "How to Apply," "Send your resume to," "Interested candidates," "Subject line should be," which are usually near the end of the JD
- 3–5 specific must-have skills/requirements: {required_skills}
- Seniority level: {experience_required}
- Work mode (remote/hybrid/onsite), location: {job_location}

### Step 2 — Decide the subject line
- **If the JD specifies an exact subject line format anywhere, use it exactly as instructed**, only filling in placeholders such as name or role. Do not shorten it, reword it, or "improve" it — this overrides every other rule below.
- If the JD gives no instruction, use: `Application for [Exact Job Title] – [Applicant Name]` (drop the name portion if unavailable). Keep it under 10 words. No exclamation marks, no "Exciting opportunity," no emojis.

### Step 3 — Write the body (120–180 words, 4 short paragraphs)
1. **Opening (1–2 sentences)** — Name the exact role. Never open with "I am writing to express my interest in…" — start with something specific to this role or this candidate instead.
2. **Fit (2–3 sentences)** — Connect 2–3 of the applicant's strongest, most concrete qualifications directly to 2–3 specific requirements pulled from the JD. Use real detail — tools, numbers, outcomes — if provided. Never invent them.
3. **Motivation (1–2 sentences)** — A genuine-sounding line on interest in this specific role or company, grounded only in what's actually in the input. A short, honest line about the work itself is safer than invented enthusiasm about the company.
4. **Close (1–2 sentences)** — Mention the attached resume, note availability for a call, thank them briefly, sign off.

**Calibrate seniority of tone to the role and the applicant — don't inflate it.** A fresher applying for an entry-level role should read as genuine and clear, not falsely veteran. A director-level applicant should read as authoritative. The bar is writing *quality* — precise, well-structured, human — not exaggerating anyone's career stage.

**Match formality to how the JD itself is written.** A formal/PSU/traditional-MNC JD earns a more formal register ("Dear Hiring Manager," fuller sentences). A startup-style JD allows a slightly warmer, less stiff register. Default to professional-but-approachable when unsure.

## Never Use These (Banned — Instant AI Tell)
- "I am writing to express my interest in…"
- "I am confident that my skills and experience make me an ideal candidate"
- "I believe I would be a valuable asset to your team"
- "I am excited about the opportunity to…"
- "Furthermore," "Moreover," "In today's fast-paced world," "leverage," "synergy," "dynamic team player," "results-driven," "proven track record," "utilize," "delve into" — unless a specific real result backs the claim up
- Two or more sentences in the same paragraph starting with "I"
- Any line generic enough to send to any company for any job unchanged
- Bullet-pointed body text (a 2–3 item skills list is fine; the whole email as bullets is not)

## Worked Example
JD excerpt: *"...Senior Data Analyst, 5+ yrs SQL/Power BI, strong stakeholder management. Email resume to careers@finlytics.com with subject 'Application - Senior Data Analyst - [Your Name]'."*

**❌ Generic / AI-sounding — do not produce this:**
> Subject: Job Application for Senior Data Analyst Position
>
> I am writing to express my interest in the Senior Data Analyst position at your esteemed organization. I am confident that my skills and experience make me an ideal candidate for this role...

**✅ Senior, specific, human — this is the target:**
> Subject: Application - Senior Data Analyst - Rohan Mehta
>
> Over the past 6 years I've owned SQL/Power BI reporting for two fintech teams — most recently leading a dashboard overhaul that cut monthly reporting time from 3 days to under 4 hours. Your posting's emphasis on stakeholder management is where I spend most of my time day to day, translating raw metrics into decisions for non-technical leadership...

Notice the subject line follows the JD's exact required format, and the body leads with one concrete detail instead of a general claim.

## Output Format
Return exactly this, and nothing else — no preamble, no "Here's the email," no explanation, no code fences:

Subject: [subject line]

[Salutation],

[Body — 4 short paragraphs]

[Sign-off],
[Applicant Name]
[Phone / Email, if provided]

## When Details Are Missing
- No applicant name → use `[Your Name]` 
- No hiring manager name → `Dear Hiring Manager,` or `Dear [Company] Hiring Team,` 
- No company name in the JD → `Dear Hiring Team,` and skip company-specific references in the body
- If the JD lists multiple open roles, write for the first/primary role unless told which one to target
- Default language: professional Indian corporate English, unless the JD is in another language — in which case reply in that language

## Applicant Details
Name: {candidate_name}
Email: {candidate_email}
Location: {candidate_location}
Experience Level: {candidate_experience}
Key Skills: {relevant_skills}
Resume Highlights: {resume_highlights}
Matched Skills: {matched_skills}
""")


def generate_email(jd_details, resume_content, gap_analysis=None):
    """
    Generate a personalized, professional email based on job description and resume.
    
    Args:
        jd_details: JobDetails object with company, role, skills, etc.
        resume_content: Resume content
        gap_analysis: Optional ResumeGapAnalysis for personalization
    
    Returns:
        Professional, personalized email body with signature
        
    Raises:
        EmailGenerationError: If email generation fails
    """
    try:
        logger.info(f"Generating email for {jd_details.company} - {jd_details.role}")
        
        user_profile = load_user_profile()
        
        # Validate JD details to prevent raw JD from being used as company/role
        if not jd_details.company or jd_details.company == "Unknown":
            logger.warning("Company not properly extracted, using fallback")
            jd_details.company = "the company"
        
        if not jd_details.role or jd_details.role == "Unknown":
            logger.warning("Role not properly extracted, using fallback")
            jd_details.role = "the position"
        
        # Extract relevant skills from resume based on JD
        relevant_skills = []
        if jd_details.skills:
            resume_lower = resume_content.lower()
            for skill in jd_details.skills:
                if skill.lower() in resume_lower:
                    relevant_skills.append(skill)
        
        # Extract matched and missing skills from gap analysis
        matched_skills = []
        missing_skills = []
        candidate_strengths = []
        
        if gap_analysis:
            if hasattr(gap_analysis, 'matched_skills'):
                matched_skills = gap_analysis.matched_skills[:5]
            if hasattr(gap_analysis, 'missing_skills'):
                missing_skills = gap_analysis.missing_skills[:3]
            if hasattr(gap_analysis, 'strengths'):
                candidate_strengths = gap_analysis.strengths[:3]
            if hasattr(gap_analysis, 'strong_areas'):
                candidate_strengths.extend(gap_analysis.strong_areas[:2])
        
        # Create resume highlights
        highlights = ""
        if candidate_strengths:
            highlights = "; ".join(candidate_strengths[:5])
        else:
            # Fallback: extract first few sentences
            sentences = resume_content.split(". ")
            highlights = ". ".join(sentences[:3])
        
        skills_str = ", ".join(relevant_skills[:5]) if relevant_skills else "various technical skills"
        required_skills_str = ", ".join(jd_details.skills[:8]) if jd_details.skills else "various skills"
        matched_str = ", ".join(matched_skills) if matched_skills else skills_str
        missing_str = ", ".join(missing_skills) if missing_skills else "None"
        strengths_str = ", ".join(candidate_strengths) if candidate_strengths else "various competencies"
        
        # Format experience level from JD
        candidate_experience = jd_details.experience or "Not specified"
        
        prompt = email_prompt.format(
            candidate_name=user_profile["name"],
            candidate_email=user_profile["email"],
            candidate_location=user_profile.get("location", ""),
            company=jd_details.company,
            job_role=jd_details.role,
            required_skills=required_skills_str,
            experience_required=jd_details.experience or "Not specified",
            job_location=jd_details.location or "Not specified",
            relevant_skills=skills_str,
            resume_highlights=highlights,
            matched_skills=matched_str,
            missing_skills=missing_str,
            candidate_strengths=strengths_str,
            candidate_experience=candidate_experience
        )

        response = llm.invoke(prompt)
        email_text = response.content.strip()

        logger.debug(f"Generated email text: {email_text[:200]}...")

        # Parse the response to extract the body only
        # The new prompt returns both subject and body, but we only need the body
        lines = email_text.split("\n")
        body_lines = []
        in_body = False
        
        for line in lines:
            line_stripped = line.strip()
            # Skip subject line if present
            if line_stripped.lower().startswith("subject:"):
                continue
            elif line_stripped and not in_body:
                # Look for the start of the body (salutation)
                if any(salutation in line_stripped.lower() for salutation in ["dear", "hi", "hello"]):
                    in_body = True
                    body_lines.append(line_stripped)
            elif in_body:
                body_lines.append(line_stripped)
        
        # If we couldn't parse the body, use the whole response minus subject
        if not body_lines:
            # Remove subject line if present and use rest as body
            email_body = email_text
            if email_body.lower().startswith("subject:"):
                # Find first newline after subject
                first_newline = email_body.find("\n")
                if first_newline > 0:
                    email_body = email_body[first_newline + 1:].strip()
            body_lines = email_body.split("\n")
        
        # Clean up the body text with better formatting
        email_body = "\n".join(body_lines).strip()
        
        # Clean up any unwanted content while preserving natural language
        cleaned_lines = []
        for line in email_body.split("\n"):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Remove signature lines (they'll be added separately)
            if any(sig in line_lower for sig in ["best regards,", "sincerely,", "regards,", "thank you,"]):
                continue
            # Remove placeholder markers
            if "[" in line_stripped and "]" in line_stripped:
                continue
            # Remove markdown code blocks
            if line_stripped.startswith("```"):
                continue
            # Remove lines that look like JD content (section headers)
            jd_headers = ["requirements:", "qualifications:", "responsibilities:", "required skills:", "must have:", "nice to have:"]
            if any(header in line_lower for header in jd_headers):
                continue
            # Remove lines that are just lists of skills or requirements (comma-heavy, very long)
            if len(line_stripped) > 300 and line_stripped.count(",") > 5:
                continue
            
            cleaned_lines.append(line_stripped)

        # Improve paragraph alignment and formatting
        formatted_paragraphs = []
        current_paragraph = []
        
        for line in cleaned_lines:
            if not line.strip():
                # Empty line indicates paragraph break
                if current_paragraph:
                    paragraph_text = " ".join(current_paragraph).strip()
                    if paragraph_text:
                        formatted_paragraphs.append(paragraph_text)
                    current_paragraph = []
            else:
                current_paragraph.append(line)
        
        # Add the last paragraph if it exists
        if current_paragraph:
            paragraph_text = " ".join(current_paragraph).strip()
            if paragraph_text:
                formatted_paragraphs.append(paragraph_text)
        
        # Join paragraphs with proper spacing
        email_body = "\n\n".join(formatted_paragraphs).strip()
        
        # Ensure proper paragraph structure (at least 2-3 paragraphs)
        if len(formatted_paragraphs) < 2:
            # If only one paragraph, try to split it logically
            sentences = email_body.split(". ")
            if len(sentences) > 3:
                # Split into 2-3 paragraphs
                mid = len(sentences) // 2
                para1 = ". ".join(sentences[:mid]).strip()
                para2 = ". ".join(sentences[mid:]).strip()
                email_body = f"{para1}\n\n{para2}"
        
        # Validate email content - ensure it's not empty or just JD content
        if not email_body or len(email_body) < 50:
            logger.warning("Generated email too short, using fallback")
            email_body = _generate_fallback_email(jd_details, user_profile, relevant_skills)
        
        # Check if email contains JD-like content (lists, requirements, etc.)
        if _contains_jd_content(email_body):
            logger.warning("Email contains JD-like content, regenerating")
            email_body = _generate_fallback_email(jd_details, user_profile, relevant_skills)

        # Dynamic signature from user profile
        signature = f"""

Best Regards,
{user_profile['name']}

Email: {user_profile['email']}
Phone: {user_profile['phone']}
LinkedIn: {user_profile['linkedin']}
GitHub: {user_profile['github']}
Portfolio: {user_profile['portfolio']}
"""

        logger.info("Email generated successfully")
        # Return just the body (subject is handled separately by subject_generator)
        return email_body + signature
        
    except Exception as e:
        logger.error(f"Error generating email: {e}", exc_info=True)
        # Fallback to simple email (signature will be added by main function)
        user_profile = load_user_profile()
        fallback_email = _generate_fallback_email(jd_details, user_profile, [])
        # Add signature to fallback
        signature = f"""

Best Regards,
{user_profile['name']}

Email: {user_profile['email']}
Phone: {user_profile['phone']}
LinkedIn: {user_profile['linkedin']}
GitHub: {user_profile['github']}
Portfolio: {user_profile['portfolio']}
"""
        return fallback_email + signature


def _contains_jd_content(text: str) -> bool:
    """Check if text contains JD-like content (lists, requirements, etc.)."""
    # More aggressive check for actual JD content vs natural skill mentions
    jd_indicators = [
        "requirements:", "qualifications:", "responsibilities:",
        "required skills:", "must have:", "nice to have:", "job description:",
        "we are looking for", "the ideal candidate", "what you'll do:"
    ]
    text_lower = text.lower()
    
    # Only flag if multiple JD indicators are present (to avoid false positives)
    count = sum(1 for indicator in jd_indicators if indicator in text_lower)
    return count >= 2


def _generate_fallback_email(jd_details, user_profile, relevant_skills):
    """Generate a simple fallback email when LLM fails."""
    skills_str = ", ".join(relevant_skills[:3]) if relevant_skills else "my technical skills"
    
    # Clean up company and role to prevent raw JD content
    company = jd_details.company if jd_details.company and len(jd_details.company) < 50 else "your company"
    role = jd_details.role if jd_details.role and len(jd_details.role) < 50 else "the position"
    
    # Get location from JD if available
    location = jd_details.location if jd_details.location and jd_details.location != "Not specified" else ""
    
    # Create location mention if available
    location_mention = f"based in {location}" if location else ""
    
    fallback = f"""Dear Hiring Manager,

I came across the {role} position at {company} and wanted to reach out. With my background in {skills_str}, this role seems like a great match for what I've been working on.

I've been working with these technologies for a while now and have tackled several projects that align well with what you're looking for. I'd be excited to bring that experience to your team {location_mention}.

I've attached my resume and would love to chat about how my background fits with what you need.

Looking forward to hearing from you.
"""
    
    return fallback