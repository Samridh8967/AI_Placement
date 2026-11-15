#keyword matcher
from typing import Any, Dict, List, Tuple
from pathlib import Path


def normalize_skill(skill: str) -> str:
   
#changing the skill to lowercase for simple comaprison

    if not skill or not isinstance(skill, str):
        return ""
    return skill.strip().lower()


def match_skill_lists(
    job_skills: List[str], 
    student_skills: List[str]
) -> Tuple[List[str], List[str]]:
    """
    Compares a list of job skills against student skills using exact matching.
    
    Args:
        job_skills: The skills required or preferred by the job.
        student_skills: The skills listed on the student profile.
        
    Returns:
        tuple: (matched_skills, missing_skills) preserving the job's display naming.
    """
    # Create a set of normalized student skills for O(1) fast lookup
    normalized_student_skills = {
        normalize_skill(s) for s in student_skills if normalize_skill(s)
    }

    matched = []
    missing = []

    for skill in job_skills:
        clean_target = normalize_skill(skill)
        if clean_target in normalized_student_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def calculate_keyword_match(
    student: Dict[str, Any], 
    job: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculates the baseline keyword match score between a single student and a job.
    
    Logic:
    1. Checks mandatory required skills.
    2. Checks preferred skills.
    3. Checks experience eligibility (months).
    4. Calculates required coverage and overall baseline score.
    
    Returns:
        dict: Detailed match metrics and lists.
    """
    student_skills = student.get("technical_skills", [])
    required_skills = job.get("required_skills", [])
    preferred_skills = job.get("preferred_skills", [])

    # 1. Match Required Skills
    matched_req, missing_req = match_skill_lists(required_skills, student_skills)
    total_req = len(required_skills)
    required_coverage = (len(matched_req) / total_req) if total_req > 0 else 0.0

    # 2. Match Preferred Skills
    matched_pref, missing_pref = match_skill_lists(preferred_skills, student_skills)
    total_pref = len(preferred_skills)
    preferred_coverage = (len(matched_pref) / total_pref) if total_pref > 0 else 0.0

    # 3. Overall Baseline Score (0.0 to 100.0)
    # Formula: 80% weight on mandatory skills, 20% bonus for preferred skills
    if total_req > 0:
        weighted_score = (required_coverage * 80.0) + (preferred_coverage * 20.0)
    else:
        # If no mandatory skills specified, use preferred skills directly
        weighted_score = preferred_coverage * 100.0

    # 4. Experience eligibility
    student_exp = student.get("experience_months", 0)
    min_exp = job.get("min_experience_months", 0)
    experience_eligible = student_exp >= min_exp
    exp_gap = max(0, min_exp - student_exp)

    # 5. Coursework overlap
    student_courses = student.get("coursework", [])
    required_courses = job.get("required_coursework", [])
    matched_courses, missing_courses = match_skill_lists(required_courses, student_courses)

    return {
        "job_id": job.get("job_id", ""),
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "student_id": student.get("id", ""),
        "student_name": student.get("name", ""),
        "method": "keyword_baseline",
        "baseline_score": round(weighted_score, 2),
        "required_coverage": round(required_coverage, 4),
        "preferred_coverage": round(preferred_coverage, 4),
        "matched_required": matched_req,
        "missing_required": missing_req,
        "matched_preferred": matched_pref,
        "missing_preferred": missing_pref,
        "matched_coursework": matched_courses,
        "missing_coursework": missing_courses,
        "experience_eligible": experience_eligible,
        "student_exp_months": student_exp,
        "job_min_exp_months": min_exp,
        "experience_gap_months": exp_gap,
    }


def rank_jobs_for_student(
    student: Dict[str, Any], 
    jobs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Ranks all available jobs for a given student in descending order of baseline score.
    """
    results = []
    for job in jobs:
        match_result = calculate_keyword_match(student, job)
        results.append(match_result)

    # Sort descending by baseline_score
    results.sort(key=lambda item: item["baseline_score"], reverse=True)
    return results


# Self-test demonstration when run directly
if __name__ == "__main__":
    from data_loader import load_all_students, load_all_jobs

    print("=" * 65)
    print("  MILESTONE 3: KEYWORD MATCHING BASELINE DEMONSTRATION")
    print("=" * 65)

    students = load_all_students()
    jobs = load_all_jobs()

    # Case 1: Aarav Sharma (Strong ML candidate) vs JOB_001 (ML Engineer)
    aarav = students[0]
    ml_job = jobs[0]
    aarav_result = calculate_keyword_match(aarav, ml_job)

    print(f"\n[Case 1: Exact Match Success]")
    print(f"Candidate: {aarav['name']}")
    print(f"Job:       {ml_job['title']} @ {ml_job['company']}")
    print(f"Matched Required Skills: {aarav_result['matched_required']}")
    print(f"Missing Required Skills: {aarav_result['missing_required']}")
    print(f"Baseline Score:          {aarav_result['baseline_score']}%")
    print(f"Experience Met:          {aarav_result['experience_eligible']} ({aarav['experience_months']} mos vs {ml_job['min_experience_months']} mos req)")

    # Case 2: Rohan Verma (Has 'NLP' and 'ML' abbreviations) vs JOB_002 (NLP Associate)
    rohan = students[2]
    nlp_job = jobs[1]
    rohan_result = calculate_keyword_match(rohan, nlp_job)

    print(f"\n[Case 2: The Keyword Flaw - Abbreviations & Synonyms]")
    print(f"Candidate: {rohan['name']}")
    print(f"Candidate Skills: {rohan['technical_skills']}")
    print(f"Job Required:     {nlp_job['required_skills']}")
    print(f"Matched Required Skills: {rohan_result['matched_required']}")
    print(f"Missing Required Skills: {rohan_result['missing_required']}")
    print(f"Baseline Score:          {rohan_result['baseline_score']}%")
    print(f"--> Notice: Rohan knows NLP, but keyword matching gave a low score because")
    print(f"    it looked for 'Natural Language Processing' and missed 'NLP'!")
    print(f"    This is the EXACT problem our AI semantic matcher will solve in Milestone 4.")

    # Case 3: Rank all jobs for Aarav
    print(f"\n[Case 3: Ranking all jobs for {aarav['name']}]")
    ranked = rank_jobs_for_student(aarav, jobs)
    for rank, r in enumerate(ranked, 1):
        print(f"  Rank {rank}: {r['job_title']} ({r['company']}) -> {r['baseline_score']}%")

    print("\n" + "=" * 65)
    print("  KEYWORD BASELINE ENGINE COMPLETE & READY")
    print("=" * 65)
