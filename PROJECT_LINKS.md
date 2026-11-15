# 🎓 TalentBridge: University Placement Skill-Match Ranking and Interview Readiness System

### Academic Submission Details
* **Student Name**: Samridhjit Barnwal
* **Registration Number**: 12509754
* **Roll Number**: 21
* **Section**: K3P25IN
* **Degree**: B.Tech CSE (AI & ML)
* **Course**: CSE276: Artificial Intelligence & Foundations (Academic Session 2026–2027)
* **Faculty Mentor / Guide**: Sir Hitesh Kumar
* **Institution**: School of Computer Science & Engineering, Lovely Professional University
* **Problem ID**: LPU-PLACEMENT-01

---

## 🌐 Official Project Links

* **🚀 Live Deployed Web Application**:  
  [https://aiplacement-t3jmxtflurnrjtxrhp3unh.streamlit.app](https://aiplacement-t3jmxtflurnrjtxrhp3unh.streamlit.app)

* **💻 GitHub Source Code Repository**:  
  [https://github.com/Samridh8967/AI_Placement](https://github.com/Samridh8967/AI_Placement)

---

## 📦 Submission Deliverables Overview

1. **Full Python Source Code**:
   * `app/streamlit_app.py` — Multi-portal web dashboard (Student, Recruiter, University Directorate)
   * `app/main.py` — FastAPI REST API backend
   * `src/semantic_matcher.py` — SBERT (`all-MiniLM-L6-v2`) 384-d semantic vector matching engine
   * `src/readiness_model.py` — Supervised Random Forest (93.10% accuracy, 100% recall) & Logistic Regression
   * `src/recommender.py` — Actionable gap remediation engine with personalized roadmaps
   * `src/database.py` — SQLite database manager
   * `data/` — Trained ML models, mock student profiles, job drives, and database
   * `tests/` — Pytest test suite
   * `requirements.txt` — Environment dependencies

2. **Project Presentation (PPT)**:
   * `AI_Placement_System_Presentation.pptx` (PowerPoint presentation deck)
   * `presentation.html` (Interactive HTML presentation)
   * `SPEAKER_NOTES.md` (Speaker presentation notes & defense guide)

3. **Academic Project Report**:
   * `TalentBridge_Report.pdf` (Academic publication-quality PDF report)
   * `PROJECT_REPORT.pdf` (Complete CSE276 project documentation)

---

## ⚙️ Quick Local Run Instructions

```bash
cd placement_system
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```
App will open at `http://localhost:8501`.
