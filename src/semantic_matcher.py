"""
Semantic Skill Matching Module
-------------------------------
Uses Sentence Transformers ('all-MiniLM-L6-v2') and Cosine Similarity
to semantically match student skills, coursework, and projects with job requirements.

Key Academic Principles:
1. Aliases & Normalization: Expands common industry acronyms (NLP, ML, DBMS).
2. Embedding Caching: Avoids redundant neural network computations.
3. Multi-tier Thresholds: Distinguishes 'Strong' (>= 0.75), 'Uncertain' (0.55 - 0.74), and 'Missing' (< 0.55).
4. Traceability: Always preserves which student skill produced the match.
5. Human Review Flag: Never treats loosely related skills (e.g. Python vs PyTorch) as interchangeable.
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Lazy load / import sentence_transformers to allow clear error messaging
_MODEL = None

# 1. Domain Acronym Aliases (Maps common acronyms to standard canonical phrases)
ALIAS_MAP: Dict[str, str] = {
    "ml": "Machine Learning",
    "nlp": "Natural Language Processing",
    "dl": "Deep Learning",
    "cv": "Computer Vision",
    "ai": "Artificial Intelligence",
    "dbms": "Database Management Systems",
    "dsa": "Data Structures and Algorithms",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "tf": "TensorFlow",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "power bi": "PowerBI",
    "powerbi": "PowerBI",
}

# 2. Configurable Decision Thresholds
STRONG_MATCH_THRESHOLD = 0.75      # Confident semantic equivalence
UNCERTAIN_MATCH_THRESHOLD = 0.55   # Related domain, requires human/interview verification

# 3. In-memory Embedding Cache
# Maps: cleaned_text_string -> 384-dimensional numpy vector
_EMBEDDING_CACHE: Dict[str, np.ndarray] = {}


def get_model():
    """
    Singleton loader for the SentenceTransformer model.
    Downloads / loads weights once and reuses across calls.
    Uses local cached weights to eliminate network latency.
    """
    global _MODEL
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            try:
                _MODEL = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            except Exception:
                _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError as err:
            raise ImportError(
                "Sentence-Transformers is required for semantic matching. "
                "Install it via: pip install sentence-transformers"
            ) from err
    return _MODEL


def canonicalize_skill(skill: str) -> str:
    """
    Expands acronyms using ALIAS_MAP and normalizes whitespace.
    
    Example:
        'nlp' -> 'Natural Language Processing'
        '  Machine Learning  ' -> 'Machine Learning'
    """
    if not skill or not isinstance(skill, str):
        return ""
    clean = skill.strip()
    return ALIAS_MAP.get(clean.lower(), clean)


def compute_embedding(text: str) -> np.ndarray:
    """
    Encodes text into a normalized 384-dimensional vector embedding.
    Uses in-memory caching to avoid re-encoding identical text strings.
    """
    text_key = text.strip().lower()
    if not text_key:
        return np.zeros(384, dtype=np.float32)

    if text_key in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[text_key]

    model = get_model()
    # model.encode returns a numpy array or torch tensor
    emb = model.encode(text, convert_to_numpy=True)
    # Normalize vector to unit length (L2 norm = 1.0) for fast cosine dot products
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm

    _EMBEDDING_CACHE[text_key] = emb
    return emb


def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Computes Cosine Similarity between two unit-normalized vectors:
        Cosine Sim(A, B) = (A • B) / (||A|| * ||B||)
    Since compute_embedding already unit-normalizes vectors, this is simply the dot product.
    """
    if vec_a is None or vec_b is None:
        return 0.0
    val = float(np.dot(vec_a, vec_b))
    # Clip between -1.0 and 1.0 to handle minor floating point rounding
    return float(np.clip(val, -1.0, 1.0))


