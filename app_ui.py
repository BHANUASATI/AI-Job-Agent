import os
import streamlit as st
from datetime import datetime
import uuid

from agents.jd_analyzer import analyze_jd
from agents.resume_loader import load_resumes
from agents.resume_splitter import split_documents
from agents.vector_store import create_vector_store
from agents.resume_selector import select_best_resume, compare_all_resumes
from agents.jd_resume_comparator import compare_jd_resume
from agents.subject_generator import generate_subject
from agents.email_generator import generate_email
from agents.resume_enhancer import generate_enhanced_resume_text
from services.gmail_service import get_gmail_service, send_email
from services.database_service import get_database_service, JobApplication
from services.pdf_generator import generate_enhanced_resume_pdf
from services.latex_resume_service import generate_enhanced_resume_latex
from utils.config_loader import load_user_profile
from config.settings import Config
from utils.validators import validate_job_description, sanitize_input
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="AI Job Agent", layout="wide")

st.title("🚀 AI Job Agent")
st.subheader("Smart AI Job Application System")

# Session State
for key in ["jd_result", "email_body", "email_subject", "resume_path", "gap_analysis", "match_score", 
            "resume_comparison", "selected_resume_mode", "selected_resume_index", "enhanced_resume_path", 
            "enhanced_resume_content", "resume_content"]:
    if key not in st.session_state:
        st.session_state[key] = None
        if key == "selected_resume_mode":
            st.session_state[key] = "auto"  # Default to auto selection
        if key == "selected_resume_index":
            st.session_state[key] = 0

# Sidebar Resume Manager
st.sidebar.title("Resume Manager")
resume_folder = Config.RESUME_DIR

if not resume_folder.exists():
    resume_folder.mkdir(parents=True, exist_ok=True)

existing_resumes = [f.name for f in resume_folder.iterdir() if f.suffix == ".pdf"]

st.sidebar.write("Current Resumes:")
for resume in existing_resumes:
    st.sidebar.write(f"• {resume}")

