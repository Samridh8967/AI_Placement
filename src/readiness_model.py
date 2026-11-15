"""
Supervised Interview Readiness Classification Module
----------------------------------------------------
Uses Scikit-learn to train and evaluate supervised classifiers
(Logistic Regression and Random Forest) to assess student interview readiness.

Academic Purpose:
Moves beyond simple heuristic score cutoffs (e.g. 'if score > 70')
by learning multivariate decision boundaries over:
1. Required Skill Coverage
2. Preferred Skill Coverage
3. Relevant Experience Ratio
4. Project Relevance (Semantic Similarity to Job)
5. Coursework Alignment
"""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

# Canonical Feature Column Names
FEATURE_NAMES: List[str] = [
    "required_skill_coverage",
    "preferred_skill_coverage",
    "experience_ratio",
    "project_relevance",
    "coursework_overlap",
]

_SAVED_MODEL = None


def extract_features(
    student: Dict[str, Any], 
    job: Dict[str, Any], 
    match_result: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Extracts the 5 numeric features required by the classifier from student and job data.
    
    Returns:
        dict mapping feature_name -> float value
    """
    if match_result is None:
        from semantic_matcher import calculate_semantic_match
        match_result = calculate_semantic_match(student, job)

    req_cov = float(match_result.get("required_coverage", 0.0))
    pref_cov = float(match_result.get("preferred_coverage", 0.0))
    proj_rel = float(match_result.get("project_relevance", 0.0))

    # Experience Ratio: student_exp / job_exp (capped at 2.0 to avoid outlier distortion)
    student_exp = student.get("experience_months", 0)
    min_exp = job.get("min_experience_months", 0)
    if min_exp > 0:
        exp_ratio = min(2.0, student_exp / min_exp)
    else:
        # If no min experience required, candidate has 100% experience satisfaction
        exp_ratio = 1.0

    # Coursework Overlap
    student_courses = {c.strip().lower() for c in student.get("coursework", [])}
    req_courses = job.get("required_coursework", [])
    if req_courses:
        matched_courses = sum(1 for c in req_courses if c.strip().lower() in student_courses)
        course_overlap = matched_courses / len(req_courses)
    else:
        course_overlap = 1.0

    return {
        "required_skill_coverage": round(req_cov, 4),
        "preferred_skill_coverage": round(pref_cov, 4),
        "experience_ratio": round(exp_ratio, 4),
        "project_relevance": round(proj_rel, 4),
        "coursework_overlap": round(course_overlap, 4),
    }


def train_and_evaluate_models(
    csv_path: Optional[Path] = None,
    save_model: bool = True
) -> Dict[str, Any]:
    """
    Loads the ground-truth dataset, performs a stratified train/test split,
    trains both Logistic Regression and Random Forest models, and computes
    comprehensive evaluation metrics.
    
    Returns:
        dict containing metrics, confusion matrices, and the best trained model.
    """
    if csv_path is None:
        base_dir = Path(__file__).resolve().parent.parent
        csv_path = base_dir / "data" / "readiness_dataset.csv"

    if not csv_path.exists():
        from data.generate_dataset import generate_readiness_dataset
        generate_readiness_dataset(csv_path)

    df = pd.read_csv(csv_path)
    X = df[FEATURE_NAMES]
    y = df["readiness_label"]

    # 80/20 Stratified Split to preserve class proportions in train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 1. Train Baseline Model: Logistic Regression (Highly interpretable)
    log_reg = LogisticRegression(random_state=42)
    log_reg.fit(X_train, y_train)
    y_pred_lr = log_reg.predict(X_test)

    lr_metrics = {
        "model_name": "Logistic Regression",
        "accuracy": round(float(accuracy_score(y_test, y_pred_lr)), 4),
        "precision": round(float(precision_score(y_test, y_pred_lr, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_lr, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred_lr, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred_lr).tolist(),
        "coefficients": dict(zip(FEATURE_NAMES, [round(float(c), 4) for c in log_reg.coef_[0]]))
    }

    # 2. Train Advanced Model: Random Forest Classifier (Captures non-linear boundaries)
    rf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)

    rf_metrics = {
        "model_name": "Random Forest",
        "accuracy": round(float(accuracy_score(y_test, y_pred_rf)), 4),
        "precision": round(float(precision_score(y_test, y_pred_rf, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_rf, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred_rf, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred_rf).tolist(),
        "feature_importances": dict(zip(FEATURE_NAMES, [round(float(imp), 4) for imp in rf.feature_importances_]))
    }

    # Save the primary model (Logistic Regression for explainability)
    if save_model:
        model_file = csv_path.parent / "readiness_model.pkl"
        with open(model_file, "wb") as f:
            pickle.dump({
                "model": log_reg,
                "rf_model": rf,
                "features": FEATURE_NAMES,
                "lr_metrics": lr_metrics,
                "rf_metrics": rf_metrics
            }, f)

    return {
        "test_samples": len(y_test),
        "logistic_regression": lr_metrics,
        "random_forest": rf_metrics,
        "primary_model": log_reg
    }


def load_trained_model():
    """Singleton loader for the pickled readiness model."""
    global _SAVED_MODEL
    if _SAVED_MODEL is None:
        base_dir = Path(__file__).resolve().parent.parent
        model_file = base_dir / "data" / "readiness_model.pkl"

        if not model_file.exists():
            # If not yet trained, train and save automatically
            train_and_evaluate_models(save_model=True)

        with open(model_file, "rb") as f:
            _SAVED_MODEL = pickle.load(f)

    return _SAVED_MODEL


def predict_interview_readiness(
    student: Dict[str, Any], 
    job: Dict[str, Any], 
    match_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates a candidate-job pair using the trained supervised classifier.
    
    Returns:
        dict containing classification decision, calibrated probability, and feature values.
    """
    feature_dict = extract_features(student, job, match_result)
    feature_df = pd.DataFrame([feature_dict])[FEATURE_NAMES]

    bundle = load_trained_model()
    model = bundle["model"]

    # Predict class (1 = Ready, 0 = Needs Improvement)
    pred_class = int(model.predict(feature_df)[0])
    
    # Predict calibrated probability of being Ready (class 1)
    probs = model.predict_proba(feature_df)[0]
    ready_prob = float(probs[1])

    status = "Interview Ready" if pred_class == 1 else "Needs Improvement"

    return {
        "readiness_status": status,
        "is_ready": pred_class == 1,
        "readiness_probability": round(ready_prob, 4),
        "confidence_percentage": round(ready_prob * 100.0, 1) if pred_class == 1 else round((1.0 - ready_prob) * 100.0, 1),
        "features": feature_dict,
        "model_used": "Logistic Regression (Supervised Classifier)"
    }


# Self-test demonstration when run directly
if __name__ == "__main__":
    from data_loader import load_all_students, load_all_jobs
    from semantic_matcher import calculate_semantic_match

    print("=" * 70)
    print("  MILESTONE 6 & 7: SUPERVISED READINESS CLASSIFIER")
    print("=" * 70)

    # 1. Train and evaluate
    eval_results = train_and_evaluate_models()
    lr = eval_results["logistic_regression"]
    rf = eval_results["random_forest"]

    print(f"\n[1. Model Performance on Test Set ({eval_results['test_samples']} samples)]")
    print(f"{'Metric':<18} | {'Logistic Regression':<22} | {'Random Forest':<15}")
    print("-" * 62)
    print(f"{'Accuracy':<18} | {lr['accuracy']:<22} | {rf['accuracy']:<15}")
    print(f"{'Precision':<18} | {lr['precision']:<22} | {rf['precision']:<15}")
    print(f"{'Recall':<18} | {lr['recall']:<22} | {rf['recall']:<15}")
    print(f"{'F1-Score':<18} | {lr['f1']:<22} | {rf['f1']:<15}")

    print(f"\n[2. Logistic Regression Feature Coefficients (Impact on Readiness)]")
    for feat, coef in lr["coefficients"].items():
        direction = "Positive (+)" if coef > 0 else "Negative (-)"
        print(f"  • {feat:<26}: {coef:>7.4f} ({direction})")

    print(f"\n[3. Confusion Matrix - Logistic Regression]")
    cm = lr["confusion_matrix"]
    print(f"  True Negatives (TN): {cm[0][0]} | False Positives (FP): {cm[0][1]}")
    print(f"  False Negatives (FN): {cm[1][0]} | True Positives (TP): {cm[1][1]}")

    # 2. Test predictions on real student profiles
    students = load_all_students()
    jobs = load_all_jobs()

    print(f"\n[4. Live Inference on Sample Students]")
    test_cases = [
        (students[0], jobs[0]),  # Aarav (ML candidate) vs ML Engineer
        (students[2], jobs[1]),  # Rohan (NLP candidate) vs NLP Associate
        (students[4], jobs[0]),  # Incomplete candidate vs ML Engineer
    ]

    for student, job in test_cases:
        sem_res = calculate_semantic_match(student, job)
        pred = predict_interview_readiness(student, job, sem_res)
        print(f"\nCandidate: {student['name']} ➔ Job: {job['title']}")
        print(f"  Readiness:   {pred['readiness_status']} ({pred['confidence_percentage']}% confidence)")
        print(f"  Features:    Req={pred['features']['required_skill_coverage']}, ExpRatio={pred['features']['experience_ratio']}, ProjRel={pred['features']['project_relevance']}")

    print("\n" + "=" * 70)
    print("  SUPERVISED CLASSIFIER COMPLETE & VERIFIED")
    print("=" * 70)
