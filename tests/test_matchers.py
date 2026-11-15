"""
Automated Unit Tests for Matching Logic
---------------------------------------
Run using:
    pytest tests/
or:
    python3 -m unittest tests/test_matchers.py
"""

import sys
from pathlib import Path
import unittest

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from keyword_matcher import normalize_skill, match_skill_lists, calculate_keyword_match
from semantic_matcher import canonicalize_skill, compute_cosine_similarity
from readiness_model import extract_features, predict_interview_readiness
from database import get_connection, init_db, save_student_db, get_all_students_db
import numpy as np
import tempfile


class TestKeywordMatcher(unittest.TestCase):

    def test_normalization(self):
        self.assertEqual(normalize_skill("  Python  "), "python")
        self.assertEqual(normalize_skill("MACHINE LEARNING"), "machine learning")
        self.assertEqual(normalize_skill(""), "")
        self.assertEqual(normalize_skill(None), "")

    def test_skill_list_matching(self):
        job_skills = ["Python", "SQL", "Docker"]
        student_skills = ["python", "sql", "java"]
        matched, missing = match_skill_lists(job_skills, student_skills)
        self.assertEqual(matched, ["Python", "SQL"])
        self.assertEqual(missing, ["Docker"])

    def test_experience_check(self):
        student = {
            "id": "T1",
            "name": "Test",
            "technical_skills": ["Python"],
            "experience_months": 6
        }
        job = {
            "job_id": "J1",
            "title": "Dev",
            "required_skills": ["Python"],
            "preferred_skills": [],
            "min_experience_months": 12
        }
        result = calculate_keyword_match(student, job)
        self.assertFalse(result["experience_eligible"])
        self.assertEqual(result["experience_gap_months"], 6)

    def test_empty_requirements_safety(self):
        student = {"id": "T2", "name": "Test", "technical_skills": [], "experience_months": 0}
        job = {"job_id": "J2", "title": "Dev", "required_skills": [], "preferred_skills": [], "min_experience_months": 0}
        result = calculate_keyword_match(student, job)
        self.assertEqual(result["baseline_score"], 0.0)
        self.assertTrue(result["experience_eligible"])


class TestSemanticMatcher(unittest.TestCase):

    def test_canonicalize_alias(self):
        self.assertEqual(canonicalize_skill("nlp"), "Natural Language Processing")
        self.assertEqual(canonicalize_skill("ML"), "Machine Learning")
        self.assertEqual(canonicalize_skill("Python"), "Python")

    def test_cosine_similarity_math(self):
        # Two identical unit vectors should have cosine similarity = 1.0
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        self.assertAlmostEqual(compute_cosine_similarity(v1, v2), 1.0, places=4)

        # Two orthogonal vectors should have cosine similarity = 0.0
        v3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.assertAlmostEqual(compute_cosine_similarity(v1, v3), 0.0, places=4)


class TestReadinessModel(unittest.TestCase):

    def test_feature_extraction_types(self):
        student = {
            "id": "T1",
            "name": "Test",
            "technical_skills": ["Python"],
            "coursework": ["Math"],
            "experience_months": 6,
            "projects": []
        }
        job = {
            "job_id": "J1",
            "title": "Engineer",
            "required_skills": ["Python"],
            "preferred_skills": [],
            "required_coursework": ["Math"],
            "min_experience_months": 6
        }
        features = extract_features(student, job)
        self.assertIn("required_skill_coverage", features)
        self.assertIn("experience_ratio", features)
        self.assertEqual(features["experience_ratio"], 1.0)
        self.assertEqual(features["coursework_overlap"], 1.0)

    def test_incomplete_profile_readiness(self):
        student = {"id": "T_EMPTY", "name": "Empty", "technical_skills": [], "experience_months": 0}
        job = {"job_id": "J1", "title": "Engineer", "required_skills": ["Python"], "preferred_skills": [], "min_experience_months": 12}
        pred = predict_interview_readiness(student, job)
        self.assertEqual(pred["readiness_status"], "Needs Improvement")
        self.assertFalse(pred["is_ready"])


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_retrieve_student(self):
        student = {
            "id": "STU_TEST",
            "name": "Unit Tester",
            "email": "test@test.com",
            "experience_months": 5,
            "technical_skills": ["Python", "SQLite"],
            "coursework": ["Testing"],
            "projects": [],
            "internship_experience": "Tester",
            "preferred_domains": ["QA"],
            "career_interests": ["QA Engineer"]
        }
        save_student_db(student, self.db_path)
        all_students = get_all_students_db(self.db_path)
        self.assertEqual(len(all_students), 1)
        self.assertEqual(all_students[0]["name"], "Unit Tester")
        self.assertEqual(all_students[0]["technical_skills"], ["Python", "SQLite"])


if __name__ == "__main__":
    unittest.main()
