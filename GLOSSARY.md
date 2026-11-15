# Academic Viva & Concepts Glossary
**Course / Evaluation Reference Guide**

This glossary contains key terminology used in the **University Placement Skill-Match Ranking and Interview Readiness System**. Use this guide to prepare for your viva and explain your project confidently.

---

### 1. Natural Language Processing (NLP) & Semantic Matching

#### **Text Embeddings**
- **What it is:** A numerical vector representation of words, phrases, or sentences that captures their underlying semantic meaning.
- **Why we use it:** Computers cannot directly compare strings like `"NLP"` and `"Natural Language Processing"` mathematically. An embedding model converts both strings into high-dimensional vectors (lists of floats, e.g., 384 dimensions) where conceptually related phrases are located close to each other in vector space.
- **Model used:** `sentence-transformers/all-MiniLM-L6-v2` (a lightweight, highly efficient transformer model producing 384-dimensional embeddings).

#### **Cosine Similarity**
- **What it is:** A metric that measures the cosine of the angle between two non-zero vectors in an inner product space:
  $$\text{Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}$$
- **Value range:** Between $-1$ and $+1$ (in text embeddings, typically between $0.0$ and $1.0$).
- **Interpretation:**
  - $1.0$: Identical direction / perfect semantic similarity.
  - $0.0$: Orthogonal / completely unrelated.
  - $\ge 0.75$: Strong match (e.g., "Deep Learning" vs "Neural Networks").
  - $0.50 - 0.74$: Uncertain or related domain (e.g., "Python" vs "PyTorch" - requires verification).
  - $< 0.50$: Unmatched skill.

#### **Keyword Matching Baseline**
- **What it is:** A deterministic rule-based method that checks for exact textual string equality (with case-folding like `.lower()` and whitespace trimming).
- **Role in Project:** Serves as the scientific control / benchmark against which the semantic matching model is evaluated.

---

### 2. Machine Learning & Classification

#### **Features (Input Variables $X$)**
- Measurable numeric properties extracted from a student-job pairing.
- Examples in our system:
  1. `required_skill_coverage`: Proportion of required skills satisfied ($0.0$ to $1.0$).
  2. `preferred_skill_coverage`: Proportion of preferred skills satisfied ($0.0$ to $1.0$).
  3. `experience_ratio`: Student experience divided by job required experience.
  4. `project_relevance_score`: Semantic match of student project descriptions with job domain.

#### **Labels (Target Variable $y$)**
- The ground-truth outcome we want the model to predict.
- In our system: Binary classification where:
  - $1$: Interview-Ready (meets core technical criteria and sufficient foundation).
  - $0$: Needs Improvement (significant skill or qualification gaps).

#### **Supervised Classification**
- Training a machine learning algorithm using paired input features and known labels $(X, y)$ so that the model learns a decision boundary to classify unseen student-job profiles.
- Models used:
  1. **Logistic Regression:** Linear, highly explainable model outputting calibrated probabilities.
  2. **Random Forest:** Ensemble of decision trees capable of capturing non-linear feature interactions.

---

### 3. Model Evaluation Metrics

#### **Accuracy**
$$\text{Accuracy} = \frac{\text{Correct Predictions}}{\text{Total Predictions}}$$
- *Limitation:* Misleading if data is imbalanced (e.g., 90% of students need improvement).

#### **Precision**
$$\text{Precision} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$$
- Answers: *"Of all students we predicted as 'Interview Ready', how many actually were?"*
- High precision prevents sending unprepared students to recruiters.

#### **Recall (Sensitivity)**
$$\text{Recall} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$$
- Answers: *"Of all truly qualified students, how many did our system identify?"*
- High recall ensures capable students are not overlooked.

#### **F1-Score**
$$F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
- Harmonic mean of Precision and Recall. Balances both concerns.

#### **Confusion Matrix**
A $2 \times 2$ table showing True Positives (TP), True Negatives (TN), False Positives (FP), and False Negatives (FN).
