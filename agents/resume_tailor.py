from langchain.prompts import PromptTemplate
from services.llm_service import get_llm
import os

llm = get_llm()

tailoring_prompt = PromptTemplate.from_template("""
You are an expert resume tailor specializing in ATS optimization.

ORIGINAL RESUME CONTENT:
{resume_content}

JOB DESCRIPTION:
Role: {role}
Company: {company}
Required Skills: {skills}
Experience Required: {experience}
Keywords: {keywords}

MISSING SKILLS TO ADD (only if candidate has them):
{missing_skills}

TASK:
Generate a tailored version of the resume that:
1. Highlights skills and experience most relevant to this specific role
2. Reorders sections to prioritize relevant experience
3. Uses keywords from the job description naturally
4. Optimizes for ATS systems (clear formatting, keyword density)
5. Maintains factual accuracy - NEVER hallucinate or add fake experience
6. Only adds missing skills if they are in the verified missing_skills list
7. Keeps the resume professional and concise

IMPORTANT RULES:
- Do NOT invent skills, projects, or experience
- Only use information from the original resume or the verified missing_skills list
- Maintain the same general structure but optimize content
- Focus on achievements and results
- Use action verbs
- Keep formatting clean and ATS-friendly

Return the tailored resume content as plain text.
""")


def tailor_resume(jd_details, resume_content, missing_skills=None):
    """
    Generate a tailored resume optimized for the specific job description.
    
    Args:
        jd_details: JobDetails object with company, role, skills, experience, keywords
        resume_content: Original resume content
        missing_skills: List of verified missing skills to add (optional)
    
    Returns:
        Tailored resume content as string
    """
    try:
        skills_str = ", ".join(jd_details.skills) if jd_details.skills else "None specified"
        keywords_str = ", ".join(jd_details.keywords) if jd_details.keywords else "None specified"
        missing_str = ", ".join(missing_skills) if missing_skills else "None"
        
        prompt = tailoring_prompt.format(
            role=jd_details.role,
            company=jd_details.company,
            skills=skills_str,
            experience=jd_details.experience,
            keywords=keywords_str,
            resume_content=resume_content,
            missing_skills=missing_str
        )
        
        response = llm.invoke(prompt)
        tailored_content = response.content.strip()
        
        return tailored_content
    except Exception as e:
        print(f"Error tailoring resume: {e}")
        # Return original content on error
        return resume_content


def generate_tailored_latex(jd_details, resume_content, user_profile, template_path="resume_templates/master_resume.tex"):
    """
    Generate a tailored LaTeX resume based on the job description.
    
    Args:
        jd_details: JobDetails object
        resume_content: Original resume content
        user_profile: User profile dict from config
        template_path: Path to LaTeX template
    
    Returns:
        Path to generated LaTeX file
    """
    output_dir = "generated_resumes"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate tailored content
    tailored_content = tailor_resume(jd_details, resume_content)
    
    # Read the original template
    try:
        with open(template_path, 'r') as f:
            template = f.read()
    except Exception as e:
        print(f"Error reading template: {e}")
        return template_path
    
    # Generate output filename based on company and role
    safe_company = "".join(c for c in jd_details.company if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_role = "".join(c for c in jd_details.role if c.isalnum() or c in (' ', '-', '_')).strip()
    output_filename = f"{safe_company}_{safe_role}_tailored.tex"
    output_path = os.path.join(output_dir, output_filename)
    
    # Update template with user profile info
    template = template.replace("Bhanu Asati", user_profile["name"])
    template = template.replace("bhanuasati13@gmail.com", user_profile["email"])
    template = template.replace("+91-73543-36191", user_profile["phone"])
    template = template.replace("Gurugram, India", user_profile["location"])
    template = template.replace("https://github.com/BHANUASATI", user_profile["github"])
    template = template.replace("https://linkedin.com/in/bhanu-asati-155493253/", user_profile["linkedin"])
    template = template.replace("https://bhanu-asati-portfolio.netlify.app/", user_profile["portfolio"])
    
    # For now, we'll save the template with updated profile info
    # Full content tailoring would require more sophisticated LaTeX parsing
    with open(output_path, 'w') as f:
        f.write(template)
    
    print(f"Generated tailored LaTeX resume: {output_path}")
    
    return output_path


def compile_tailored_resume(latex_path):
    """
    Compile the tailored LaTeX resume to PDF.
    
    Args:
        latex_path: Path to the LaTeX file
    
    Returns:
        Path to generated PDF or None if compilation fails
    """
    from services.latex_service import compile_resume
    
    output_dir = os.path.dirname(latex_path)
    pdf_path = compile_resume(latex_path, output_dir)
    
    return pdf_path