uploaded_files = st.sidebar.file_uploader(
    "Upload New Resume (Optional)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        save_path = resume_folder / uploaded_file.name
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    st.sidebar.success("Resume Uploaded Successfully")
    st.rerun()

# User Profile
user_profile = load_user_profile()
st.sidebar.markdown("---")
st.sidebar.subheader("👤 User Profile")
st.sidebar.write(f"**Name:** {user_profile['name']}")
st.sidebar.write(f"**Email:** {user_profile['email']}")

# Input method selection
input_method = st.radio(
    "Input Method",
    ["Paste Job Description", "Job Link"],
    horizontal=True
)

job_description = ""

if input_method == "Paste Job Description":
    job_description = st.text_area(
        "Paste Job Description",
        height=300,
        key="job_desc_input"
    )

else:
    job_url = st.text_input("Enter Job Link")

    if job_url and st.button("Extract Job Description"):
        from agents.link_scraper import scrape_job_link

        with st.spinner("Extracting job description..."):
            result = scrape_job_link(job_url)

            if result["success"]:
                job_description = result["job_description"]
                st.success("Job description extracted successfully!")

                st.text_area(
                    "Extracted Job Description",
                    value=job_description,
                    height=300,
                    key="extracted_jd"
                )
            else:
                st.error(f"Failed to extract: {result.get('error', 'Unknown error')}")

if st.button("Analyze Job"):
    try:
        # Validate and sanitize input
        if not job_description.strip():
            st.error("Please enter a job description first.")
            st.stop()
        
        validate_job_description(job_description)
        job_description = sanitize_input(job_description, max_length=10000)
        
        logger.info("Starting job analysis from UI")
        
    except Exception as e:
        st.error(f"Validation error: {str(e)}")
        logger.error(f"Validation error: {e}", exc_info=True)
        st.stop()

    with st.spinner("Analyzing Job Description..."):
        jd_result = analyze_jd(job_description)

    with st.spinner("Loading and indexing resumes..."):
        documents = load_resumes()
        chunks = split_documents(documents)
        vector_store = create_vector_store(chunks)

    with st.spinner("Comparing all resumes against job description..."):
        query = f"Role: {jd_result.role}, Skills: {', '.join(jd_result.skills)}"
        resume_comparison = compare_all_resumes(
            vector_store, query, jd_result.skills, jd_result.experience
        )
        st.session_state.resume_comparison = resume_comparison

    # Auto-select best resume by default
    if resume_comparison:
        best_resume = resume_comparison[0]
        st.session_state.selected_resume_index = 0
        best_resume_path = best_resume['resume_path']
        score = best_resume['score']
        
        # Get resume content for selected resume
        resume_groups = {}
        for doc in documents:
            source = doc.metadata.get("source", "Unknown")
            if source not in resume_groups:
                resume_groups[source] = []
            resume_groups[source].append(doc)
        
        if best_resume_path in resume_groups:
            best_chunks = resume_groups[best_resume_path]
            resume_content = "\n\n".join([chunk.page_content for chunk in best_chunks])
            st.session_state.resume_content = resume_content
        else:
            resume_content = ""
            st.session_state.resume_content = ""
            logger.warning(f"Could not find resume content for {best_resume_path}")
    else:
        st.error("No resumes found for comparison")
        st.stop()

    with st.spinner("Analyzing resume gaps..."):
        gap_analysis = compare_jd_resume(jd_result, resume_content)

    with st.spinner("Generating personalized email..."):
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

        email_body = generate_email(jd_result, resume_content, gap_analysis)

    st.session_state.jd_result = jd_result
    st.session_state.email_body = email_body
    st.session_state.email_subject = email_subject
    st.session_state.resume_path = best_resume_path
    st.session_state.gap_analysis = gap_analysis
    st.session_state.match_score = score

if st.session_state.jd_result:
    st.write("## Job Analysis")
    col1, col2, col3 = st.columns(3)
    col1.metric("Company", st.session_state.jd_result.company)
    col2.metric("Role", st.session_state.jd_result.role)
    col3.metric("Location", st.session_state.jd_result.location or "Not specified")

    st.write("**Required Skills:**", ", ".join(st.session_state.jd_result.skills))

    if st.session_state.jd_result.keywords:
        st.write("**Keywords:**", ", ".join(st.session_state.jd_result.keywords))

# Resume Comparison Table
if st.session_state.resume_comparison:
    st.write("## Resume Comparison")
    
    # Create comparison dataframe
    comparison_data = []
    for idx, resume in enumerate(st.session_state.resume_comparison):
        comparison_data.append({
            "Resume Name": resume['resume_name'],
            "Match Score": f"{resume['score']:.1f}%",
            "Matched Skills": resume['matched_count'],
            "Missing Skills": resume['missing_count']
        })
    
    import pandas as pd
    comparison_df = pd.DataFrame(comparison_data)
    
    # Display comparison table
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Resume Selection Mode
    st.write("## Resume Selection")
    selection_mode = st.radio(
        "Selection Mode",
        ["Auto Select (Best Match)", "Manual Select"],
        horizontal=True,
        key="resume_selection_mode"
    )
    
    if selection_mode == "Auto Select (Best Match)":
        st.session_state.selected_resume_mode = "auto"
        st.session_state.selected_resume_index = 0
        best_resume = st.session_state.resume_comparison[0]
        st.success(f"✅ Auto-selected: {best_resume['resume_name']} with {best_resume['score']:.1f}% match")
    else:
        st.session_state.selected_resume_mode = "manual"
        resume_options = [f"{r['resume_name']} ({r['score']:.1f}%)" for r in st.session_state.resume_comparison]
        selected_idx = st.selectbox(
            "Select Resume",
            range(len(resume_options)),
            format_func=lambda x: resume_options[x],
            index=st.session_state.selected_resume_index
        )
        st.session_state.selected_resume_index = selected_idx
        selected_resume = st.session_state.resume_comparison[selected_idx]
        st.info(f"📌 Manually selected: {selected_resume['resume_name']} with {selected_resume['score']:.1f}% match")
    
    # Low Match Warning
    selected_resume = st.session_state.resume_comparison[st.session_state.selected_resume_index]
    match_score = selected_resume['score']
    
    if match_score < 50:
        st.error(f"⚠️ **Low Match Warning**: The selected resume has only {match_score:.1f}% match. Consider uploading a more relevant resume or proceeding with caution.")
    elif match_score < 75:
        st.warning(f"⚡ **Medium Match**: The selected resume has {match_score:.1f}% match. Some skills may be missing.")
    else:
        st.success(f"✅ **Strong Match**: The selected resume has {match_score:.1f}% match with the job requirements.")

if st.session_state.match_score is not None:
    st.write("## Resume Match")
    col1, col2 = st.columns(2)
    col1.metric("Match Score", f"{st.session_state.match_score:.2f}")
    col2.metric("Selected Resume", os.path.basename(st.session_state.resume_path))

if st.session_state.gap_analysis:
    st.write("## Gap Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Matched Skills:**")
        if hasattr(st.session_state.gap_analysis, 'matched_skills') and st.session_state.gap_analysis.matched_skills:
            for skill in st.session_state.gap_analysis.matched_skills[:5]:
                st.write(f"✓ {skill}")
        else:
            st.write("None")
        
        st.write("**Critical Missing Skills:**")
        if hasattr(st.session_state.gap_analysis, 'critical_missing_skills') and st.session_state.gap_analysis.critical_missing_skills:
            for skill in st.session_state.gap_analysis.critical_missing_skills:
                st.write(f"⚠️ {skill}")
        else:
            st.write("None")
        
        st.write("**Optional Missing Skills:**")
        if hasattr(st.session_state.gap_analysis, 'optional_missing_skills') and st.session_state.gap_analysis.optional_missing_skills:
            for skill in st.session_state.gap_analysis.optional_missing_skills:
                st.write(f"• {skill}")
        else:
            st.write("None")

    with col2:
        st.write("**Strengths:**")
        if st.session_state.gap_analysis.strengths:
            for strength in st.session_state.gap_analysis.strengths[:3]:
                st.write(f"• {strength}")
        else:
            st.write("N/A")
        
        st.write("**Strong Areas:**")
        if hasattr(st.session_state.gap_analysis, 'strong_areas') and st.session_state.gap_analysis.strong_areas:
            for area in st.session_state.gap_analysis.strong_areas[:3]:
                st.write(f"• {area}")
        else:
            st.write("N/A")
        
        st.write("**Weak Areas:**")
        if hasattr(st.session_state.gap_analysis, 'weak_areas') and st.session_state.gap_analysis.weak_areas:
            for area in st.session_state.gap_analysis.weak_areas[:3]:
                st.write(f"• {area}")
        else:
            st.write("N/A")

# Resume Enhancement Section
if st.session_state.gap_analysis and st.session_state.resume_content:
    st.write("## Resume Enhancement")
    
    # Check if there are missing skills
    missing_skills = []
    if hasattr(st.session_state.gap_analysis, 'critical_missing_skills') and st.session_state.gap_analysis.critical_missing_skills:
        missing_skills.extend(st.session_state.gap_analysis.critical_missing_skills)
    if hasattr(st.session_state.gap_analysis, 'optional_missing_skills') and st.session_state.gap_analysis.optional_missing_skills:
        missing_skills.extend(st.session_state.gap_analysis.optional_missing_skills)
    
    if missing_skills:
        st.info(f"📝 Found {len(missing_skills)} missing skills that can be added to your resume.")
        
        if st.button("✨ Auto-Enhance Resume (Add Missing Skills)"):
            with st.spinner("Enhancing resume with missing skills..."):
                try:
                    # Generate enhanced resume content
                    enhanced_content = generate_enhanced_resume_text(
                        st.session_state.resume_content,
                        st.session_state.gap_analysis,
                        st.session_state.jd_result
                    )
                    st.session_state.enhanced_resume_content = enhanced_content
                    
                    # Generate LaTeX PDF
                    enhanced_pdf_path = generate_enhanced_resume_latex(
                        enhanced_content,
                        st.session_state.resume_path,
                        st.session_state.jd_result.company,
                        st.session_state.jd_result.role,
                        user_profile
                    )
                    st.session_state.enhanced_resume_path = enhanced_pdf_path
                    
                    st.success("✅ Resume enhanced successfully!")
                    st.info(f"Enhanced resume saved to: {enhanced_pdf_path}")
                    
                except Exception as e:
                    st.error(f"Error enhancing resume: {str(e)}")
                    logger.error(f"Resume enhancement error: {e}", exc_info=True)
        
        # Show enhanced resume if available
        if st.session_state.enhanced_resume_content:
            st.write("### Enhanced Resume Preview")
            with st.expander("View Enhanced Resume Content"):
                st.text_area(
                    "Enhanced Resume",
                    st.session_state.enhanced_resume_content,
                    height=400,
                    key="enhanced_resume_view"
                )
            
            # Option to use enhanced resume
            use_enhanced = st.checkbox("📎 Use Enhanced Resume for Application", value=False)
            
            if use_enhanced and st.session_state.enhanced_resume_path:
                st.session_state.resume_path = st.session_state.enhanced_resume_path
                st.success(f"Will use enhanced resume: {os.path.basename(st.session_state.enhanced_resume_path)}")
    else:
        st.success("✅ No missing skills found! Your resume is well-matched for this position.")

if st.session_state.email_body:
    st.write("## Generated Email")
    st.code(st.session_state.email_subject, language="text")

    st.text_area(
        "Email Preview",
        st.session_state.email_body,
        height=350,
        key="email_preview"
    )

    if st.button("Send Application"):
        try:
            service = get_gmail_service()

            send_email(
                service=service,
                to_email=st.session_state.jd_result.email,
                subject=st.session_state.email_subject,
                body=st.session_state.email_body,
                attachment_path=st.session_state.resume_path
            )

            st.success("Application Sent Successfully 🚀")

            db = get_database_service()
            application = JobApplication(
                id=str(uuid.uuid4()),
                company=st.session_state.jd_result.company,
                role=st.session_state.jd_result.role,
                location=st.session_state.jd_result.location,
                skills=st.session_state.jd_result.skills,
                experience=st.session_state.jd_result.experience,
                email=st.session_state.jd_result.email,
                resume_used=st.session_state.resume_path,
                match_score=st.session_state.match_score,
                gap_score=st.session_state.gap_analysis.match_score if st.session_state.gap_analysis else 0,
                status="Applied",
                applied_date=datetime.now().isoformat(),
                notes=""
            )

            db.add_application(application)
            st.info("Application saved to dashboard")

        except Exception as e:
            st.error(f"Error sending email: {str(e)}")