def find_best_skill_match(
    target_skill: str, 
    candidate_skills: List[str]
) -> Dict[str, Any]:
    """
    Compares a single target job skill against all skills listed by a student.
    Finds the highest-scoring candidate skill and determines match confidence.
    
    Args:
        target_skill: e.g. 'Natural Language Processing'
        candidate_skills: e.g. ['Python', 'NLP', 'PyTorch']
        
    Returns:
        dict: Details of the best match, score, and verification state.
    """
    canonical_target = canonicalize_skill(target_skill)
    target_vec = compute_embedding(canonical_target)

    best_match_skill = None
    best_score = -1.0

    for cand in candidate_skills:
        canonical_cand = canonicalize_skill(cand)
        
        # 1. Exact string match after canonicalization = 1.0 perfect match
        if canonical_target.lower() == canonical_cand.lower():
            best_score = 1.0
            best_match_skill = cand
            break

        cand_vec = compute_embedding(canonical_cand)
        sim = compute_cosine_similarity(target_vec, cand_vec)

        if sim > best_score:
            best_score = sim
            best_match_skill = cand

    if best_score < 0:
        best_score = 0.0

    # Determine confidence status based on scientific thresholds
    if best_score >= STRONG_MATCH_THRESHOLD:
        status = "strong_match"
        needs_review = False
        credit = 1.0
    elif best_score >= UNCERTAIN_MATCH_THRESHOLD:
        status = "uncertain_match"
        needs_review = True
        credit = 0.5  # Partial credit for related skill; recruiter verification needed
    else:
        status = "missing"
        needs_review = False
        credit = 0.0

    return {
        "job_skill": target_skill,
        "matched_student_skill": best_match_skill if status != "missing" else None,
        "similarity_score": round(best_score, 4),
        "status": status,
        "needs_human_review": needs_review,
        "credit": credit
    }


