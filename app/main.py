"""
FastAPI Backend Application
---------------------------
Exposes RESTful endpoints for placement matching, ranking, and interview readiness.
Run using:
    uvicorn app.main:app --reload --port 8000
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src/ is accessible
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    # If fastapi is not installed yet, provide helpful instruction
    raise ImportError("FastAPI/Uvicorn is required. Install via: pip install fastapi uvicorn")

from database import (
    seed_db_from_json, get_all_students_db, get_all_jobs_db,
    save_student_db, save_job_db
)
from keyword_matcher import calculate_keyword_match
from semantic_matcher import calculate_semantic_match, rank_jobs_semantically
from readiness_model import predict_interview_readiness, train_and_evaluate_models
from recommender import generate_recommendations

# Initialize Database on app start
seed_db_from_json()

app = FastAPI(
    title="University Placement AI Backend",
    description="REST API for semantic skill matching, job ranking, and interview readiness classification.",
    version="1.0.0"
)


# Pydantic Schemas for Request Validation
class StudentProfileSchema(BaseModel):
    id: str
    name: str
    email: Optional[str] = ""
    experience_months: Optional[int] = 0
    technical_skills: List[str] = []
    coursework: List[str] = []
    projects: List[Dict[str, Any]] = []
    internship_experience: Optional[str] = ""
    preferred_domains: List[str] = []
    career_interests: List[str] = []


class JobListingSchema(BaseModel):
    job_id: str
    title: str
    company: str
    domain: Optional[str] = "General"
    description: Optional[str] = ""
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    min_experience_months: Optional[int] = 0
    required_coursework: List[str] = []
    min_cgpa: Optional[float] = 6.0


class MatchRequestSchema(BaseModel):
    student_id: str
    job_id: str


@app.get("/")
def read_root():
    return {
        "project": "University Placement Skill-Match Ranking & Interview Readiness System",
        "problem_id": "LPU-PLACEMENT-01",
        "status": "Online",
        "docs_url": "/docs"
    }


@app.get("/api/students")
def list_students():
    return get_all_students_db()


@app.get("/api/jobs")
def list_jobs():
    return get_all_jobs_db()


@app.post("/api/match/keyword")
def api_keyword_match(req: MatchRequestSchema):
    students = {s["id"]: s for s in get_all_students_db()}
    jobs = {j["job_id"]: j for j in get_all_jobs_db()}

    if req.student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    if req.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return calculate_keyword_match(students[req.student_id], jobs[req.job_id])


@app.post("/api/match/semantic")
def api_semantic_match(req: MatchRequestSchema):
    students = {s["id"]: s for s in get_all_students_db()}
    jobs = {j["job_id"]: j for j in get_all_jobs_db()}

    if req.student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    if req.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return calculate_semantic_match(students[req.student_id], jobs[req.job_id])


@app.post("/api/readiness")
def api_interview_readiness(req: MatchRequestSchema):
    students = {s["id"]: s for s in get_all_students_db()}
    jobs = {j["job_id"]: j for j in get_all_jobs_db()}

    if req.student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    if req.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    student = students[req.student_id]
    job = jobs[req.job_id]
    sem_res = calculate_semantic_match(student, job)
    return predict_interview_readiness(student, job, sem_res)


@app.post("/api/recommendations")
def api_recommendations(req: MatchRequestSchema):
    students = {s["id"]: s for s in get_all_students_db()}
    jobs = {j["job_id"]: j for j in get_all_jobs_db()}

    if req.student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    if req.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    student = students[req.student_id]
    job = jobs[req.job_id]
    sem_res = calculate_semantic_match(student, job)
    kw_res = calculate_keyword_match(student, job)
    readiness = predict_interview_readiness(student, job, sem_res)

    return generate_recommendations(student, job, sem_res, kw_res, readiness)


@app.get("/api/evaluation")
def api_evaluation():
    eval_res = train_and_evaluate_models()
    return {
        "test_samples": eval_res["test_samples"],
        "logistic_regression": eval_res["logistic_regression"],
        "random_forest": eval_res["random_forest"]
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
