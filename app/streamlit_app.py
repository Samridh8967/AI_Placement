"""
TalentBridge | Enterprise Campus Recruitment & Placement Platform
================================================================
A production-grade, end-to-end university career platform with 3 dedicated dashboards:
1. Student Dashboard (Personal credentials, live drive matching, readiness verdicts, preparation roadmaps, and application tracking)
2. Corporate Recruiter / HR Workspace (Post new job roles, review live applicants, rank by semantic fit, shortlist for interviews, export CSV)
3. University Placement Directorate (Campus KPIs, live market demand BI, master audit roster, drive manager, announcements)
All actions persist in real-time to SQLite.
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add src to system path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import pandas as pd

# Page Configuration - Institutional Authority
st.set_page_config(
    page_title="TalentBridge | Career Services & Placement Suite",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Backend Imports
from database import (
    seed_db_from_json,
    get_all_students_db,
    get_all_jobs_db,
    save_job_db,
    save_student_db,
    get_student_applications_db,
    submit_application_db,
    withdraw_application_db,
    get_all_applications_db,
    get_job_shortlists_db,
    toggle_shortlist_db,
    get_all_shortlists_db,
    get_announcements_db,
    add_announcement_db
)
from keyword_matcher import calculate_keyword_match
from semantic_matcher import calculate_semantic_match, rank_jobs_semantically, get_model
from readiness_model import predict_interview_readiness
from recommender import generate_recommendations

# ------------------------------------------------------------------------------
# 1. DATABASE & ML INITIALIZATION
# ------------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def init_database():
    seed_db_from_json()
    return True

init_database()

@st.cache_resource(show_spinner=False)
def load_matching_engine():
    return get_model()

load_matching_engine()

def refresh_placement_data():
    return get_all_students_db(), get_all_jobs_db()

students, jobs = refresh_placement_data()
student_dict = {s["id"]: s for s in students}
job_dict = {j["job_id"]: j for j in jobs}

@st.cache_data(show_spinner=False)
def get_cached_job_rankings(student_id: str, _jobs_list):
    target_student = student_dict[student_id]
    return rank_jobs_semantically(target_student, _jobs_list)

# ------------------------------------------------------------------------------
# 2. SESSION STATE
# ------------------------------------------------------------------------------
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

if "auth_role" not in st.session_state:
    st.session_state.auth_role = None  # 'student', 'recruiter', 'tpo'

if "auth_user_name" not in st.session_state:
    st.session_state.auth_user_name = ""

if "current_student_id" not in st.session_state:
    st.session_state.current_student_id = "STU_003"  # Default: Rohan Verma

if "current_recruiter_company" not in st.session_state:
    st.session_state.current_recruiter_company = "CloudScale Systems"

if "current_recruiter_job_id" not in st.session_state:
    st.session_state.current_recruiter_job_id = "JOB_003"

if "show_student_registration" not in st.session_state:
    st.session_state.show_student_registration = False

# Live SQLite helpers
def get_student_applied_job_ids(student_id: str):
    appls = get_student_applications_db(student_id)
    return {a["job_id"] for a in appls}

def get_job_shortlisted_student_ids(job_id: str):
    shortlists = get_job_shortlists_db(job_id)
    return {s["student_id"] for s in shortlists}

def is_student_shortlisted_for_job(student_id: str, job_id: str):
    return student_id in get_job_shortlisted_student_ids(job_id)

def get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    return name[:2].upper() if name else "TB"


# ------------------------------------------------------------------------------
# 3. ENTERPRISE DESIGN SYSTEM (CLEAN, SPACIOUS, EXECUTIVE)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #0f172a;
    }

    /* Hide Streamlit Chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 4rem;
        max-width: 1140px;
    }

    /* Card Containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 24px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
        margin-bottom: 20px !important;
    }

    /* Enterprise Buttons */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: -0.01em !important;
        padding: 8px 18px !important;
        transition: all 0.15s ease-in-out !important;
    }
    .stButton > button[kind="primary"] {
        background: #1e40af !important;
        border-color: #1e40af !important;
        color: #ffffff !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
        box-shadow: 0 4px 6px -1px rgba(30, 64, 175, 0.2) !important;
    }
    .stButton > button[kind="secondary"] {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #334155 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #f8fafc !important;
        border-color: #94a3b8 !important;
        color: #0f172a !important;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        line-height: 1.2 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #64748b !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* Top Master Navigation */
    .app-navbar {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 22px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04);
    }
    .app-crest {
        width: 38px;
        height: 38px;
        background: #1e40af;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-weight: 800;
        font-size: 15px;
        letter-spacing: -0.02em;
    }

    /* Badges */
    .badge-ready {
        display: inline-block;
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #065f46;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .badge-prep {
        display: inline-block;
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .badge-cutoff {
        display: inline-block;
        background: #fef2f2;
        border: 1px solid #fecdd3;
        color: #9f1239;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .badge-shortlist {
        display: inline-block;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1e40af;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    /* Skill Tags */
    .tag-chip {
        display: inline-block;
        background: #f1f5f9;
        color: #334155;
        border: 1px solid #e2e8f0;
        padding: 3px 9px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        margin: 2px 4px 2px 0;
    }
    .tag-chip-req {
        display: inline-block;
        background: #eff6ff;
        color: #1e40af;
        border: 1px solid #bfdbfe;
        padding: 3px 9px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px 4px 2px 0;
    }

    /* Announcement Card */
    .notice-card {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-left: 4px solid #1e40af;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 4. MODALS (POST JOB & UPDATE STUDENT PROFILE & POST ANNOUNCEMENT)
# ------------------------------------------------------------------------------
@st.dialog("Post a New Job Role", width="large")
def modal_post_job():
    st.caption("Publish a new corporate recruitment opening to graduating candidates:")
    with st.form("form_add_job_recruiter", clear_on_submit=True):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            j_company = st.text_input("Company Name *", value=st.session_state.current_recruiter_company)
            j_title = st.text_input("Role Title *", placeholder="e.g. Associate Cloud Engineer")
            j_domain = st.text_input("Technical Domain", placeholder="e.g. Cloud & Distributed Systems")
        with c2:
            j_cgpa = st.number_input("Minimum Marks Cutoff (CGPA)", min_value=0.0, max_value=10.0, value=6.5, step=0.1)
            j_exp = st.number_input("Minimum Internship (Months)", min_value=0, max_value=60, value=0)

        j_req = st.text_area("Required Technical Skills (comma-separated) *", placeholder="e.g. Python, Docker, Kubernetes, Linux, SQL")
        j_desc = st.text_area("Role Overview", placeholder="Brief description of candidate responsibilities and project scope.")

        if st.form_submit_button("Publish Job Role", type="primary", use_container_width=True):
            if not j_title.strip() or not j_req.strip():
                st.error("Please provide Role Title and Required Skills.")
            else:
                new_id = f"JOB_{uuid.uuid4().hex[:6].upper()}"
                new_j = {
                    "job_id": new_id,
                    "title": j_title.strip(),
                    "company": j_company.strip(),
                    "domain": j_domain.strip() or "Technology",
                    "description": j_desc.strip() or f"Campus recruitment for {j_title}",
                    "required_skills": [s.strip() for s in j_req.split(",") if s.strip()],
                    "preferred_skills": [],
                    "min_experience_months": int(j_exp),
                    "required_coursework": [],
                    "min_cgpa": float(j_cgpa)
                }
                save_job_db(new_j)
                st.cache_data.clear()
                st.session_state.current_recruiter_job_id = new_id
                st.success(f"Position '{j_title}' published to campus placement roster.")
                st.rerun()


@st.dialog("Update My Placement Profile", width="large")
def modal_update_profile(s_obj):
    st.caption("Update your verified academic and technical credentials:")
    with st.form("form_edit_student_profile", clear_on_submit=False):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            u_cgpa = st.number_input("Cumulative CGPA", min_value=0.0, max_value=10.0, value=float(s_obj.get("cgpa", 7.5)), step=0.1)
        with c2:
            u_exp = st.number_input("Internship Experience (Months)", min_value=0, max_value=60, value=int(s_obj.get("experience_months", 0)))

        current_skills = ", ".join(s_obj.get("technical_skills", []))
        u_skills = st.text_area("Verified Technical Skills (comma-separated)", value=current_skills)

        projs = s_obj.get("projects", [])
        p_title = projs[0].get("title", "Capstone Project") if projs else "Capstone Project"
        p_desc = projs[0].get("description", "") if projs else ""

        u_p_title = st.text_input("Capstone Project Title", value=p_title)
        u_p_desc = st.text_area("Project Summary", value=p_desc)

        if st.form_submit_button("Save Profile Updates", type="primary", use_container_width=True):
            new_skills_list = [s.strip() for s in u_skills.split(",") if s.strip()]
            updated_stu = dict(s_obj)
            updated_stu["cgpa"] = float(u_cgpa)
            updated_stu["experience_months"] = int(u_exp)
            updated_stu["technical_skills"] = new_skills_list
            updated_stu["projects"] = [{
                "title": u_p_title.strip() or "Capstone Project",
                "description": u_p_desc.strip(),
                "skills_used": new_skills_list
            }]
            save_student_db(updated_stu)
            st.cache_data.clear()
            st.success("Profile updated in database. Semantic match rankings recalculated.")
            st.rerun()


@st.dialog("Publish Campus Placement Notice", width="large")
def modal_add_announcement():
    st.caption("Publish a placement notice to be visible on student and recruiter dashboards:")
    with st.form("form_add_announcement", clear_on_submit=True):
        an_title = st.text_input("Notice Headline *", placeholder="e.g. Technical Round 1 Schedule Announced")
        an_cat = st.selectbox("Category", ["Recruitment Drive", "Assessment", "General Notice", "Policy Update"])
        an_content = st.text_area("Announcement Details *", placeholder="Provide relevant timings, venue, or required materials.")

        if st.form_submit_button("Publish Announcement", type="primary", use_container_width=True):
            if not an_title.strip() or not an_content.strip():
                st.error("Please supply Notice Headline and Details.")
            else:
                add_announcement_db(an_title.strip(), an_content.strip(), an_cat, "Placement Directorate")
                st.success("Announcement published to campus bulletin.")
                st.rerun()


# ------------------------------------------------------------------------------
# 5. UNIFIED LOGIN PORTAL (DISCRETE CREDENTIALS FOR EACH ROLE)
# ------------------------------------------------------------------------------
if not st.session_state.is_authenticated:
    # Check if student clicked self-registration
    if st.session_state.show_student_registration:
        s_reg_col1, s_reg_col2, s_reg_col3 = st.columns([1, 4, 1])
        with s_reg_col2:
            st.markdown("### 🎓 Student Placement Registration")
            st.caption("Create your verified academic profile to discover matching companies:")

            with st.container(border=True):
                with st.form("form_student_self_registration", clear_on_submit=False):
                    st.markdown("##### 1. Academic Credentials")
                    c1, c2 = st.columns(2, gap="large")
                    with c1:
                        new_name = st.text_input("Full Name *", placeholder="e.g. Samridhjit Barnwal")
                        new_email = st.text_input("University Institutional Email *", placeholder="e.g. samridhjit@university.edu")
                    with c2:
                        new_cgpa = st.number_input("Cumulative CGPA (out of 10) *", min_value=0.0, max_value=10.0, value=7.8, step=0.1)
                        new_exp = st.number_input("Prior Internship Experience (Months)", min_value=0, max_value=60, value=0)

                    st.write("")
                    st.markdown("##### 2. Technical Skills")
                    new_skills = st.text_area("Verified Skills (comma-separated) *", placeholder="e.g. Python, SQL, Machine Learning, Git, React, Docker")

                    st.write("")
                    st.markdown("##### 3. Capstone Project")
                    new_proj_title = st.text_input("Project Title", placeholder="e.g. NLP Resume Matcher")
                    new_proj_desc = st.text_area("Project Abstract", placeholder="Brief description of tools and technologies used.")

                    st.write("")
                    sub_c1, sub_c2 = st.columns([2, 1])
                    with sub_c1:
                        if st.form_submit_button("Register & Enter Student Portal", type="primary", use_container_width=True):
                            if not new_name.strip() or not new_email.strip() or not new_skills.strip():
                                st.error("Please supply Full Name, Email, and Technical Skills.")
                            else:
                                new_id = f"STU_{uuid.uuid4().hex[:6].upper()}"
                                skills_list = [s.strip() for s in new_skills.split(",") if s.strip()]
                                new_student_data = {
                                    "id": new_id,
                                    "name": new_name.strip(),
                                    "email": new_email.strip(),
                                    "experience_months": int(new_exp),
                                    "technical_skills": skills_list,
                                    "coursework": [],
                                    "projects": [{
                                        "title": new_proj_title.strip() or "Capstone Project",
                                        "description": new_proj_desc.strip(),
                                        "skills_used": skills_list
                                    }],
                                    "internship_experience": f"{new_exp} months internship",
                                    "preferred_domains": [],
                                    "career_interests": [],
                                    "cgpa": float(new_cgpa),
                                    "branch": "Computer Science & Engineering"
                                }
                                save_student_db(new_student_data)
                                st.cache_data.clear()
                                st.session_state.is_authenticated = True
                                st.session_state.auth_role = "student"
                                st.session_state.current_student_id = new_id
                                st.session_state.auth_user_name = new_name.strip()
                                st.session_state.show_student_registration = False
                                st.rerun()

                    with sub_c2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.show_student_registration = False
                            st.rerun()
        st.stop()

    # Normal Login Screen (Clean, Centered, Spacious)
    l_spacer_l, l_center, l_spacer_r = st.columns([1, 2.8, 1])

    with l_center:
        st.markdown("""
        <div style="text-align: center; padding: 28px 0 16px 0;">
            <div style="display:inline-flex; align-items:center; gap:10px; margin-bottom:8px;">
                <div class="app-crest" style="width:44px; height:44px; font-size:18px;">TB</div>
                <span style="font-size:26px; font-weight:800; color:#0f172a; letter-spacing:-0.02em;">TalentBridge</span>
            </div>
            <div style="font-size:14px; color:#475569; font-weight:500;">
                Campus Recruitment & Career Placement Suite
            </div>
            <div style="font-size:12px; color:#64748b; margin-top:2px;">
                Directorate of Career Services & Corporate Relations
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("##### Portal Authentication")
            st.caption("Sign in with your role credentials to access your dedicated placement workspace:")

            login_tab_stu, login_tab_rec, login_tab_tpo = st.tabs([
                "Student Portal",
                "Corporate Recruiter",
                "University Placement (TPO)"
            ])

            # 1. STUDENT LOGIN
            with login_tab_stu:
                st.write("")
                student_options = list(student_dict.keys())
                sel_stu_login = st.selectbox(
                    "Select Student Profile / Account:",
                    options=student_options,
                    format_func=lambda s_id: f"{student_dict[s_id]['name']} — {student_dict[s_id].get('email', s_id)} ({student_dict[s_id].get('cgpa', 7.5)} CGPA)"
                )
                st.text_input("Password", type="password", value="student2026", disabled=True, help="Institutional demo credentials prefilled")

                st.write("")
                if st.button("Sign In to Student Dashboard", type="primary", use_container_width=True):
                    st.session_state.is_authenticated = True
                    st.session_state.auth_role = "student"
                    st.session_state.current_student_id = sel_stu_login
                    st.session_state.auth_user_name = student_dict[sel_stu_login]["name"]
                    st.rerun()

                st.write("")
                if st.button("New Graduating Student? Register Profile", use_container_width=True):
                    st.session_state.show_student_registration = True
                    st.rerun()

            # 2. RECRUITER / HR LOGIN
            with login_tab_rec:
                st.write("")
                company_options = sorted(list(set(j["company"] for j in jobs)))
                sel_comp_login = st.selectbox("Select Visiting Corporate Entity:", options=company_options)

                comp_jobs = [j for j in jobs if j["company"] == sel_comp_login]
                sel_job_login = comp_jobs[0]["job_id"] if comp_jobs else list(job_dict.keys())[0]

                st.text_input("Work Email", value=f"hr@{sel_comp_login.lower().replace(' ', '')}.com", disabled=True)
                st.text_input("Recruiter Access Key", type="password", value="recruiter2026", disabled=True)

                st.write("")
                if st.button("Sign In to Recruiter Workspace", type="primary", use_container_width=True):
                    st.session_state.is_authenticated = True
                    st.session_state.auth_role = "recruiter"
                    st.session_state.current_recruiter_company = sel_comp_login
                    st.session_state.current_recruiter_job_id = sel_job_login
                    st.session_state.auth_user_name = f"{sel_comp_login} HR"
                    st.rerun()

            # 3. UNIVERSITY PLACEMENT (TPO) LOGIN
            with login_tab_tpo:
                st.write("")
                st.selectbox(
                    "Placement Directorate Officer:",
                    ["Dr. A. K. Sharma — Head, Corporate Relations & TPO", "Prof. Sneha Deshmukh — Placement Coordinator"]
                )
                st.text_input("Staff Email", value="tpo@university.edu", disabled=True)
                st.text_input("Administrative Security PIN", type="password", value="admin2026", disabled=True)

                st.write("")
                if st.button("Sign In to Placement Directorate", type="primary", use_container_width=True):
                    st.session_state.is_authenticated = True
                    st.session_state.auth_role = "tpo"
                    st.session_state.auth_user_name = "Dr. A. K. Sharma (TPO)"
                    st.rerun()

        # Fast Evaluator 1-Click Access
        st.write("")
        st.markdown("<div style='text-align:center; font-size:12px; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:8px;'>Evaluator One-Click Preview</div>", unsafe_allow_html=True)
        q1, q2, q3 = st.columns(3)
        with q1:
            if st.button("Demo: Student (Rohan)", use_container_width=True):
                st.session_state.is_authenticated = True
                st.session_state.auth_role = "student"
                st.session_state.current_student_id = "STU_003"
                st.session_state.auth_user_name = "Rohan Verma"
                st.rerun()
        with q2:
            if st.button("Demo: Recruiter (CloudScale)", use_container_width=True):
                st.session_state.is_authenticated = True
                st.session_state.auth_role = "recruiter"
                st.session_state.current_recruiter_company = "CloudScale Systems"
                st.session_state.current_recruiter_job_id = "JOB_003"
                st.session_state.auth_user_name = "CloudScale Systems HR"
                st.rerun()
        with q3:
            if st.button("Demo: University TPO", use_container_width=True):
                st.session_state.is_authenticated = True
                st.session_state.auth_role = "tpo"
                st.session_state.auth_user_name = "Dr. A. K. Sharma (TPO)"
                st.rerun()

    st.stop()


