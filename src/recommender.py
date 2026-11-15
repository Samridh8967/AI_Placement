"""
Explainable Recommendations & Skill-Gap Analysis Module
-------------------------------------------------------
Generates transparent, student-centric explanations and actionable career guidance.

Key Capabilities:
1. Traceable Gap Identification: Distinguishes missing mandatory skills from optional ones.
2. Targeted Recommendations: Suggests specific skills, project ideas, and coursework.
3. Ethical AI Governance: Clear human-review flags and non-guarantee placement disclaimers.
"""

from typing import Any, Dict, List, Optional


# Curated learning roadmap database mapping skill -> recommended project and coursework ideas
SKILL_LEARNING_GUIDE: Dict[str, Dict[str, str]] = {
    "docker": {
        "course": "DevOps Foundations / Containerization with Docker",
        "project": "Containerize a multi-tier Python application with Docker Compose and deploy to a cloud instance."
    },
    "git": {
        "course": "Software Engineering & Version Control with Git/GitHub",
        "project": "Publish an open-source GitHub repository with automated GitHub Actions CI/CD workflows."
    },
    "pytorch": {
        "course": "Deep Learning with PyTorch & Neural Networks",
        "project": "Implement an image classifier or LSTM sequence model from scratch using PyTorch."
    },
    "tensorflow": {
        "course": "Deep Learning Specialization / Convolutional Neural Networks",
        "project": "Build and evaluate a Transfer Learning vision pipeline using TensorFlow Keras."
    },
    "natural language processing": {
        "course": "Natural Language Processing with Transformers",
        "project": "Build an extractive text summarizer or Q&A chatbot using Hugging Face transformers."
    },
    "machine learning": {
        "course": "Foundations of Machine Learning & Applied Predictive Modeling",
        "project": "Perform end-to-end exploratory data analysis and train evaluated ensemble models on tabular data."
    },
    "sql": {
        "course": "Database Management Systems & Relational Query Optimization",
        "project": "Design a 3NF normalized schema and write complex analytical window queries for a business dataset."
    },
    "fastapi": {
        "course": "Modern Asynchronous Web Development in Python",
        "project": "Create a high-performance REST API with Pydantic validation, JWT authentication, and Swagger docs."
    },
    "powerbi": {
        "course": "Business Intelligence & Data Visualization",
        "project": "Design an executive dashboard with interactive DAX measures and drill-down KPIs."
    },
    "tableau": {
        "course": "Visual Analytics & Business Reporting",
        "project": "Publish an interactive public Tableau workbook visualizing global supply chain or socioeconomic metrics."
    },
}


