"""
CLI application for AI Job Agent.

Supports command-line arguments and interactive mode for job applications.
"""

import sys
import argparse
from agents.jd_analyzer import analyze_jd
from agents.resume_loader import load_resumes
from agents.resume_splitter import split_documents
from agents.vector_store import create_vector_store
from agents.resume_selector import select_best_resume
from agents.jd_resume_comparator import compare_jd_resume
from agents.subject_generator import generate_subject
from agents.email_generator import generate_email
from agents.resume_selector import compare_all_resumes
from agents.resume_enhancer import generate_enhanced_resume_text
from services.gmail_service import get_gmail_service, send_email
from services.database_service import get_database_service, JobApplication
from services.pdf_generator import generate_enhanced_resume_pdf
from services.latex_resume_service import generate_enhanced_resume_latex
from utils.config_loader import load_user_profile
from config.settings import Config
from utils.validators import validate_job_description, sanitize_input
from utils.logger import get_logger
from utils.exceptions import JobAgentException
from datetime import datetime
import uuid

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="AI Job Agent - Automated Job Application System")
    parser.add_argument("--jd", type=str, help="Job description text or file path")
    parser.add_argument("--jd-file", type=str, help="Path to file containing job description")
    parser.add_argument("--dry-run", action="store_true", help="Generate email without sending")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--enhance-resume", action="store_true", help="Auto-enhance resume with missing skills")
    
    args = parser.parse_args()
    
    # Get job description
    job_description = ""
    
    if args.jd_file:
        with open(args.jd_file, 'r') as f:
            job_description = f.read()
    elif args.jd:
        job_description = args.jd
    elif args.interactive:
        print("Enter job description (press Ctrl+D when done):")
        job_description = sys.stdin.read()
    else:
        print("Error: Please provide job description via --jd, --jd-file, or --interactive")
        parser.print_help()
        sys.exit(1)
    
    if not job_description.strip():
        print("Error: Job description cannot be empty")
        sys.exit(1)
    
    # Validate and sanitize input
    try:
        validate_job_description(job_description)
        job_description = sanitize_input(job_description, max_length=10000)
        logger.info("Job description validated successfully")
    except Exception as e:
        print(f"Validation error: {e}")
        logger.error(f"Validation error: {e}", exc_info=True)
        sys.exit(1)

    # Load user profile
    user_profile = load_user_profile()
    print(f"User: {user_profile['name']}")

    # Step 1: Analyze JD
    print("\n[1/6] Analyzing Job Description...")
    jd_result = analyze_jd(job_description)
    print(f"  Company: {jd_result.company}")
    print(f"  Role: {jd_result.role}")
    print(f"  Skills: {', '.join(jd_result.skills)}")
    print(f"  Location: {jd_result.location or 'Not specified'}")

    # Step 2: Load resumes and create vector store
    print("\n[2/6] Loading and indexing resumes...")
    documents = load_resumes()
    chunks = split_documents(documents)
    vector_store = create_vector_store(chunks)
    print(f"  Indexed {len(documents)} resume documents")

    # Step 3: Select best resume
    print("\n[3/6] Selecting best matching resume...")
    query = f"Role: {jd_result.role}, Skills: {', '.join(jd_result.skills)}"
    best_resume_path, resume_content, score = select_best_resume(
        vector_store, query, jd_result.skills, jd_result.experience
    )
    print(f"  Selected: {best_resume_path}")
    print(f"  Match Score: {score:.2f}%")

    # Step 4: Compare JD vs Resume
    print("\n[4/6] Analyzing resume gaps...")
    gap_analysis = compare_jd_resume(jd_result, resume_content)
    print(f"  Match Score: {gap_analysis.match_score:.2%}")
    print(f"  Missing Skills: {', '.join(gap_analysis.missing_skills) if gap_analysis.missing_skills else 'None'}")
    print(f"  Strengths: {', '.join(gap_analysis.strengths[:2]) if gap_analysis.strengths else 'N/A'}")

    # Step 4.5: Enhance resume if requested
    if args.enhance_resume:
        print("\n[4.5/6] Enhancing resume with missing skills...")
        
        # Check if there are missing skills
        missing_skills = []
        if hasattr(gap_analysis, 'critical_missing_skills') and gap_analysis.critical_missing_skills:
            missing_skills.extend(gap_analysis.critical_missing_skills)
        if hasattr(gap_analysis, 'optional_missing_skills') and gap_analysis.optional_missing_skills:
            missing_skills.extend(gap_analysis.optional_missing_skills)
        
        if missing_skills:
            print(f"  Found {len(missing_skills)} missing skills to add")
            
            try:
                # Generate enhanced resume content
                enhanced_content = generate_enhanced_resume_text(
                    resume_content,
                    gap_analysis,
                    jd_result
                )
                
                # Generate LaTeX PDF
                enhanced_pdf_path = generate_enhanced_resume_latex(
                    enhanced_content,
                    best_resume_path,
                    jd_result.company,
                    jd_result.role,
                    user_profile
                )
                
                # Update resume path to use enhanced version
                best_resume_path = enhanced_pdf_path
                print(f"  Enhanced resume saved to: {enhanced_pdf_path}")
                print(f"  Using enhanced resume for application")
                
            except Exception as e:
                print(f"  Warning: Resume enhancement failed: {e}")
                print(f"  Proceeding with original resume")
                logger.error(f"Resume enhancement error: {e}", exc_info=True)
        else:
            print("  No missing skills found - resume is well-matched")

    # Step 5: Generate subject and email
    print("\n[5/6] Generating personalized email...")
    
    # Extract candidate strengths from gap analysis
    candidate_strengths = []
    if gap_analysis and hasattr(gap_analysis, 'strengths'):
        candidate_strengths = gap_analysis.strengths
    if gap_analysis and hasattr(gap_analysis, 'strong_areas'):
        candidate_strengths.extend(gap_analysis.strong_areas)
    
    email_subject = generate_subject(
        candidate_name=user_profile["name"],
        company=jd_result.company,
        role=jd_result.role,
        candidate_strengths=candidate_strengths
    )
    print(f"  Subject: {email_subject}")

    email_body = generate_email(jd_result, resume_content, gap_analysis)

    # Step 6: Send email (or dry run)
    if args.dry_run:
        print("\n[DRY RUN] Email would be sent to:", jd_result.email)
        print("\n--- Email Preview ---")
        print(f"Subject: {email_subject}")
        print("\nBody:")
        print(email_body)
        print("\n--- End Preview ---")
    else:
        print("\n[6/6] Sending application...")
        try:
            service = get_gmail_service()

            send_email(
                service=service,
                to_email=jd_result.email,
                subject=email_subject,
                body=email_body,
                attachment_path=best_resume_path
            )

            print("\n✅ Application Sent Successfully 🚀")
            print(f"   To: {jd_result.email}")
            print(f"   Resume: {best_resume_path}")

            # Save to database
            print("\n💾 Saving to database...")
            db = get_database_service()
            application = JobApplication(
                id=str(uuid.uuid4()),
                company=jd_result.company,
                role=jd_result.role,
                location=jd_result.location,
                skills=jd_result.skills,
                experience=jd_result.experience,
                email=jd_result.email,
                resume_used=best_resume_path,
                match_score=score / 100 if score > 1 else score,  # Normalize to 0-1
                gap_score=gap_analysis.match_score if gap_analysis else 0.5,
                status="Applied",
                applied_date=datetime.now().isoformat(),
                notes=""
            )
            db.add_application(application)
            print("   Application saved to database")

        except Exception as e:
            print(f"\n❌ Error sending email: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