# ------------------------------------------------------------------------------
# 6. AUTHENTICATED TOPBAR (FOCUSED ON CURRENT USER — ZERO CONFUSING SWITCHERS)
# ------------------------------------------------------------------------------
top_col1, top_col2 = st.columns([3, 1], vertical_alignment="center")

with top_col1:
    portal_name = {
        "student": "Student Placement Portal",
        "recruiter": f"Corporate Recruiter Workspace — {st.session_state.current_recruiter_company}",
        "tpo": "University Placement Directorate"
    }.get(st.session_state.auth_role, "Placement Portal")

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px;">
        <div class="app-crest">{get_initials(st.session_state.auth_user_name)}</div>
        <div>
            <div style="font-size:18px; font-weight:700; color:#0f172a; letter-spacing:-0.02em;">{portal_name}</div>
            <div style="font-size:12px; color:#64748b;">
                Signed in as <strong style="color:#0f172a;">{st.session_state.auth_user_name}</strong> &nbsp;•&nbsp; 
                Academic Session 2026–2027
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_col2:
    if st.button("Sign Out", use_container_width=True):
        st.session_state.is_authenticated = False
        st.session_state.auth_role = None
        st.session_state.auth_user_name = ""
        st.rerun()

st.write("")


# ==============================================================================
# DASHBOARD 1: STUDENT DASHBOARD (OWN DATA, MATCHED DRIVES, READINESS, RECS)
# ==============================================================================
if st.session_state.auth_role == "student":
    s_obj = student_dict.get(st.session_state.current_student_id, students[0])

    # Campus Notice Board Banner
    announcements = get_announcements_db()
    if announcements:
        latest = announcements[0]
        st.markdown(f"""
        <div class="notice-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#1e40af; font-size:13px;">📢 {latest['title']}</strong>
                <span style="font-size:11px; color:#64748b;">{latest['category']} • {latest['author']}</span>
            </div>
            <div style="font-size:12px; color:#334155; margin-top:4px;">{latest['content']}</div>
        </div>
        """, unsafe_allow_html=True)

    # 1. PERSONAL CREDENTIALS & METRICS
    st.markdown("#### Candidate Placement Overview")
    st.caption("Your verified academic standing, active applications, and interview invitations:")

    student_applied_ids = get_student_applied_job_ids(s_obj["id"])
    all_shortlists = get_all_shortlists_db()
    student_shortlist_count = sum(1 for sh in all_shortlists if sh["student_id"] == s_obj["id"])

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Academic Marks", f"{s_obj.get('cgpa', 7.5)} CGPA")
    with m2:
        st.metric("Verified Skills", f"{len(s_obj.get('technical_skills', []))} Competencies")
    with m3:
        st.metric("Drives Applied", f"{len(student_applied_ids)} Openings")
    with m4:
        st.metric("Interview Shortlists", f"{student_shortlist_count} Confirmed")

    st.write("")

    # 2. STUDENT MAIN TABS
    tab_companies, tab_appls, tab_recs, tab_profile = st.tabs([
        f"Matched Corporate Drives ({len(jobs)})",
        f"My Applications Tracker ({len(student_applied_ids)})",
        "Personalized Preparation Roadmap",
        "My Academic Profile & Skills"
    ])

    # --------------------------------------------------------------------------
    # Tab 1: Matched Companies & Readiness Level
    # --------------------------------------------------------------------------
    with tab_companies:
        st.markdown("##### Visiting Campus Recruitment Drives")
        st.caption("Openings ranked by semantic profile fit. Check eligibility cutoffs and apply in real time:")

        # Search filter
        search_kw = st.text_input("Search drives by role, company, or skill:", placeholder="e.g. Backend, Python, CloudScale, ML")

        ranked_jobs = get_cached_job_rankings(s_obj["id"], jobs)

        filtered_jobs = []
        for r in ranked_jobs:
            j = job_dict[r["job_id"]]
            if search_kw.strip():
                kw = search_kw.lower()
                text_to_search = f"{j['title']} {j['company']} {j.get('domain', '')} {' '.join(j.get('required_skills', []))}".lower()
                if kw not in text_to_search:
                    continue
            filtered_jobs.append((r, j))

        if not filtered_jobs:
            st.info("No corporate drives match your search query.")

        for r, j in filtered_jobs:
            readiness = predict_interview_readiness(s_obj, j, r)
            score = int(r.get("semantic_score", 0.0))
            is_ready = readiness["is_ready"]
            applied = j["job_id"] in student_applied_ids
            shortlisted = is_student_shortlisted_for_job(s_obj["id"], j["job_id"])

            cgpa_ok = float(s_obj.get("cgpa", 7.5)) >= float(j.get("min_cgpa", 0.0))
            exp_ok = int(s_obj.get("experience_months", 0)) >= int(j.get("min_experience_months", 0))

            if is_ready:
                status_pill = '<span class="badge-ready">Ready & Eligible</span>'
            elif cgpa_ok and exp_ok:
                status_pill = '<span class="badge-prep">Needs Skill Preparation</span>'
            else:
                status_pill = '<span class="badge-cutoff">Cutoff Not Met</span>'

            with st.container(border=True):
                jc1, jc2 = st.columns([3, 1])
                with jc1:
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <div style="font-size:16px; font-weight:700; color:#0f172a;">{j['title']}</div>
                            <div style="font-size:13px; font-weight:600; color:#1e40af; margin-top:2px;">{j['company']} • {j.get('domain', 'Technology')}</div>
                            <div style="font-size:12px; color:#64748b; margin-top:4px;">
                                Required Cutoff: <strong>{j.get('min_cgpa', 6.0)} CGPA</strong> &nbsp;|&nbsp; 
                                Min Experience: <strong>{j.get('min_experience_months', 0)} Months</strong>
                            </div>
                        </div>
                        <div>
                            {status_pill}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Match Progress
                    st.markdown(f"""
                    <div style="margin-top:12px; display:flex; align-items:center; gap:10px;">
                        <div style="font-size:13px; font-weight:700; color:#0f172a; width:75px;">{score}% Match</div>
                        <div style="flex-grow:1; background:#f1f5f9; height:6px; border-radius:3px; overflow:hidden;">
                            <div style="background:{'#059669' if score>=70 else ('#d97706' if score>=45 else '#64748b')}; width:{score}%; height:100%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Required Skills
                    st.markdown(f"""
                    <div style="margin-top:10px;">
                        <span style="font-size:11px; font-weight:600; color:#64748b; text-transform:uppercase;">Required Competencies:</span><br>
                        {' '.join([f'<span class="tag-chip-req">{s}</span>' for s in j.get('required_skills', [])])}
                    </div>
                    """, unsafe_allow_html=True)

                    # Missing Skills if any
                    missing = readiness.get("missing_skills", [])
                    if missing:
                        st.markdown(f"""
                        <div style="font-size:12px; color:#9f1239; margin-top:6px;">
                            <strong>Prerequisite Gaps:</strong> {', '.join(missing)}
                        </div>
                        """, unsafe_allow_html=True)

                with jc2:
                    st.write("")
                    if shortlisted:
                        st.markdown('<div class="badge-shortlist" style="width:100%; text-align:center; padding:6px 0; margin-bottom:8px;">Interview Shortlisted</div>', unsafe_allow_html=True)

                    if applied:
                        st.markdown('<div class="badge-ready" style="width:100%; text-align:center; padding:6px 0; margin-bottom:8px;">Application Submitted</div>', unsafe_allow_html=True)
                        if st.button("Withdraw", key=f"withdraw_{j['job_id']}", use_container_width=True):
                            withdraw_application_db(s_obj["id"], j["job_id"])
                            st.toast(f"Withdrew application for {j['title']}.")
                            st.rerun()
                    else:
                        btn_txt = "Apply Now" if is_ready else "Apply (Review Required)"
                        if st.button(btn_txt, key=f"apply_{j['job_id']}", type="primary" if is_ready else "secondary", use_container_width=True):
                            submit_application_db(s_obj["id"], j["job_id"])
                            st.toast(f"Application submitted to {j['company']}!")
                            st.rerun()

    # --------------------------------------------------------------------------
    # Tab 2: My Applications Tracker
    # --------------------------------------------------------------------------
    with tab_appls:
        st.markdown("##### My Submitted Placement Applications")
        st.caption("Real-time tracking of applications submitted to visiting campus employers:")

        stu_appls = get_student_applications_db(s_obj["id"])
        if stu_appls:
            appl_table = []
            for idx, a in enumerate(stu_appls, 1):
                j_info = job_dict.get(a["job_id"], {})
                is_sh = is_student_shortlisted_for_job(s_obj["id"], a["job_id"])
                appl_table.append({
                    "#": idx,
                    "Employer": j_info.get("company", "N/A"),
                    "Position": j_info.get("title", "N/A"),
                    "Date Applied": a.get("applied_at", "Recent"),
                    "Status": "⭐ Interview Shortlisted" if is_sh else a.get("status", "Under Review"),
                    "Cutoff Met": "Yes" if float(s_obj.get("cgpa", 7.5)) >= float(j_info.get("min_cgpa", 0.0)) else "Under Cutoff"
                })
            st.dataframe(pd.DataFrame(appl_table), use_container_width=True, hide_index=True)
        else:
            st.info("You haven't submitted any applications yet. Explore the 'Matched Corporate Drives' tab to apply.")

    # --------------------------------------------------------------------------
    # Tab 3: Personalized Preparation Roadmap
    # --------------------------------------------------------------------------
    with tab_recs:
        st.markdown("##### Personalized Career Preparation Roadmap")
        st.caption("AI-generated preparation strategy based on your skill gaps for target companies:")

        target_company_id = st.selectbox(
            "Select Target Corporate Drive to Inspect:",
            options=list(job_dict.keys()),
            format_func=lambda j_id: f"{job_dict[j_id]['company']} — {job_dict[j_id]['title']}"
        )

        target_job = job_dict[target_company_id]
        kw_data = calculate_keyword_match(s_obj, target_job)
        match_data = calculate_semantic_match(s_obj, target_job)
        readiness_data = predict_interview_readiness(s_obj, target_job, match_data)
        rec_data = generate_recommendations(s_obj, target_job, match_data, kw_data, readiness_data)

        rc1, rc2 = st.columns([1.2, 1], gap="large")
        with rc1:
            with st.container(border=True):
                st.markdown("###### Detailed Skill Match Breakdown")
                rows = []
                for item in match_data.get("required_match_details", []):
                    status_str = "Verified" if item.get("status") == "strong_match" else ("Adjacent" if item.get("status") == "uncertain_match" else "Missing")
                    rows.append({
                        "Company Requirement": item.get("job_skill"),
                        "Verification Status": status_str,
                        "Your Skill": item.get("matched_student_skill") or "Not found"
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with rc2:
            with st.container(border=True):
                st.markdown("###### Recommended Learning Steps")
                recs = rec_data.get("recommendations", [])
                if recs:
                    for idx, r in enumerate(recs, 1):
                        st.markdown(f"""
                        <div style="border-left: 3px solid #1e40af; padding: 10px 12px; background: #f8fafc; border-radius: 4px; margin-bottom: 10px;">
                            <div style="font-size: 13px; font-weight: 700; color: #0f172a;">Phase {idx}: Learn {r['skill']}</div>
                            <div style="font-size: 12px; color: #475569; margin: 4px 0;">{r['reason']}</div>
                            <div style="font-size: 11px; color: #1e40af; font-weight: 600;">Course: {r['recommended_course']}</div>
                            <div style="font-size: 11px; color: #059669;">Lab: {r['suggested_project']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("You already meet all technical skill requirements for this position!")

    # --------------------------------------------------------------------------
    # Tab 4: My Profile & Skills Dossier
    # --------------------------------------------------------------------------
    with tab_profile:
        pc1, pc2 = st.columns([3, 1])
        with pc1:
            st.markdown("##### My Placement Dossier")
            st.caption("Official university academic record and verified credentials presented to recruiters:")
        with pc2:
            if st.button("Update Profile & Skills", type="primary", use_container_width=True):
                modal_update_profile(s_obj)

        with st.container(border=True):
            p_col1, p_col2 = st.columns([1, 2], gap="large")
            with p_col1:
                st.markdown(f"""
                <div class="app-crest" style="width:52px; height:52px; font-size:20px; margin-bottom:12px;">
                    {get_initials(s_obj['name'])}
                </div>
                <div style="font-size:18px; font-weight:700; color:#0f172a;">{s_obj['name']}</div>
                <div style="font-size:12px; color:#64748b;">UID: {s_obj['id']}</div>
                <div style="font-size:12px; color:#1e40af; margin-top:2px;">{s_obj.get('email', 'student@university.edu')}</div>
                <div style="font-size:12px; color:#475569; margin-top:4px;">{s_obj.get('branch', 'Computer Science & Engineering')}</div>
                """, unsafe_allow_html=True)

                st.write("")
                st.metric("Academic Marks", f"{s_obj.get('cgpa', 7.5)} CGPA")
                st.metric("Internship Experience", f"{s_obj.get('experience_months', 0)} Months")

            with p_col2:
                st.markdown("###### Verified Technical Competencies")
                st.markdown(' '.join([f'<span class="tag-chip">{s}</span>' for s in s_obj.get('technical_skills', [])]), unsafe_allow_html=True)

                st.write("")
                st.markdown("###### Capstone Portfolio Project")
                projs = s_obj.get("projects", [])
                if projs:
                    p = projs[0]
                    st.markdown(f"""
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px 14px; margin-top:6px;">
                        <div style="font-size:14px; font-weight:700; color:#0f172a;">{p.get('title', 'Capstone Project')}</div>
                        <div style="font-size:13px; color:#475569; margin-top:4px; line-height:1.4;">{p.get('description', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)


# ==============================================================================
# DASHBOARD 2: CORPORATE RECRUITER WORKSPACE (POST JOBS, VIEW APPLIED, SHORTLIST)
# ==============================================================================
elif st.session_state.auth_role == "recruiter":
    # 1. HEADER & JOB ROLE SELECTOR
    r_hdr_1, r_hdr_2 = st.columns([3, 1], vertical_alignment="center")

    company_jobs = [j for j in jobs if j["company"] == st.session_state.current_recruiter_company]
    if not company_jobs:
        company_jobs = jobs[:1]

    with r_hdr_1:
        st.markdown(f"#### {st.session_state.current_recruiter_company} Recruitment Workspace")
        st.caption("Review candidate applications, screen eligibility cutoffs, and shortlist for technical interviews:")

    with r_hdr_2:
        if st.button("+ Post New Job Role", type="primary", use_container_width=True):
            modal_post_job()

    st.write("")

    # Select Active Job under review
    job_ids = [j["job_id"] for j in company_jobs]
    default_job_idx = job_ids.index(st.session_state.current_recruiter_job_id) if st.session_state.current_recruiter_job_id in job_ids else 0

    sel_rec_job_id = st.selectbox(
        "Active Position under Review:",
        options=job_ids,
        index=default_job_idx,
        format_func=lambda j_id: f"{job_dict[j_id]['title']} (Cutoff: {job_dict[j_id].get('min_cgpa', 6.0)} CGPA)"
    )
    st.session_state.current_recruiter_job_id = sel_rec_job_id
    active_job = job_dict[sel_rec_job_id]

    # Live Shortlists & Applications from SQLite
    live_shortlisted_ids = get_job_shortlisted_student_ids(active_job["job_id"])
    all_appls_for_job = [a for a in get_all_applications_db() if a["job_id"] == active_job["job_id"]]
    live_applied_ids = {a["student_id"] for a in all_appls_for_job}

    with st.container(border=True):
        jc1, jc2, jc3, jc4 = st.columns(4)
        with jc1:
            st.metric("Position Title", active_job["title"])
        with jc2:
            st.metric("Marks Cutoff", f"{active_job.get('min_cgpa', 6.0)} CGPA")
        with jc3:
            st.metric("Direct Applications", f"{len(live_applied_ids)} Candidates")
        with jc4:
            st.metric("Shortlisted for Interview", f"{len(live_shortlisted_ids)} Nominees")

    st.write("")

    # 2. CANDIDATE PIPELINE RANKED BY BEST MATCH
    st.markdown("##### Candidate Evaluation & Shortlisting Pipeline")
    st.caption("Candidates ranked using Sentence Transformer semantic match against job requirements:")

    filt_choice = st.radio(
        "Filter Candidate Pipeline:",
        options=["Applied Candidates Only", "All Qualified Batch Students", "Shortlisted for Interview"],
        horizontal=True
    )

    # Calculate Rankings for this Job
    ranked_candidates = []
    for s in students:
        sem_res = calculate_semantic_match(s, active_job)
        read_res = predict_interview_readiness(s, active_job, sem_res)
        score = int(sem_res.get("semantic_score", 0.0))
        is_appl = s["id"] in live_applied_ids
        is_short = s["id"] in live_shortlisted_ids

        ranked_candidates.append({
            "id": s["id"],
            "name": s["name"],
            "email": s.get("email", "student@university.edu"),
            "branch": s.get("branch", "Computer Science"),
            "cgpa": s.get("cgpa", 7.5),
            "experience": f"{s.get('experience_months', 0)} Mo",
            "score": score,
            "is_ready": read_res["is_ready"],
            "applied": is_appl,
            "shortlisted": is_short,
            "skills": ", ".join(s.get("technical_skills", [])[:4]),
            "missing": ", ".join(read_res.get("missing_skills", [])) or "None"
        })

    # Sort: Applied candidates first, then best match score
    ranked_candidates.sort(key=lambda x: (x["applied"], x["score"]), reverse=True)

    # Filter
    if filt_choice == "Applied Candidates Only":
        display_candidates = [c for c in ranked_candidates if c["applied"]]
    elif filt_choice == "Shortlisted for Interview":
        display_candidates = [c for c in ranked_candidates if c["shortlisted"]]
    else:
        display_candidates = [c for c in ranked_candidates if c["is_ready"]]

    # Table View
    if display_candidates:
        table_rows = []
        for idx, c in enumerate(display_candidates, 1):
            table_rows.append({
                "Rank": f"#{idx}",
                "Candidate Name": c["name"],
                "Department": c["branch"],
                "College Marks": f"{c['cgpa']} CGPA",
                "Experience": c["experience"],
                "Match Score": f"{c['score']}%",
                "Applied?": "✅ Applied" if c["applied"] else "No",
                "Shortlist Status": "⭐ Shortlisted" if c["shortlisted"] else "Pending",
                "Verified Skills": c["skills"]
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No candidates match the selected filter.")

    # 3. SHORTLIST CANDIDATE & REAL CSV EXPORT
    st.write("")
    st.markdown("##### Candidate Shortlist Decision")
    act_col1, act_col2, act_col3 = st.columns([2, 1, 1], vertical_alignment="bottom")

    with act_col1:
        target_nominee_id = st.selectbox(
            "Select Candidate to Shortlist / Nominate for Interview:",
            options=[c["id"] for c in display_candidates] if display_candidates else [s["id"] for s in students],
            format_func=lambda s_id: f"{student_dict[s_id]['name']} — UID: {s_id} ({student_dict[s_id].get('cgpa', 7.5)} CGPA)"
        )

    with act_col2:
        is_cur_short = target_nominee_id in live_shortlisted_ids
        btn_short_txt = "Remove from Shortlist" if is_cur_short else "Shortlist Candidate"
        if st.button(btn_short_txt, type="secondary" if is_cur_short else "primary", use_container_width=True):
            toggle_shortlist_db(active_job["job_id"], target_nominee_id)
            st.toast(f"Shortlist updated for candidate {student_dict[target_nominee_id]['name']}!")
            st.rerun()

    with act_col3:
        if display_candidates:
            df_export = pd.DataFrame(table_rows)
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Export Shortlist (CSV)",
                data=csv_data,
                file_name=f"{active_job['company']}_{active_job['title']}_Candidates.csv",
                mime="text/csv",
                use_container_width=True
            )


# ==============================================================================
# DASHBOARD 3: UNIVERSITY PLACEMENT PORTAL (TPO DIRECTORATE)
# ==============================================================================
else:
    # 1. TPO TOPBAR & ANNOUNCEMENT BUTTON
    t_hdr1, t_hdr2 = st.columns([3, 1], vertical_alignment="center")
    with t_hdr1:
        st.markdown("#### Directorate of Career Services & Campus Placements")
        st.caption("Institutional management dashboard for campus recruitment drives, student placement tracking, and market analytics:")
    with t_hdr2:
        if st.button("📢 Post Campus Notice", type="primary", use_container_width=True):
            modal_add_announcement()

    st.write("")

    # 2. MACRO CAMPUS METRICS (LIVE FROM SQLITE)
    all_appls = get_all_applications_db()
    all_shorts = get_all_shortlists_db()
    tot_stus = len(students)
    tot_drives = len(jobs)
    total_shortlist_count = len(all_shorts)
    unique_placed_stus = len(set(s["student_id"] for s in all_shorts))
    placement_rate = round((unique_placed_stus / max(tot_stus, 1)) * 100, 1)
    avg_cgpa = round(sum(s.get("cgpa", 7.5) for s in students) / max(tot_stus, 1), 2)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Enrolled Batch", f"{tot_stus} Students")
    with kpi2:
        st.metric("Visiting Companies", f"{tot_drives} Employers")
    with kpi3:
        st.metric("Interview Nominations", f"{total_shortlist_count} Confirmed")
    with kpi4:
        st.metric("Campus Placement Rate", f"{placement_rate}%")

    st.write("")

    # 3. TPO TABS
    tpo_tab_analytics, tpo_tab_students, tpo_tab_drives = st.tabs([
        "Placement Intelligence & Market Demand BI",
        f"Master Student Placement Roster ({tot_stus})",
        f"Visiting Corporate Recruitment Drives ({tot_drives})"
    ])

    # --------------------------------------------------------------------------
    # Tab 1: Analytics & Market Demand BI
    # --------------------------------------------------------------------------
    with tpo_tab_analytics:
        st.markdown("##### Market Demand vs. Student Batch Competencies")
        st.caption("Empirical comparison of market requirements demanded by visiting employers vs. competencies verified across graduating candidates:")

        c_an1, c_an2 = st.columns(2, gap="large")

        with c_an1:
            with st.container(border=True):
                st.markdown("###### Skills Demanded by Visiting Companies")
                skill_counts = {}
                for j in jobs:
                    for sk in j.get("required_skills", []):
                        skill_counts[sk] = skill_counts.get(sk, 0) + 1

                df_demand = pd.DataFrame(
                    sorted(skill_counts.items(), key=lambda x: x[1], reverse=True),
                    columns=["Technical Skill", "Employer Demand"]
                )
                st.bar_chart(df_demand.set_index("Technical Skill"), color="#1e40af")

        with c_an2:
            with st.container(border=True):
                st.markdown("###### Skills Possessed by Graduating Students")
                stu_skill_counts = {}
                for s in students:
                    for sk in s.get("technical_skills", []):
                        stu_skill_counts[sk] = stu_skill_counts.get(sk, 0) + 1

                df_supply = pd.DataFrame(
                    sorted(stu_skill_counts.items(), key=lambda x: x[1], reverse=True),
                    columns=["Technical Skill", "Proficient Students"]
                )
                st.bar_chart(df_supply.set_index("Technical Skill"), color="#059669")

        # Official Master Shortlist Audit Table
        st.write("")
        with st.container(border=True):
            st.markdown("###### Official Master Shortlist Audit Record (Live SQLite)")
            audit_rows = []
            for sh in all_shorts:
                j_obj = job_dict.get(sh["job_id"], {})
                s_obj = student_dict.get(sh["student_id"], {})
                audit_rows.append({
                    "Visiting Employer": j_obj.get("company", "N/A"),
                    "Position": j_obj.get("title", "N/A"),
                    "Candidate Name": s_obj.get("name", "N/A"),
                    "Department": s_obj.get("branch", "Engineering"),
                    "Marks": f"{s_obj.get('cgpa', 7.5)} CGPA",
                    "Interview Stage": sh.get("interview_round", "Round 1 Technical"),
                    "Scheduled Timestamp": sh.get("shortlisted_at", "Confirmed")
                })

            if audit_rows:
                st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No candidates nominated for interviews yet.")

    # --------------------------------------------------------------------------
    # Tab 2: Master Student Roster
    # --------------------------------------------------------------------------
    with tpo_tab_students:
        st.markdown("##### Enrolled Student Placement Directory")
        st.caption("Central directory of registered graduating candidates with application and shortlist tracking:")

        tpo_stu_filter = st.radio(
            "Filter Student Roster:",
            options=["All Enrolled Candidates", "Shortlisted Candidates Only", "Candidates with Submitted Applications", "Registered / Available"],
            horizontal=True
        )

        stu_dir_data = []
        for idx, s in enumerate(students, 1):
            s_appls = get_student_applications_db(s["id"])
            s_shorts = [sh for sh in all_shorts if sh["student_id"] == s["id"]]
            shortlisted_drives = [
                f"{job_dict[sh['job_id']]['company']} ({job_dict[sh['job_id']]['title']})"
                for sh in s_shorts
                if sh["job_id"] in job_dict
            ]
            shortlisted_str = " • ".join(shortlisted_drives) if shortlisted_drives else "None"
            is_sh = len(s_shorts) > 0
            has_appls = len(s_appls) > 0

            # Filter check
            if tpo_stu_filter == "Shortlisted Candidates Only" and not is_sh:
                continue
            if tpo_stu_filter == "Candidates with Submitted Applications" and not has_appls:
                continue
            if tpo_stu_filter == "Registered / Available" and (is_sh or has_appls):
                continue

            stu_dir_data.append({
                "#": idx,
                "Candidate Name": s["name"],
                "UID": s["id"],
                "Department": s.get("branch", "Computer Science"),
                "Academic Marks": f"{s.get('cgpa', 7.5)} CGPA",
                "Applications Sent": f"{len(s_appls)} Drives",
                "Shortlist Count": f"{len(s_shorts)} Drives" if is_sh else "0 Drives",
                "Shortlisted For Drives": shortlisted_str,
                "Placement Status": "⭐ Shortlisted" if is_sh else ("Applied" if has_appls else "Registered"),
                "Verified Competencies": ", ".join(s.get("technical_skills", [])[:4])
            })

        if stu_dir_data:
            st.dataframe(pd.DataFrame(stu_dir_data), use_container_width=True, hide_index=True)
        else:
            st.info("No candidates match the selected filter.")

        # Export Full Placement Report
        if stu_dir_data:
            csv_tpo_report = pd.DataFrame(stu_dir_data).to_csv(index=False).encode('utf-8')
            st.download_button(
                "Export Institutional Placement Report (CSV)",
                data=csv_tpo_report,
                file_name="University_Placement_Roster_2026.csv",
                mime="text/csv",
                use_container_width=True
            )

    # --------------------------------------------------------------------------
    # Tab 3: Visiting Campus Drives
    # --------------------------------------------------------------------------
    with tpo_tab_drives:
        d_c1, d_c2 = st.columns([3, 1], vertical_alignment="center")
        with d_c1:
            st.markdown("##### Visiting Corporate Recruitment Drives")
        with d_c2:
            if st.button("Schedule Campus Drive", type="primary", use_container_width=True):
                modal_post_job()

        d_rows = []
        for idx, j in enumerate(jobs, 1):
            sh_count = len(get_job_shortlists_db(j["job_id"]))
            appl_count = sum(1 for a in all_appls if a["job_id"] == j["job_id"])
            d_rows.append({
                "#": idx,
                "Employer": j["company"],
                "Position": j["title"],
                "CGPA Cutoff": f"{j.get('min_cgpa', 6.0)} CGPA",
                "Min Experience": f"{j.get('min_experience_months', 0)} Mo",
                "Applications": f"{appl_count} Candidates",
                "Shortlisted Nominees": f"{sh_count} Candidates",
                "Required Skills": ", ".join(j.get("required_skills", []))
            })

        st.dataframe(pd.DataFrame(d_rows), use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# 7. INSTITUTIONAL FOOTER
# ------------------------------------------------------------------------------
st.markdown("""
<div style="border-top:1px solid #e2e8f0; margin-top:40px; padding:18px 0; display:flex; justify-content:space-between; align-items:center; font-size:12px; color:#64748b;">
    <div><strong>TalentBridge</strong> • Campus Recruitment & Career Placement Suite</div>
    <div>Academic Session 2026–2027 • Directorate of Career Services</div>
</div>
""", unsafe_allow_html=True)
