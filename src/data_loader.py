"""
Data Loader & Profile Validation Module
----------------------------------------
This module handles:
1. Loading raw JSON profile files for students and job descriptions.
2. Defensive data validation (handling missing fields, None values, whitespace, and duplicates).
3. Ensuring standard data structures for downstream matching engines.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json_file(file_path: Path) -> Any:
    """
    Safely reads a JSON file from disk.
    
    Args:
        file_path (Path): Absolute or relative path to the JSON file.
        
    Returns:
        Any: Parsed JSON data (usually a list of dictionaries).
        
    Raises:
        FileNotFoundError: If the target file does not exist.
        ValueError: If the file is not valid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found at: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as err:
        raise ValueError(f"File {file_path} contains invalid JSON: {err}")


def clean_skill_list(skills: Optional[List[Any]]) -> List[str]:
    """
    Cleans a list of skills by:
    - Skipping non-string or None items.
    - Stripping leading and trailing whitespace.
    - Removing duplicates while preserving the original order.
    
    Example:
        [" Python ", "SQL", "python", ""] -> ["Python", "SQL"]
    """
    if not skills or not isinstance(skills, list):
        return []

    cleaned = []
    seen_lower = set()

    for item in skills:
        if isinstance(item, str):
            trimmed = item.strip()
            if trimmed and trimmed.lower() not in seen_lower:
                cleaned.append(trimmed)
                seen_lower.add(trimmed.lower())

    return cleaned


def validate_student_profile(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and normalizes a student profile dictionary.
    Guarantees that all required keys exist with safe default types,
    preventing runtime errors in downstream matching modules.
    
    Args:
        raw (dict): Raw student data loaded from JSON or form input.
        
    Returns:
        dict: Cleaned and validated student profile.
    """
    # 1. Experience months validation (handle None, negative numbers, or invalid strings)
    raw_exp = raw.get("experience_months")
    try:
        experience_months = int(raw_exp) if raw_exp is not None else 0
        if experience_months < 0:
            experience_months = 0
    except (ValueError, TypeError):
        experience_months = 0

    # 2. Extract and clean skills
    technical_skills = clean_skill_list(raw.get("technical_skills", []))
    coursework = clean_skill_list(raw.get("coursework", []))
    preferred_domains = clean_skill_list(raw.get("preferred_domains", []))
    career_interests = clean_skill_list(raw.get("career_interests", []))

    # 3. Clean project entries
    raw_projects = raw.get("projects", [])
    cleaned_projects = []
    if isinstance(raw_projects, list):
        for p in raw_projects:
            if isinstance(p, dict):
                cleaned_projects.append({
                    "title": str(p.get("title", "Untitled Project")).strip(),
                    "description": str(p.get("description", "")).strip(),
                    "skills_used": clean_skill_list(p.get("skills_used", []))
                })

    return {
        "id": str(raw.get("id", "UNKNOWN_ID")).strip(),
        "name": str(raw.get("name", "Anonymous Candidate")).strip(),
        "email": str(raw.get("email", "")).strip(),
        "technical_skills": technical_skills,
        "coursework": coursework,
        "projects": cleaned_projects,
        "internship_experience": str(raw.get("internship_experience", "")).strip(),
        "experience_months": experience_months,
        "preferred_domains": preferred_domains,
        "career_interests": career_interests,
    }


def validate_job_profile(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and normalizes a recruiter job listing dictionary.
    Distinguishes mandatory required skills from preferred skills.
    
    Args:
        raw (dict): Raw job posting data.
        
    Returns:
        dict: Cleaned and validated job profile.
    """
    raw_exp = raw.get("min_experience_months")
    try:
        min_experience = int(raw_exp) if raw_exp is not None else 0
        if min_experience < 0:
            min_experience = 0
    except (ValueError, TypeError):
        min_experience = 0

    raw_cgpa = raw.get("min_cgpa")
    try:
        min_cgpa = float(raw_cgpa) if raw_cgpa is not None else 0.0
    except (ValueError, TypeError):
        min_cgpa = 0.0

    return {
        "job_id": str(raw.get("job_id", "UNKNOWN_JOB")).strip(),
        "title": str(raw.get("title", "Untitled Job")).strip(),
        "company": str(raw.get("company", "Unknown Organization")).strip(),
        "domain": str(raw.get("domain", "General")).strip(),
        "description": str(raw.get("description", "")).strip(),
        "required_skills": clean_skill_list(raw.get("required_skills", [])),
        "preferred_skills": clean_skill_list(raw.get("preferred_skills", [])),
        "min_experience_months": min_experience,
        "required_coursework": clean_skill_list(raw.get("required_coursework", [])),
        "min_cgpa": min_cgpa,
    }


def load_all_students(file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Loads and validates all student profiles from JSON."""
    if file_path is None:
        base_dir = Path(__file__).resolve().parent.parent
        file_path = base_dir / "data" / "students.json"
        
    raw_list = load_json_file(file_path)
    if not isinstance(raw_list, list):
        raise ValueError("Students data must be a JSON array of objects.")
        
    return [validate_student_profile(item) for item in raw_list]


def load_all_jobs(file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Loads and validates all job postings from JSON."""
    if file_path is None:
        base_dir = Path(__file__).resolve().parent.parent
        file_path = base_dir / "data" / "jobs.json"
        
    raw_list = load_json_file(file_path)
    if not isinstance(raw_list, list):
        raise ValueError("Jobs data must be a JSON array of objects.")
        
    return [validate_job_profile(item) for item in raw_list]


# Demonstration and quick test when run directly
if __name__ == "__main__":
    print("=" * 60)
    print("  TESTING DATA LOADER & PROFILE VALIDATION")
    print("=" * 60)

    students = load_all_students()
    jobs = load_all_jobs()

    print(f"\n[+] Successfully loaded and validated {len(students)} students:")
    for s in students:
        print(f"  - [{s['id']}] {s['name']}: {len(s['technical_skills'])} skills, {s['experience_months']} mos exp, {len(s['projects'])} projects")

    print(f"\n[+] Successfully loaded and validated {len(jobs)} jobs:")
    for j in jobs:
        print(f"  - [{j['job_id']}] {j['title']} @ {j['company']}: {len(j['required_skills'])} required, {len(j['preferred_skills'])} preferred")

    # Inspect the edge-case candidate to confirm safe handling
    edge_candidate = students[-1]
    print(f"\n[*] Edge Case Candidate Verification:")
    print(f"    Name: {edge_candidate['name']}")
    print(f"    Skills: {edge_candidate['technical_skills']} (type: {type(edge_candidate['technical_skills'])})")
    print(f"    Experience: {edge_candidate['experience_months']} (type: {type(edge_candidate['experience_months'])})")
    print("\n[+] Validation logic handled missing/null values safely without crashing!")
    print("=" * 60)
