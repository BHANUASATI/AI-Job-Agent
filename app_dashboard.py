import streamlit as st
import pandas as pd
import plotly.express as px
from services.database_service import get_database_service
from datetime import datetime

st.set_page_config(page_title="Application Dashboard", layout="wide")

st.title("📊 Job Application Dashboard")
st.subheader("Track and analyze your job applications")

# Initialize database service
db = get_database_service()

# Sidebar filters
st.sidebar.title("Filters")

# Status filter
all_statuses = ["All", "Applied", "Under Review", "Interview", "Offer", "Rejected", "Withdrawn"]
status_filter = st.sidebar.selectbox("Status", all_statuses)

# Company filter
applications = db.get_all_applications()
companies = ["All"] + sorted(list(set([app.company for app in applications])))
company_filter = st.sidebar.selectbox("Company", companies)

# Get filtered applications
filtered_apps = applications

if status_filter != "All":
    filtered_apps = [app for app in filtered_apps if app.status == status_filter]

if company_filter != "All":
    filtered_apps = [app for app in filtered_apps if app.company == company_filter]

# Statistics
stats = db.get_statistics()

st.write("## Overview Statistics")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Applications", stats["total"])
col2.metric("Avg Match Score", f"{stats['avg_match_score']:.2%}")
col3.metric("Companies Applied", len(stats["by_company"]))
col4.metric("Domains", len(stats["by_domain"]))

# Status breakdown
st.write("## Application Status")
if stats["by_status"]:
    status_df = pd.DataFrame(
        list(stats["by_status"].items()),
        columns=["Status", "Count"]
    )
    fig_status = px.bar(status_df, x="Status", y="Count", color="Status", title="Applications by Status")
    st.plotly_chart(fig_status, use_container_width=True)
else:
    st.info("No application data available")

# Company breakdown
st.write("## Applications by Company")
if stats["by_company"]:
    company_df = pd.DataFrame(
        list(stats["by_company"].items()),
        columns=["Company", "Count"]
    )
    fig_company = px.bar(company_df, x="Company", y="Count", color="Count", title="Applications by Company")
    st.plotly_chart(fig_company, use_container_width=True)
else:
    st.info("No application data available")

# Domain breakdown
st.write("## Applications by Domain")
if stats["by_domain"]:
    domain_df = pd.DataFrame(
        list(stats["by_domain"].items()),
        columns=["Domain", "Count"]
    )
    fig_domain = px.pie(domain_df, values="Count", names="Domain", title="Applications by Domain")
    st.plotly_chart(fig_domain, use_container_width=True)
else:
    st.info("No application data available")

# Weekly/Monthly Reports
st.write("## Time-Based Reports")
time_filter = st.selectbox("Time Period", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])

from datetime import datetime, timedelta

all_apps = db.get_all_applications()
filtered_by_time = all_apps

if time_filter == "Last 7 Days":
    cutoff = datetime.now() - timedelta(days=7)
    filtered_by_time = [app for app in all_apps if datetime.fromisoformat(app.applied_date) >= cutoff]
elif time_filter == "Last 30 Days":
    cutoff = datetime.now() - timedelta(days=30)
    filtered_by_time = [app for app in all_apps if datetime.fromisoformat(app.applied_date) >= cutoff]
elif time_filter == "Last 90 Days":
    cutoff = datetime.now() - timedelta(days=90)
    filtered_by_time = [app for app in all_apps if datetime.fromisoformat(app.applied_date) >= cutoff]

if filtered_by_time:
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Applications ({time_filter})", len(filtered_by_time))
    
    # Calculate response rate (non-pending applications)
    responded = len([app for app in filtered_by_time if app.status not in ["Applied", "Under Review"]])
    col2.metric("Response Rate", f"{responded/len(filtered_by_time):.1%}" if filtered_by_time else "0%")
    
    # Success rate (offers)
    offers = len([app for app in filtered_by_time if app.status == "Offer"])
    col3.metric("Offers", offers)
    
    # Status distribution for selected period
    status_data = {}
    for app in filtered_by_time:
        status_data[app.status] = status_data.get(app.status, 0) + 1
    
    if status_data:
        status_df = pd.DataFrame(
            list(status_data.items()),
            columns=["Status", "Count"]
        )
        fig_time = px.pie(status_df, values="Count", names="Status", title=f"Status Distribution - {time_filter}")
        st.plotly_chart(fig_time, use_container_width=True)
else:
    st.info(f"No applications in the selected time period ({time_filter})")

# Manual application entry
st.write("## Add Manual Application")
with st.expander("Add Application Manually"):
    with st.form("manual_application"):
        col1, col2 = st.columns(2)
        
        with col1:
            company = st.text_input("Company")
            role = st.text_input("Role")
            location = st.text_input("Location")
            email = st.text_input("Recruiter Email")
        
        with col2:
            status = st.selectbox("Status", ["Applied", "Under Review", "Interview", "Offer", "Rejected", "Withdrawn"])
            match_score = st.slider("Match Score", 0.0, 1.0, 0.5, 0.01)
            resume_used = st.text_input("Resume Used")
            notes = st.text_area("Notes")
        
        skills = st.text_input("Skills (comma-separated)")
        experience = st.text_input("Experience Required")
        
        submitted = st.form_submit_button("Add Application")
        
        if submitted:
            from services.database_service import JobApplication
            import uuid
            
            skills_list = [s.strip() for s in skills.split(",")] if skills else []
            
            app = JobApplication(
                id=str(uuid.uuid4()),
                company=company,
                role=role,
                location=location,
                skills=skills_list,
                experience=experience,
                email=email,
                resume_used=resume_used,
                match_score=match_score,
                gap_score=0.0,
                status=status,
                applied_date=datetime.now().isoformat(),
                notes=notes
            )
            
            db.add_application(app)
            st.success("Application added successfully!")
            st.rerun()
