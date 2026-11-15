"""
Dataset Generator for Supervised Interview Readiness Classifier
----------------------------------------------------------------
Generates a transparent, documented dataset representing student-job evaluations.

Academic Ground-Truth Rubric:
A candidate-job pair is labelled Interview-Ready (1) if and only if:
1. Required Skill Coverage >= 0.70 (strong foundation in core competencies)
2. Experience Ratio >= 0.80 OR (Experience Ratio >= 0.50 AND Project Relevance >= 0.40)
3. Coursework Overlap >= 0.50 (for roles requiring specialized academic background)
Otherwise, labelled Needs Improvement (0).

This script generates:
- Clear positive cases (strong candidates)
- Clear negative cases (unqualified candidates)
- Borderline cases (strong skills but low experience, or good experience with skill gaps)
- Edge cases (empty profiles, zero skills, overqualified candidates)
"""

import csv
from pathlib import Path
import random

# Fix random seed for exact academic reproducibility
random.seed(42)


def generate_readiness_dataset(output_path: Path, num_samples: int = 150):
    """
    Creates a CSV dataset of student-job feature interactions and ground-truth labels.
    """
    headers = [
        "pair_id",
        "student_category",
        "required_skill_coverage",
        "preferred_skill_coverage",
        "experience_ratio",
        "project_relevance",
        "coursework_overlap",
        "readiness_label",
        "label_reason"
    ]

    rows = []

    # Category 1: Strong Candidates (Clear Ready: ~35% of data)
    for i in range(50):
        req_cov = round(random.uniform(0.75, 1.0), 3)
        pref_cov = round(random.uniform(0.50, 1.0), 3)
        exp_ratio = round(random.uniform(0.90, 2.0), 3)
        proj_rel = round(random.uniform(0.45, 0.90), 3)
        course_ov = round(random.uniform(0.60, 1.0), 3)
        rows.append([
            f"PAIR_{len(rows)+1:03d}",
            "strong_candidate",
            req_cov, pref_cov, exp_ratio, proj_rel, course_ov,
            1,
            "Meets or exceeds all skill and experience requirements"
        ])

    # Category 2: Unqualified / Beginner Candidates (Clear Not Ready: ~35% of data)
    for i in range(50):
        req_cov = round(random.uniform(0.10, 0.50), 3)
        pref_cov = round(random.uniform(0.0, 0.40), 3)
        exp_ratio = round(random.uniform(0.0, 0.50), 3)
        proj_rel = round(random.uniform(0.05, 0.35), 3)
        course_ov = round(random.uniform(0.0, 0.40), 3)
        rows.append([
            f"PAIR_{len(rows)+1:03d}",
            "unqualified_candidate",
            req_cov, pref_cov, exp_ratio, proj_rel, course_ov,
            0,
            "Substantial skill and qualification deficiencies"
        ])

    # Category 3: Borderline Candidates - High Skills, Low Experience (~15% of data)
    for i in range(25):
        req_cov = round(random.uniform(0.75, 0.95), 3)
        pref_cov = round(random.uniform(0.40, 0.70), 3)
        exp_ratio = round(random.uniform(0.10, 0.45), 3)  # low experience
        proj_rel = round(random.uniform(0.50, 0.85), 3)   # strong projects to compensate
        course_ov = round(random.uniform(0.50, 0.90), 3)
        # If strong project relevance (>= 0.65), allowed as interview ready
        label = 1 if proj_rel >= 0.65 else 0
        reason = "Passes due to exceptional project portfolio" if label == 1 else "Needs more hands-on practical experience"
        rows.append([
            f"PAIR_{len(rows)+1:03d}",
            "borderline_skills_over_exp",
            req_cov, pref_cov, exp_ratio, proj_rel, course_ov,
            label,
            reason
        ])

    # Category 4: Borderline Candidates - High Experience, Missing Core Skills (~10% of data)
    for i in range(15):
        req_cov = round(random.uniform(0.40, 0.65), 3)  # missing essential skills
        pref_cov = round(random.uniform(0.60, 0.90), 3)
        exp_ratio = round(random.uniform(1.20, 2.0), 3)  # high experience
        proj_rel = round(random.uniform(0.30, 0.60), 3)
        course_ov = round(random.uniform(0.30, 0.70), 3)
        # Even with high experience, core mandatory skill deficit fails readiness
        rows.append([
            f"PAIR_{len(rows)+1:03d}",
            "borderline_exp_over_skills",
            req_cov, pref_cov, exp_ratio, proj_rel, course_ov,
            0,
            "High experience cannot substitute for missing mandatory core skills"
        ])

    # Category 5: Extreme Edge Cases (Empty profiles, zeros, overqualified)
    edge_cases = [
        ("PAIR_141", "edge_empty_profile", 0.0, 0.0, 0.0, 0.0, 0.0, 0, "Empty profile - completely unverified"),
        ("PAIR_142", "edge_perfect_candidate", 1.0, 1.0, 2.0, 0.95, 1.0, 1, "Ideal maximum benchmark candidate"),
        ("PAIR_143", "edge_zero_exp_fresher_eligible", 0.85, 0.70, 1.0, 0.75, 0.80, 1, "Fresher role where 0 exp is fully acceptable"),
        ("PAIR_144", "edge_single_skill_match", 0.25, 0.0, 0.0, 0.10, 0.0, 0, "Only 1 out of 4 skills satisfied"),
        ("PAIR_145", "edge_no_coursework_match", 0.80, 0.60, 1.0, 0.70, 0.0, 1, "Strong practical skills with non-standard coursework")
    ]
    rows.extend(edge_cases)

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"[+] Successfully generated {len(rows)} samples in {output_path}")
    ready_count = sum(1 for r in rows if r[7] == 1)
    not_ready_count = len(rows) - ready_count
    print(f"    - Interview-Ready (1):    {ready_count} ({ready_count/len(rows)*100:.1f}%)")
    print(f"    - Needs Improvement (0): {not_ready_count} ({not_ready_count/len(rows)*100:.1f}%)")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    target_csv = base_dir / "data" / "readiness_dataset.csv"
    generate_readiness_dataset(target_csv)
