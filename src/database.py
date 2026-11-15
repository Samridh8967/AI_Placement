"""
SQLite Persistence Module
--------------------------
Provides a clean, local database using Python's standard `sqlite3` library.
Stores student profiles, recruiter job postings, and match history.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "placement_system.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Returns a SQLite connection configured with Row factory for dict-like access."""
    path = db_path or DB_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None):
    """
    Initializes tables:
    - students: stores candidate profiles
    - jobs: stores recruiter job listings
    - match_history: logs evaluations for auditing and analytics
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # 1. Students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                experience_months INTEGER DEFAULT 0,
                technical_skills TEXT,   -- JSON array string
                coursework TEXT,         -- JSON array string
                projects TEXT,           -- JSON array of dicts string
                internship_experience TEXT,
                preferred_domains TEXT,  -- JSON array string
                career_interests TEXT    -- JSON array string
            )
        """)

        # 2. Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                domain TEXT,
                description TEXT,
                required_skills TEXT,     -- JSON array string
                preferred_skills TEXT,    -- JSON array string
                min_experience_months INTEGER DEFAULT 0,
                required_coursework TEXT, -- JSON array string
                min_cgpa REAL DEFAULT 0.0
            )
        """)

        # 3. Match History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                student_id TEXT,
                job_id TEXT,
                keyword_score REAL,
                semantic_score REAL,
                readiness_status TEXT,
                confidence REAL,
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(job_id) REFERENCES jobs(job_id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def seed_db_from_json(db_path: Optional[Path] = None):
    """Populates SQLite from existing JSON files if tables are empty."""
    from data_loader import load_all_students, load_all_jobs

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        if cursor.fetchone()[0] == 0:
            for s in load_all_students():
                cursor.execute("""
                    INSERT OR REPLACE INTO students 
                    (id, name, email, experience_months, technical_skills, coursework, projects, internship_experience, preferred_domains, career_interests)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    s["id"], s["name"], s["email"], s["experience_months"],
                    json.dumps(s["technical_skills"]),
                    json.dumps(s["coursework"]),
                    json.dumps(s["projects"]),
                    s["internship_experience"],
                    json.dumps(s["preferred_domains"]),
                    json.dumps(s["career_interests"])
                ))
            conn.commit()

        cursor.execute("SELECT COUNT(*) FROM jobs")
        if cursor.fetchone()[0] == 0:
            for j in load_all_jobs():
                cursor.execute("""
                    INSERT OR REPLACE INTO jobs
                    (job_id, title, company, domain, description, required_skills, preferred_skills, min_experience_months, required_coursework, min_cgpa)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    j["job_id"], j["title"], j["company"], j["domain"], j["description"],
                    json.dumps(j["required_skills"]),
                    json.dumps(j["preferred_skills"]),
                    j["min_experience_months"],
                    json.dumps(j["required_coursework"]),
                    j["min_cgpa"]
                ))
            conn.commit()
    finally:
        conn.close()


def get_all_students_db(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieves all student profiles, deserializing JSON arrays."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY id ASC")
        rows = cursor.fetchall()
        students = []
        for r in rows:
            students.append({
                "id": r["id"],
                "name": r["name"],
                "email": r["email"],
                "experience_months": r["experience_months"],
                "technical_skills": json.loads(r["technical_skills"] or "[]"),
                "coursework": json.loads(r["coursework"] or "[]"),
                "projects": json.loads(r["projects"] or "[]"),
                "internship_experience": r["internship_experience"] or "",
                "preferred_domains": json.loads(r["preferred_domains"] or "[]"),
                "career_interests": json.loads(r["career_interests"] or "[]"),
                "cgpa": float(r["cgpa"]) if ("cgpa" in r.keys() and r["cgpa"] is not None) else 7.5,
                "branch": r["branch"] if ("branch" in r.keys() and r["branch"]) else "Computer Science & Engineering"
            })
        return students
    finally:
        conn.close()


def get_all_jobs_db(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieves all job listings, deserializing JSON arrays."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY job_id ASC")
        rows = cursor.fetchall()
        jobs = []
        for r in rows:
            jobs.append({
                "job_id": r["job_id"],
                "title": r["title"],
                "company": r["company"],
                "domain": r["domain"],
                "description": r["description"],
                "required_skills": json.loads(r["required_skills"] or "[]"),
                "preferred_skills": json.loads(r["preferred_skills"] or "[]"),
                "min_experience_months": r["min_experience_months"],
                "required_coursework": json.loads(r["required_coursework"] or "[]"),
                "min_cgpa": r["min_cgpa"],
            })
        return jobs
    finally:
        conn.close()


def save_student_db(student: Dict[str, Any], db_path: Optional[Path] = None):
    """Inserts or updates a student profile in SQLite."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO students 
            (id, name, email, experience_months, technical_skills, coursework, projects, internship_experience, preferred_domains, career_interests, cgpa, branch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student["id"], student["name"], student["email"], student.get("experience_months", 0),
            json.dumps(student.get("technical_skills", [])),
            json.dumps(student.get("coursework", [])),
            json.dumps(student.get("projects", [])),
            student.get("internship_experience", ""),
            json.dumps(student.get("preferred_domains", [])),
            json.dumps(student.get("career_interests", [])),
            float(student.get("cgpa", 7.5)),
            student.get("branch", "Computer Science & Engineering")
        ))
        conn.commit()
    finally:
        conn.close()


