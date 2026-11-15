"""
Placement System - Milestone 1 Verification Script
--------------------------------------------------
This script checks:
1. Python runtime version.
2. Required project directory layout.
3. Fundamental Python data structures (lists, dicts, functions).
"""

import sys
from pathlib import Path


def check_python_version() -> bool:
    """Ensure Python version is 3.9 or higher."""
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"[*] Detected Python version: {major}.{minor}.{sys.version_info.micro}")
    if major < 3 or (major == 3 and minor < 9):
        print("[!] Warning: Python 3.9+ is recommended for modern ML packages.")
        return False
    print("[+] Python version check: PASSED")
    return True


def check_directory_structure(base_dir: Path) -> bool:
    """Verify that expected project directories exist."""
    expected_dirs = ["data", "src", "app", "tests"]
    all_ok = True
    print(f"\n[*] Checking project structure in: {base_dir}")
    for d in expected_dirs:
        target = base_dir / d
        if target.is_dir():
            print(f"  [+] Directory found: {d}/")
        else:
            print(f"  [-] Directory missing, creating: {d}/")
            target.mkdir(parents=True, exist_ok=True)
    return all_ok


def test_core_python_concepts() -> bool:
    """
    Demonstrate and verify the basic data structures used in this project:
    - Lists: for storing collections of skills or candidates
    - Dictionaries: for structured student profiles and job listings
    - Loops & Comprehensions: for matching logic
    """
    print("\n[*] Testing core Python data structures...")

    # 1. Sample student profile as a Python dictionary
    sample_student = {
        "id": "STU_001",
        "name": "Aarav Sharma",
        "skills": ["Python", "SQL", "Machine Learning"],
        "experience_months": 6,
    }

    # 2. Sample job requirements
    sample_job = {
        "job_id": "JOB_101",
        "title": "Junior ML Engineer",
        "required_skills": ["python", "sql", "git"],
    }

    # 3. Simple normalized comparison using a loop
    normalized_student_skills = [s.strip().lower() for s in sample_student["skills"]]
    matched = []
    missing = []

    for req in sample_job["required_skills"]:
        if req.lower() in normalized_student_skills:
            matched.append(req)
        else:
            missing.append(req)

    print(f"  Sample Candidate: {sample_student['name']}")
    print(f"  Matched Skills  : {matched}")
    print(f"  Missing Skills  : {missing}")

    assert "python" in matched, "Logic error: Python should match"
    assert "git" in missing, "Logic error: Git should be missing"

    print("[+] Core Python structures check: PASSED")
    return True


def main():
    print("=" * 60)
    print("  UNIVERSITY PLACEMENT SYSTEM - SETUP VERIFICATION")
    print("=" * 60)

    base_dir = Path(__file__).resolve().parent.parent

    v_ok = check_python_version()
    d_ok = check_directory_structure(base_dir)
    c_ok = test_core_python_concepts()

    print("\n" + "=" * 60)
    if v_ok and d_ok and c_ok:
        print("  🎉 MILESTONE 1 VERIFICATION COMPLETE: ALL SYSTEMS READY")
    else:
        print("  ⚠️ Setup completed with warnings. Review details above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