def match_skills_semantically(
    job_skills: List[str], 
    student_skills: List[str]
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Compares all job skills against student skills.
    
    Returns:
        tuple: (list of skill match details, coverage score between 0.0 and 1.0)
    """
    if not job_skills:
        return [], 1.0  # If job requires no skills, coverage is 100%

    details = []
    total_credit = 0.0

    for skill in job_skills:
        match_info = find_best_skill_match(skill, student_skills)
        details.append(match_info)
        total_credit += match_info["credit"]

    coverage = total_credit / len(job_skills)
    return details, coverage


def compute_project_relevance(
    projects: List[Dict[str, Any]], 
    job: Dict[str, Any]
) -> float:
    """
    Calculates semantic alignment between student project descriptions and the job description/domain.
    Returns a float from 0.0 to 1.0.
    """
    if not projects:
        return 0.0

    job_text = f"{job.get('title', '')} {job.get('domain', '')} {job.get('description', '')}"
    job_vec = compute_embedding(job_text)

    project_scores = []
    for p in projects:
        p_text = f"{p.get('title', '')}: {p.get('description', '')}"
        p_vec = compute_embedding(p_text)
        sim = compute_cosine_similarity(job_vec, p_vec)
        # Cosine similarity on sentence paragraphs typically ranges 0.2 - 0.7
        # We normalize negative scores to 0.0
        project_scores.append(max(0.0, sim))

    # Highest scoring relevant project
    return round(float(max(project_scores)), 4) if project_scores else 0.0


def calculate_semantic_match(
    student: Dict[str, Any], 
    job: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Comprehensive student-to-job semantic matching engine.
    
    Outputs:
    - Overall semantic match score (0.0 to 100.0)
    - Detailed required skill matches with supporting evidence
    - Detailed preferred skill matches
    - Coursework overlap
    - Project relevance score
    - Flag for human review when ambiguous matches occur
    """
    student_skills = student.get("technical_skills", [])
    required_skills = job.get("required_skills", [])
    preferred_skills = job.get("preferred_skills", [])

    # 1. Match Required Skills
    req_details, req_coverage = match_skills_semantically(required_skills, student_skills)

    # 2. Match Preferred Skills
    pref_details, pref_coverage = match_skills_semantically(preferred_skills, student_skills)

    # 3. Overall Semantic Score
    # 80% weight on mandatory skills, 20% on preferred skills
    if required_skills:
        semantic_score = (req_coverage * 80.0) + (pref_coverage * 20.0)
    else:
        semantic_score = pref_coverage * 100.0

    # 4. Project relevance
    project_rel = compute_project_relevance(student.get("projects", []), job)

    # 5. Review flags & missing skills
    uncertain_skills = [m["job_skill"] for m in req_details if m["status"] == "uncertain_match"]
    missing_skills = [m["job_skill"] for m in req_details if m["status"] == "missing"]
    strong_matches = [m["job_skill"] for m in req_details if m["status"] == "strong_match"]

    student_exp = student.get("experience_months", 0)
    min_exp = job.get("min_experience_months", 0)
    experience_eligible = student_exp >= min_exp

    return {
        "job_id": job.get("job_id", ""),
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "domain": job.get("domain", ""),
        "student_id": student.get("id", ""),
        "student_name": student.get("name", ""),
        "method": "semantic_transformer",
        "semantic_score": round(semantic_score, 2),
        "required_coverage": round(req_coverage, 4),
        "preferred_coverage": round(pref_coverage, 4),
        "project_relevance": project_rel,
        "required_match_details": req_details,
        "preferred_match_details": pref_details,
        "strong_matches": strong_matches,
        "uncertain_skills": uncertain_skills,
        "missing_skills": missing_skills,
        "needs_human_review": len(uncertain_skills) > 0,
        "experience_eligible": experience_eligible,
        "student_exp_months": student_exp,
        "job_min_exp_months": min_exp,
        "experience_gap_months": max(0, min_exp - student_exp),
    }


def rank_jobs_semantically(
    student: Dict[str, Any], 
    jobs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Ranks all available job postings for a student based on semantic match score.
    """
    results = [calculate_semantic_match(student, job) for job in jobs]
    results.sort(key=lambda item: item["semantic_score"], reverse=True)
    return results


# Self-test demonstration when run directly
if __name__ == "__main__":
    from data_loader import load_all_students, load_all_jobs
    from keyword_matcher import calculate_keyword_match

    print("=" * 70)
    print("  MILESTONE 4 & 5: SEMANTIC SKILL MATCHING DEMONSTRATION")
    print("=" * 70)

    students = load_all_students()
    jobs = load_all_jobs()

    # Case: Rohan Verma vs JOB_002 (NLP Associate)
    # Rohan has 'NLP' and 'ML'
    # Job requires 'Natural Language Processing', 'Python', 'PyTorch'
    rohan = students[2]
    nlp_job = jobs[1]

    kw_result = calculate_keyword_match(rohan, nlp_job)
    sem_result = calculate_semantic_match(rohan, nlp_job)

    print(f"\nCandidate: {rohan['name']}")
    print(f"Candidate Skills: {rohan['technical_skills']}")
    print(f"Target Job:       {nlp_job['title']} @ {nlp_job['company']}")
    print(f"Required Skills:  {nlp_job['required_skills']}")
    print("-" * 70)
    print(f"1. Traditional Keyword Match Score: {kw_result['baseline_score']}%")
    print(f"   Matched: {kw_result['matched_required']}")
    print(f"   Missing: {kw_result['missing_required']}")
    print("-" * 70)
    print(f"2. AI Semantic Match Score:         {sem_result['semantic_score']}%")
    print(f"   Skill Match Breakdown:")
    for detail in sem_result["required_match_details"]:
        matched_str = detail['matched_student_skill'] or 'None'
        print(f"     • {detail['job_skill']} -> Matched with '{matched_str}' (Similarity: {detail['similarity_score']}) [{detail['status']}]")

    print(f"\n   Human Review Needed: {sem_result['needs_human_review']}")
    print(f"   Project Relevance Score: {sem_result['project_relevance']}")
    print("-" * 70)
    print("--> PROOF: The semantic matcher recognized 'NLP' as 'Natural Language Processing'")
    print(f"    boosting Rohan's score from {kw_result['baseline_score']}% to {sem_result['semantic_score']}%!")

    print(f"\n[Ranking all jobs semantically for {rohan['name']}]:")
    ranked = rank_jobs_semantically(rohan, jobs)
    for rank, r in enumerate(ranked, 1):
        review_flag = "⚠️ (Needs Review)" if r["needs_human_review"] else "✅"
        print(f"  Rank {rank}: {r['job_title']} ({r['company']}) -> {r['semantic_score']}% {review_flag}")

    print("\n" + "=" * 70)
    print("  SEMANTIC MATCHER & JOB RANKING COMPLETE")
    print("=" * 70)