def generate_recommendations(
    student: Dict[str, Any],
    job: Dict[str, Any],
    semantic_match: Dict[str, Any],
    keyword_match: Dict[str, Any],
    readiness_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Builds a structured, human-readable report explaining the match,
    highlighting gaps, and recommending tailored improvements.
    """
    missing_required = semantic_match.get("missing_skills", [])
    uncertain_skills = semantic_match.get("uncertain_skills", [])
    
    # Missing preferred skills
    pref_details = semantic_match.get("preferred_match_details", [])
    missing_preferred = [p["job_skill"] for p in pref_details if p["status"] == "missing"]

    # 1. Actionable Skill Recommendations (Prioritized: Missing Required -> Uncertain -> Missing Preferred)
    recommended_actions = []
    
    # Priority 1: Mandatory Missing Skills
    for skill in missing_required:
        clean = skill.strip().lower()
        guide = SKILL_LEARNING_GUIDE.get(clean, {
            "course": f"Applied {skill} Foundations",
            "project": f"Build a portfolio project demonstrating hands-on proficiency in {skill}."
        })
        recommended_actions.append({
            "skill": skill,
            "priority": "HIGH (Mandatory Requirement)",
            "reason": f"Required for {job.get('title')}. Currently unverified in your profile.",
            "recommended_course": guide["course"],
            "suggested_project": guide["project"]
        })

    # Priority 2: Uncertain Skills (Need verification or strengthening)
    for skill in uncertain_skills:
        clean = skill.strip().lower()
        guide = SKILL_LEARNING_GUIDE.get(clean, {
            "course": f"Advanced {skill} Specialization",
            "project": f"Add an explicit project demonstrating {skill} to remove ambiguity."
        })
        recommended_actions.append({
            "skill": skill,
            "priority": "MEDIUM (Verification Needed)",
            "reason": f"Semantic similarity indicates related background, but explicit evidence is needed.",
            "recommended_course": guide["course"],
            "suggested_project": guide["project"]
        })

    # Priority 3: Preferred Skills (Bonus differentiators)
    for skill in missing_preferred[:2]:  # Suggest top 2 preferred
        clean = skill.strip().lower()
        guide = SKILL_LEARNING_GUIDE.get(clean, {
            "course": f"Introduction to {skill}",
            "project": f"Integrate {skill} into an existing project to gain a competitive edge."
        })
        recommended_actions.append({
            "skill": skill,
            "priority": "LOW (Competitive Advantage)",
            "reason": f"Preferred bonus skill that sets you apart from other applicants.",
            "recommended_course": guide["course"],
            "suggested_project": guide["project"]
        })

    # 2. Experience Advice
    exp_gap = semantic_match.get("experience_gap_months", 0)
    if exp_gap > 0:
        exp_advice = (
            f"You currently have {student.get('experience_months', 0)} months of experience, "
            f"while this role requires {job.get('min_experience_months', 0)} months. "
            f"Bridge this {exp_gap}-month gap through internships, research assistantships, or high-impact capstone projects."
        )
    else:
        exp_advice = f"Experience requirement fully satisfied ({student.get('experience_months', 0)} months provided)."

    # 3. Overall Match Summary Statement
    score_diff = round(semantic_match["semantic_score"] - keyword_match["baseline_score"], 2)
    if score_diff > 5.0:
        comparison_summary = (
            f"AI Semantic Matching recognized {score_diff}% higher compatibility than traditional keyword matching "
            f"by understanding conceptual skill equivalents."
        )
    elif score_diff < -5.0:
        comparison_summary = (
            "Keyword matching was overly optimistic; semantic evaluation identified subtle gaps in required depths."
        )
    else:
        comparison_summary = "Keyword and semantic assessments are closely aligned."

    return {
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "student_name": student.get("name", ""),
        "overall_semantic_score": semantic_match.get("semantic_score", 0.0),
        "baseline_keyword_score": keyword_match.get("baseline_score", 0.0),
        "score_difference": score_diff,
        "readiness_status": readiness_result.get("readiness_status", "Needs Improvement"),
        "confidence": readiness_result.get("confidence_percentage", 0.0),
        "comparison_summary": comparison_summary,
        "experience_advice": exp_advice,
        "recommendations": recommended_actions,
        "disclaimer": (
            "Academic Notice: This assessment is generated by an algorithmic matching and classification model "
            "for academic career preparation. It does not guarantee interview scheduling, placement, or employment."
        )
    }


if __name__ == "__main__":
    from data_loader import load_all_students, load_all_jobs
    from keyword_matcher import calculate_keyword_match
    from semantic_matcher import calculate_semantic_match
    from readiness_model import predict_interview_readiness

    print("=" * 70)
    print("  MILESTONE 8: EXPLAINABLE RECOMMENDATIONS & GAP ANALYSIS")
    print("=" * 70)

    students = load_all_students()
    jobs = load_all_jobs()

    # Test candidate: Rohan Verma (NLP candidate) vs DeepVision ML Engineer job
    rohan = students[2]
    ml_job = jobs[0]

    sem_res = calculate_semantic_match(rohan, ml_job)
    kw_res = calculate_keyword_match(rohan, ml_job)
    readiness = predict_interview_readiness(rohan, ml_job, sem_res)

    report = generate_recommendations(rohan, ml_job, sem_res, kw_res, readiness)

    print(f"\nCandidate: {report['student_name']} ➔ Job: {report['job_title']} @ {report['company']}")
    print(f"Overall Semantic Score: {report['overall_semantic_score']}% (vs Keyword Baseline: {report['baseline_keyword_score']}%)")
    print(f"Readiness:              {report['readiness_status']} ({report['confidence']}% confidence)")
    print(f"Comparison:             {report['comparison_summary']}")
    print(f"Experience Feedback:    {report['experience_advice']}")
    print(f"\n[Personalized Improvement Plan ({len(report['recommendations'])} items)]:")
    for idx, r in enumerate(report["recommendations"], 1):
        print(f"  {idx}. [{r['priority']}] {r['skill']}")
        print(f"     Reason:     {r['reason']}")
        print(f"     Course:     {r['recommended_course']}")
        print(f"     Project:    {r['suggested_project']}")

    print(f"\nDisclaimer: {report['disclaimer']}")
    print("=" * 70)