def save_job_db(job: Dict[str, Any], db_path: Optional[Path] = None):
    """Inserts or updates a job posting in SQLite."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO jobs
            (job_id, title, company, domain, description, required_skills, preferred_skills, min_experience_months, required_coursework, min_cgpa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job["job_id"], job["title"], job["company"], job.get("domain", "General"), job.get("description", ""),
            json.dumps(job.get("required_skills", [])),
            json.dumps(job.get("preferred_skills", [])),
            job.get("min_experience_months", 0),
            json.dumps(job.get("required_coursework", [])),
            job.get("min_cgpa", 0.0)
        ))
        conn.commit()
    finally:
        conn.close()


def log_match_history_db(
    student_id: str, 
    job_id: str, 
    kw_score: float, 
    sem_score: float, 
    status: str, 
    conf: float,
    db_path: Optional[Path] = None
):
    """Logs evaluation to match_history table."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO match_history (student_id, job_id, keyword_score, semantic_score, readiness_status, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, job_id, kw_score, sem_score, status, conf))
        conn.commit()
    finally:
        conn.close()


def get_match_history_db(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieves all logged evaluations."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM match_history ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_student_applications_db(student_id: str, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE student_id = ? ORDER BY applied_at DESC", (student_id,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def submit_application_db(student_id: str, job_id: str, db_path: Optional[Path] = None) -> bool:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO applications (student_id, job_id, status) VALUES (?, ?, 'Under Review')", (student_id, job_id))
        conn.commit()
        return True
    finally:
        conn.close()


def withdraw_application_db(student_id: str, job_id: str, db_path: Optional[Path] = None) -> bool:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications WHERE student_id = ? AND job_id = ?", (student_id, job_id))
        conn.commit()
        return True
    finally:
        conn.close()


def get_all_applications_db(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications ORDER BY applied_at DESC")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_job_shortlists_db(job_id: str, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shortlists WHERE job_id = ? ORDER BY shortlisted_at DESC", (job_id,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def toggle_shortlist_db(job_id: str, student_id: str, round_name: str = "Round 1: Technical Interview", db_path: Optional[Path] = None) -> bool:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM shortlists WHERE job_id = ? AND student_id = ?", (job_id, student_id))
        if cursor.fetchone():
            cursor.execute("DELETE FROM shortlists WHERE job_id = ? AND student_id = ?", (job_id, student_id))
            is_now_shortlisted = False
        else:
            cursor.execute("INSERT INTO shortlists (job_id, student_id, interview_round) VALUES (?, ?, ?)", (job_id, student_id, round_name))
            cursor.execute("UPDATE applications SET status = 'Shortlisted' WHERE student_id = ? AND job_id = ?", (student_id, job_id))
            is_now_shortlisted = True
        conn.commit()
        return is_now_shortlisted
    finally:
        conn.close()


def get_all_shortlists_db(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shortlists ORDER BY shortlisted_at DESC")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_announcements_db(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 10")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def add_announcement_db(title: str, content: str, category: str = "General", author: str = "Directorate of Placements", db_path: Optional[Path] = None) -> bool:
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO announcements (title, content, category, author) VALUES (?, ?, ?, ?)", (title, content, category, author))
        conn.commit()
        return True
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  TESTING SQLITE PERSISTENCE MODULE")
    print("=" * 60)
    seed_db_from_json()
    students = get_all_students_db()
    jobs = get_all_jobs_db()
    print(f"[+] Loaded {len(students)} students from SQLite database.")
    print(f"[+] Loaded {len(jobs)} jobs from SQLite database.")
    print(f"[+] Database location: {DB_FILE}")
    print("=" * 60)
