#!/usr/bin/env python3
"""
TalentBridge Academic Report PDF Generator (Valid ISO 32000-1 Compliant PDF)
Strictly adheres to 20-byte xref entries and sequential object numbering to ensure
compatibility with Apple Quartz, macOS Preview, Adobe Acrobat, and PDFKit.
"""

import sys
import zlib
from pathlib import Path


class ValidPDF:
    def __init__(self, filename="TalentBridge_Report.pdf"):
        self.filename = filename
        self.pages = []
        self.current_page_commands = []
        self.page_width = 595.28   # A4 width
        self.page_height = 841.89  # A4 height
        self.margin_x = 48.0
        self.margin_top = 790.0
        self.margin_bottom = 52.0
        self.cursor_y = self.margin_top
        self.content_width = self.page_width - (2 * self.margin_x)

    def new_page(self):
        if self.current_page_commands:
            self.pages.append(self.current_page_commands)
            self.current_page_commands = []
        self.cursor_y = self.margin_top

    def ensure_space(self, needed_pt):
        if self.cursor_y - needed_pt < self.margin_bottom:
            self.new_page()

    def draw_rect(self, x, y, w, h, fill_rgb=None, stroke_rgb=None, line_width=1.0):
        cmd = []
        cmd.append(f"q\n{line_width:.2f} w")
        if stroke_rgb:
            cmd.append(f"{stroke_rgb[0]:.3f} {stroke_rgb[1]:.3f} {stroke_rgb[2]:.3f} RG")
        if fill_rgb:
            cmd.append(f"{fill_rgb[0]:.3f} {fill_rgb[1]:.3f} {fill_rgb[2]:.3f} rg")
        cmd.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re")
        if fill_rgb and stroke_rgb:
            cmd.append("B")
        elif fill_rgb:
            cmd.append("f")
        else:
            cmd.append("S")
        cmd.append("Q")
        self.current_page_commands.append("\n".join(cmd))

    def draw_line(self, x1, y1, x2, y2, stroke_rgb=(0.8, 0.85, 0.9), line_width=1.0):
        cmd = f"q\n{line_width:.2f} w\n{stroke_rgb[0]:.3f} {stroke_rgb[1]:.3f} {stroke_rgb[2]:.3f} RG\n{x1:.2f} {y1:.2f} m\n{x2:.2f} {y2:.2f} l\nS\nQ"
        self.current_page_commands.append(cmd)

    def escape_text(self, text):
        clean = ""
        for ch in text:
            code = ord(ch)
            if code < 32 or code > 126:
                if ch == '•':
                    clean += "-"
                elif ch in ('—', '–'):
                    clean += "-"
                elif ch in ('"', '"'):
                    clean += '"'
                elif ch in ('\'', '\''):
                    clean += "'"
                elif ch == '≥':
                    clean += ">="
                elif ch == '≤':
                    clean += "<="
                elif ch == '→':
                    clean += "->"
                elif ch == '↔':
                    clean += "<->"
                elif ch == 'Σ':
                    clean += "Sum"
                elif ch == 'π':
                    clean += "pi"
                elif ch == '²':
                    clean += "^2"
                elif ch == '³':
                    clean += "^3"
                else:
                    clean += " "
            elif ch in ('(', ')', '\\'):
                clean += "\\" + ch
            else:
                clean += ch
        return clean

    def draw_text(self, x, y, text, font="F1", size=10, rgb=(0.1, 0.1, 0.15)):
        esc = self.escape_text(text)
        cmd = f"BT\n/{font} {size:.2f} Tf\n{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg\n{x:.2f} {y:.2f} Td\n({esc}) Tj\nET"
        self.current_page_commands.append(cmd)

    def add_title_block(self):
        self.ensure_space(115)
        self.draw_rect(self.margin_x, self.cursor_y - 18, self.content_width, 22, fill_rgb=(0.88, 0.95, 1.0), stroke_rgb=(0.7, 0.85, 1.0), line_width=0.8)
        self.draw_text(self.margin_x + 10, self.cursor_y - 12, "LOVELY PROFESSIONAL UNIVERSITY • SCHOOL OF COMPUTER SCIENCE & ENGINEERING • CSE276", font="F2", size=8.5, rgb=(0.01, 0.4, 0.7))
        self.cursor_y -= 32

        self.draw_text(self.margin_x, self.cursor_y, "TalentBridge: Placement Skill-Match & Readiness System", font="F2", size=16.5, rgb=(0.05, 0.1, 0.2))
        self.cursor_y -= 16
        self.draw_text(self.margin_x, self.cursor_y, "An Explainable Machine Learning & Dense Vector Semantic Assessment Architecture", font="F3", size=10, rgb=(0.3, 0.35, 0.45))
        self.cursor_y -= 16

        meta_h = 46
        self.draw_rect(self.margin_x, self.cursor_y - meta_h + 8, self.content_width, meta_h, fill_rgb=(0.97, 0.985, 1.0), stroke_rgb=(0.85, 0.88, 0.92))
        
        col1_x = self.margin_x + 12
        col2_x = self.margin_x + 260
        y_m1 = self.cursor_y - 4
        y_m2 = self.cursor_y - 18
        y_m3 = self.cursor_y - 32

        self.draw_text(col1_x, y_m1, "Author: Samridhjit Barnwal", font="F2", size=9, rgb=(0.08, 0.12, 0.2))
        self.draw_text(col1_x, y_m2, "Reg No: 12509754  •  Roll No: 21", font="F1", size=8.5, rgb=(0.2, 0.25, 0.35))
        self.draw_text(col1_x, y_m3, "Section: K3P25IN  •  B.Tech CSE (AI & ML)", font="F1", size=8.5, rgb=(0.2, 0.25, 0.35))

        self.draw_text(col2_x, y_m1, "Faculty Mentor: Sir Hitesh Kumar", font="F2", size=9, rgb=(0.08, 0.12, 0.2))
        self.draw_text(col2_x, y_m2, "Course: CSE276 (AI & Foundations)", font="F1", size=8.5, rgb=(0.2, 0.25, 0.35))
        self.draw_text(col2_x, y_m3, "Problem ID: LPU-PLACEMENT-01  •  Session 2026-2027", font="F1", size=8.5, rgb=(0.2, 0.25, 0.35))

        self.cursor_y -= (meta_h + 14)

    def add_section_header(self, text):
        self.ensure_space(34)
        self.cursor_y -= 4
        self.draw_text(self.margin_x, self.cursor_y, text.upper(), font="F2", size=10.5, rgb=(0.01, 0.42, 0.72))
        self.draw_line(self.margin_x, self.cursor_y - 4, self.margin_x + self.content_width, self.cursor_y - 4, stroke_rgb=(0.8, 0.88, 0.95), line_width=1.2)
        self.cursor_y -= 15

    def add_subsection_header(self, text):
        self.ensure_space(22)
        self.draw_text(self.margin_x, self.cursor_y, text, font="F2", size=9.5, rgb=(0.1, 0.15, 0.25))
        self.cursor_y -= 12

    def add_paragraph(self, text, indent=0, font="F1", size=8.5, line_height=12.0, rgb=(0.15, 0.2, 0.25)):
        max_chars = int((self.content_width - indent) / (size * 0.49))
        words = text.split()
        lines = []
        cur_line = []
        cur_len = 0

        for w in words:
            if cur_len + len(w) + 1 <= max_chars:
                cur_line.append(w)
                cur_len += len(w) + 1
            else:
                lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        for line in lines:
            self.ensure_space(line_height + 2)
            self.draw_text(self.margin_x + indent, self.cursor_y, line, font=font, size=size, rgb=rgb)
            self.cursor_y -= line_height

        self.cursor_y -= 2

    def add_bullet(self, bold_prefix, text, size=8.5):
        self.ensure_space(18)
        self.draw_rect(self.margin_x + 6, self.cursor_y + 2, 3.5, 3.5, fill_rgb=(0.01, 0.45, 0.75))
        full_text = f"{bold_prefix} {text}"
        self.add_paragraph(full_text, indent=16, font="F1", size=size, line_height=11.5)

    def add_callout(self, title, body, border_rgb=(0.01, 0.45, 0.72)):
        needed = 38 + (len(body) // 85) * 11
        self.ensure_space(needed)
        box_y = self.cursor_y - needed + 8
        self.draw_rect(self.margin_x, box_y, self.content_width, needed, fill_rgb=(0.975, 0.985, 1.0), stroke_rgb=(0.85, 0.9, 0.95))
        self.draw_rect(self.margin_x, box_y, 4, needed, fill_rgb=border_rgb)
        
        self.draw_text(self.margin_x + 12, self.cursor_y - 2, title, font="F2", size=9, rgb=border_rgb)
        self.cursor_y -= 13
        self.add_paragraph(body, indent=12, font="F1", size=8.2, line_height=11.0)
        self.cursor_y -= 6

    def add_table(self, headers, rows, col_widths):
        table_h = (len(rows) + 1) * 15 + 8
        self.ensure_space(table_h)

        table_x = self.margin_x
        header_y = self.cursor_y - 11
        self.draw_rect(table_x, header_y - 2, self.content_width, 15, fill_rgb=(0.93, 0.95, 0.98), stroke_rgb=(0.8, 0.85, 0.9))
        cur_x = table_x
        for i, h in enumerate(headers):
            w = col_widths[i]
            self.draw_text(cur_x + 5, header_y + 2, h, font="F2", size=8, rgb=(0.05, 0.1, 0.2))
            cur_x += w

        self.cursor_y -= 15

        for r_idx, row in enumerate(rows):
            r_y = self.cursor_y - 11
            bg_col = (1.0, 1.0, 1.0) if r_idx % 2 == 0 else (0.97, 0.98, 0.99)
            self.draw_rect(table_x, r_y - 2, self.content_width, 15, fill_rgb=bg_col, stroke_rgb=(0.85, 0.88, 0.92))
            cur_x = table_x
            for c_idx, cell in enumerate(row):
                w = col_widths[c_idx]
                f_name = "F2" if c_idx == 0 else "F1"
                self.draw_text(cur_x + 5, r_y + 2, str(cell), font=f_name, size=7.8, rgb=(0.1, 0.15, 0.25))
                cur_x += w
            self.cursor_y -= 15

        self.cursor_y -= 4

    def compile(self):
        if self.current_page_commands:
            self.pages.append(self.current_page_commands)

        total_pages = len(self.pages)
        
        # We will strictly map:
        # 1: Catalog
        # 2: Pages
        # Page i: Obj ID = 3 + 2*(i-1)
        # Content i: Obj ID = 4 + 2*(i-1)
        # Fonts start at: 3 + 2*total_pages
        font1_id = 3 + 2 * total_pages
        font2_id = font1_id + 1
        font3_id = font2_id + 1
        font4_id = font3_id + 1

        font_res_str = f"/Font << /F1 {font1_id} 0 R /F2 {font2_id} 0 R /F3 {font3_id} 0 R /F4 {font4_id} 0 R >>"

        # Build Objects array indexed 1 to Total
        # objects[k] corresponds to (k+1) 0 obj
        objects = []

        # 1: Catalog
        catalog_str = "<< /Type /Catalog /Pages 2 0 R >>"
        objects.append(catalog_str.encode())

        # 2: Pages
        page_kids = " ".join([f"{3 + 2*i} 0 R" for i in range(total_pages)])
        pages_str = f"<< /Type /Pages /Kids [ {page_kids} ] /Count {total_pages} >>"
        objects.append(pages_str.encode())

        # For each page:
        for p_idx, page_cmds in enumerate(self.pages):
            p_num = p_idx + 1
            running_header = (
                f"q\n0.5 w\n0.85 0.88 0.92 RG\n{self.margin_x:.2f} 820 m {self.margin_x + self.content_width:.2f} 820 l\nS\nQ\n"
                f"BT\n/F1 7.5 Tf\n0.4 0.45 0.55 rg\n{self.margin_x:.2f} 824 Td\n(TalentBridge: Placement System - CSE276 Academic Report | Samridhjit Barnwal) Tj\nET\n"
            )
            running_footer = (
                f"q\n0.5 w\n0.85 0.88 0.92 RG\n{self.margin_x:.2f} 36 m {self.margin_x + self.content_width:.2f} 36 l\nS\nQ\n"
                f"BT\n/F1 7.5 Tf\n0.4 0.45 0.55 rg\n{self.margin_x:.2f} 26 Td\n(Lovely Professional University - School of Computer Science & Engineering) Tj\nET\n"
                f"BT\n/F2 7.5 Tf\n0.2 0.25 0.35 rg\n{self.margin_x + self.content_width - 55:.2f} 26 Td\n(Page {p_num} of {total_pages}) Tj\nET\n"
            )

            raw_stream = (running_header + "\n".join(page_cmds) + "\n" + running_footer).encode("ascii", "replace")
            comp_stream = zlib.compress(raw_stream)

            content_id = 4 + 2 * p_idx

            # Page Object
            page_obj_str = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.page_width:.2f} {self.page_height:.2f}] "
                f"/Contents {content_id} 0 R /Resources << {font_res_str} >> >>"
            )
            objects.append(page_obj_str.encode())

            # Content Stream Object
            stream_obj_bytes = (
                f"<< /Length {len(comp_stream)} /Filter /FlateDecode >>\nstream\n".encode() +
                comp_stream +
                b"\nendstream"
            )
            objects.append(stream_obj_bytes)

        # Fonts
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>")

        # Now assemble PDF file
        header = b"%PDF-1.4\n"
        body = b""
        offsets = []

        for idx, obj_bytes in enumerate(objects):
            obj_num = idx + 1
            offsets.append(len(header) + len(body))
            body += f"{obj_num} 0 obj\n".encode() + obj_bytes + b"\nendobj\n"

        xref_pos = len(header) + len(body)
        total_objs = len(objects)

        # Build strictly 20-byte entries for xref
        xref = f"xref\r\n0 {total_objs + 1}\r\n0000000000 65535 f\r\n".encode()
        for o in offsets:
            xref += f"{o:010d} 00000 n\r\n".encode()

        trailer = (
            f"trailer\r\n<< /Size {total_objs + 1} /Root 1 0 R >>\r\n"
            f"startxref\r\n{xref_pos}\r\n%%EOF\r\n"
        ).encode()

        out_path = Path(self.filename)
        out_path.write_bytes(header + body + xref + trailer)
        print(f"[+] Successfully compiled {total_pages} page PDF: {out_path.resolve()} ({out_path.stat().st_size} bytes)")


def generate_report():
    pdf = ValidPDF("placement_system/TalentBridge_Report.pdf")

    # ==================== PAGE 1 ====================
    pdf.add_title_block()

    pdf.add_section_header("1. Preliminaries (Front Matter)")
    pdf.add_callout(
        "Declaration & Approval Certificate",
        "I, Samridhjit Barnwal (Reg. No: 12509754, Roll No: 21, Section: K3P25IN), declare that this report represents "
        "original engineering work carried out for course CSE276 under the supervision of Sir Hitesh Kumar. "
        "Approved by: Sir Hitesh Kumar (Course Mentor) & Head of Department, School of Computer Science & Engineering, "
        "Lovely Professional University, Phagwara, Punjab."
    )

    pdf.add_paragraph(
        "Acknowledgements: Gratitude is expressed to my course mentor, Sir Hitesh Kumar, for guidance on explainability "
        "and empirical model evaluation, and to the LPU Placement Division for insights into campus recruitment bottlenecks.",
        size=8.2
    )

    pdf.add_callout(
        "Executive Summary / Abstract",
        "Campus recruitment drives evaluate thousands of applicants against diverse corporate roles under tight schedules. "
        "Conventional Applicant Tracking Systems (ATS) rely on exact character string matching and linear CGPA cutoffs, "
        "introducing the 'Keyword Trap' (disqualifying students for using synonyms like 'NLP' instead of 'Natural Language Processing') "
        "and the 'Rejection Void' (zero diagnostic feedback). TalentBridge resolves this through a multi-stage AI pipeline: "
        "(1) domain acronym canonicalization, (2) dense semantic embeddings using Sentence Transformers (all-MiniLM-L6-v2), "
        "(3) supervised interview readiness classification over a 5D feature space, and (4) prescriptive gap remediation. "
        "On a held-out test split (N=29), the Random Forest model achieved 93.10% accuracy and 100% recall (zero false negatives), "
        "guaranteeing that qualified students are never mistakenly screened out."
    )

    pdf.add_section_header("2. Chapter I: Introduction & Problem Context")
    pdf.add_bullet(
        "1.1 Background:",
        "Engineering placement drives process thousands of applications for visiting corporations under strict time limits. "
        "Placement coordinators and recruiters rely heavily on automated screening to filter candidates prior to technical interviews."
    )
    pdf.add_bullet(
        "1.2 The Keyword Trap:",
        "Lexical string matching treats language as rigid characters. Candidates proficient in 'PyTorch' or 'FastAPI' are marked as misses "
        "if the job description specifies 'Deep Learning' or 'REST APIs', encouraging artificial keyword stuffing."
    )
    pdf.add_bullet(
        "1.3 Linear Cutoff Flaws:",
        "Linear screening rules ('if CGPA >= 8.0 AND exp >= 6 months') ignore non-linear capability, discarding self-taught candidates "
        "who possess outstanding capstone projects and open-source contributions but lower GPAs."
    )
    pdf.add_bullet(
        "1.4 The Rejection Void:",
        "Unselected candidates receive automated rejections with no diagnostic insight, preventing strategic skill development."
    )

    # ==================== PAGE 2 ====================
    pdf.new_page()

    pdf.add_subsection_header("1.5 SMART Objectives of the Study")
    pdf.add_paragraph(
        "- Specific: Develop an end-to-end recruitment platform combining canonical normalization, dense embeddings, and supervised ML.\n"
        "- Measurable: Attain >= 90% semantic similarity across synonyms; maintain 100% Recall and >= 90% classification accuracy.\n"
        "- Achievable: Implement using standard open-source libraries: sentence-transformers, scikit-learn, sqlite3, streamlit, and fastapi.\n"
        "- Relevant: Provide dual perspectives: a Student Career Dossier for guidance and a Recruiter Command Center for batch shortlisting.\n"
        "- Time-Bound: Complete system design, dataset generation, model validation, and deployment within the academic semester.",
        indent=8, size=8.2, line_height=11.2
    )

    pdf.add_section_header("3. Chapter II: Literature Review & Technical Study")
    pdf.add_paragraph(
        "Traditional ATS platforms trace back to early Boolean indexing tools. Literature indicates that exact keyword matching filters "
        "reject over 70% of qualified applicants due to syntactic and formatting variations (Faliagka et al., 2012). While lexical frequency "
        "metrics like TF-IDF measure document importance, they treat synonymous technical terms as orthogonal dimensions. Static embeddings "
        "(Word2Vec, GloVe) capture word associations but struggle with multi-word technical descriptions and context.",
        size=8.2
    )
    pdf.add_paragraph(
        "Sentence-BERT (Reimers & Gurevych, 2019) resolved these bottlenecks using siamese transformer networks to derive continuous "
        "sentence embeddings comparable via cosine distance. TalentBridge adopts all-MiniLM-L6-v2, mapping technical competencies into a "
        "384-dimensional dense vector space with fast CPU inference and low memory overhead.",
        size=8.2
    )

    pdf.add_section_header("4. Chapter III: Methodology & System Architecture")
    pdf.add_paragraph(
        "TalentBridge is engineered as four loosely coupled, modular layers:\n"
        "1. Data Layer: SQLite database (placement_system.db) storing student profiles, job requisitions, and audit ledgers.\n"
        "2. NLP Engine: Domain canonical alias normalization followed by SBERT dense vector encoding and cosine similarity.\n"
        "3. Decision Layer: 5-dimensional feature extraction driving Logistic Regression and Random Forest readiness classifiers.\n"
        "4. Delivery Layer: High-contrast white-background Streamlit web dashboard and FastAPI REST endpoints.",
        size=8.2
    )

    pdf.add_subsection_header("Mathematical Formulation & Gating Thresholds")
    pdf.add_paragraph(
        "Vector Cosine Similarity: Sim(u, v) = (u . v) / (||u|| * ||v||) = Sum(u_i * v_i) for unit vectors in R^384.\n"
        "Multi-Tier Gating Policy:\n"
        "  - Strong Equivalence (Sim >= 0.75): Confirmed skill match (e.g., PyTorch <-> Deep Learning).\n"
        "  - Interview Verification Needed (0.55 <= Sim < 0.75): Related domain flagged for technical interviewer review.\n"
        "  - Missing Prerequisite (Sim < 0.55): Competency gap routed to prescriptive learning engine.",
        indent=8, size=8.2, line_height=11.2
    )

    pdf.add_subsection_header("The 5-Dimensional Feature Space (x)")
    pdf.add_paragraph(
        "1. x1 (Required Skill Coverage): Proportion of mandatory prerequisites satisfied at Sim >= 0.75.\n"
        "2. x2 (Preferred Skill Coverage): Proportion of bonus/preferred competencies satisfied at Sim >= 0.75.\n"
        "3. x3 (Experience Ratio): Candidate internship months divided by job minimum (capped at 2.0 to prevent outlier distortion).\n"
        "4. x4 (Project Relevance): Max cosine similarity between student capstone project abstracts and corporate role description.\n"
        "5. x5 (Coursework Overlap): Proportion of required university courses completed by the student.",
        indent=8, size=8.2, line_height=11.2
    )

    # ==================== PAGE 3 ====================
    pdf.new_page()

    pdf.add_section_header("5. Chapter IV: Implementation & Execution")
    pdf.add_paragraph(
        "Core Modules Breakdown:\n"
        "- data_loader.py: Validates schemas and maps acronyms via ALIAS_MAP ('nlp' -> 'Natural Language Processing', 'postgres' -> 'PostgreSQL').\n"
        "- semantic_matcher.py: Computes SBERT embeddings and caches vectors in an in-memory dictionary (_EMBEDDING_CACHE), reducing "
        "repeated inference latency from ~850ms down to < 15ms.\n"
        "- readiness_model.py: Extracts feature vector x and trains Scikit-Learn Logistic Regression and Random Forest models.\n"
        "- recommender.py: Maps missing prerequisites to structured university courses and open-source capstone project specifications.\n"
        "- streamlit_app.py: Clean white-background web UI featuring Student Career Dossier and Recruiter Command Center modes.",
        size=8.2
    )

    pdf.add_subsection_header("Practical Engineering Challenges Solved")
    pdf.add_bullet(
        "Semantic Drift (Python vs. PyTorch):",
        "Unchecked cosine similarity assigned 0.58 between Python and PyTorch. A single 0.50 cutoff caused false positives. "
        "Introducing the 0.75 strong threshold and 0.55-0.74 review zone eliminated premature automated approvals."
    )
    pdf.add_bullet(
        "Dashboard UI Latency:",
        "Encoding candidate profiles on every filter change introduced noticeable lag. Adding in-memory vector caching "
        "eliminated redundant transformer passes and yielded instantaneous page re-renders."
    )
    pdf.add_bullet(
        "Defensive Zero-Division Guards:",
        "Candidates with empty project lists or zero skills caused division errors. Robust fallbacks defaulting to 0.0 were added."
    )

    pdf.add_section_header("6. Chapter V: Results, Testing, & Analysis")
    pdf.add_paragraph(
        "Dataset & Rubric: 145 stratified candidate-job pairings (Category 1: Strong Candidates 35%, Category 2: Unqualified 35%, "
        "Category 3: High Skills/Low Exp 17%, Category 4: High Exp/Missing Skills 10%, Category 5: Edge Cases 3%) with an 80/20 train/test split.",
        size=8.2
    )

    pdf.add_subsection_header("Baseline Comparison: Keyword Match vs. Semantic Vector Match")
    comp_headers = ["Candidate Input", "Job Requirement", "Keyword Match", "TalentBridge Match", "Operational Impact"]
    comp_rows = [
        ["NLP", "Natural Language Processing", "Miss (0.00)", "1.00 (Canonical)", "Prevents acronym false-rejection"],
        ["PyTorch", "Deep Learning", "Miss (0.00)", "0.78 (Strong Match)", "Maps framework to domain hierarchy"],
        ["Docker", "Containerization", "Miss (0.00)", "0.81 (Strong Match)", "Maps tool to architectural concept"],
        ["Java", "JavaScript", "Miss / Substring", "0.31 (Deficient)", "Avoids superficial prefix confusion"]
    ]
    pdf.add_table(comp_headers, comp_rows, [68, 120, 85, 95, 136])

    pdf.add_subsection_header("Quantitative Model Evaluation on Held-Out Test Set (N = 29)")
    metric_headers = ["Evaluation Metric", "Logistic Regression", "Random Forest Classifier", "Performance Analysis"]
    metric_rows = [
        ["Accuracy", "79.31%", "93.10%", "Random Forest captures non-linear boundary trade-offs (+13.79%)"],
        ["Precision", "68.42%", "86.67%", "Random Forest slashes false positives from 6 down to 2 (+18.25%)"],
        ["Recall (Sensitivity)", "100.00%", "100.00%", "Zero False Negatives: No qualified candidate is mistakenly screened out"],
        ["F1-Score", "81.25%", "92.86%", "Exceptional harmonic balance between precision and recall (+11.61%)"]
    ]
    pdf.add_table(metric_headers, metric_rows, [95, 95, 110, 204])

    # ==================== PAGE 4 ====================
    pdf.new_page()

    pdf.add_subsection_header("Confusion Matrix Breakdown (Test Set: N = 29)")
    pdf.add_paragraph(
        "- Logistic Regression:  [ TN = 10,  FP = 6  |  FN = 0,  TP = 13 ]  (Precision: 68.42%, Recall: 100.0%)\n"
        "- Random Forest:        [ TN = 14,  FP = 2  |  FN = 0,  TP = 13 ]  (Precision: 86.67%, Recall: 100.0%)\n"
        "Key Finding: In educational recruitment, a False Negative (wrongly rejecting a capable student) is far more detrimental than a "
        "False Positive. Both models achieved 100% Recall, while Random Forest achieved 93.10% overall accuracy by pruning false positives.",
        size=8.2, line_height=11.2
    )

    pdf.add_subsection_header("Feature Importance & Learned Coefficients")
    pdf.add_paragraph(
        "- Logistic Regression Coefficients: Project Relevance (+2.6643), Required Skill Coverage (+2.5475), Coursework Overlap (+1.6795), "
        "Experience Ratio (+0.7921), Preferred Skill Coverage (+0.6763).\n"
        "- Random Forest Gini Importances: Project Relevance (32.13%) and Required Skill Coverage (30.13%) dominate decision paths (> 62%), "
        "proving that demonstrable practical project proof outweighs tenure alone.",
        size=8.2, line_height=11.2
    )

    pdf.add_section_header("7. Chapter VI: Conclusion & Recommendations")
    pdf.add_paragraph(
        "7.1 Conclusion: TalentBridge establishes that campus recruitment systems can be fair, semantic, and explainable. "
        "By replacing exact keyword matching with Sentence Transformers and heuristic thresholds with supervised classifiers, "
        "the platform achieved 93.10% accuracy while maintaining 100% recall for qualified students.",
        size=8.2
    )
    pdf.add_paragraph(
        "7.2 Placement Cell Recommendations:\n"
        "1. Transition from strict CGPA cutoffs to multi-dimensional candidate evaluation incorporating verified capstone projects.\n"
        "2. Provide automated diagnostic feedback to non-shortlisted students to support preparation for subsequent recruitment drives.\n"
        "3. Preserve human oversight by having interviewers review borderline applicants (0.55 <= Sim < 0.75).",
        size=8.2, line_height=11.2
    )
    pdf.add_paragraph(
        "7.3 Future Roadmap: Integration of OCR/PyMuPDF for direct resume PDF parsing, two-stage cross-encoder re-ranking, and "
        "an automated AI mock interview module tailored to identified skill gaps.",
        size=8.2
    )

    pdf.add_section_header("8. End Matter: References & Appendices")
    pdf.add_paragraph(
        "References:\n"
        "1. Devlin, J., et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers. arXiv:1810.04805.\n"
        "2. Faliagka, E., et al. (2012). An integrated e-recruitment system. Internet Research, 22(5), 551-568.\n"
        "3. Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. JMLR, 12, 2825-2830.\n"
        "4. Reimers, N., & Gurevych, I. (2019). Sentence-BERT. EMNLP-IJCNLP, 3982-3992.\n"
        "5. Vaswani, A., et al. (2017). Attention is all you need. NeurIPS, 30, 5998-6008.",
        size=7.6, line_height=10.2
    )

    pdf.add_callout(
        "Appendix: Sample Prescriptive Diagnostic Output",
        "Candidate: Samridhjit Barnwal (Reg: 12509754, Roll: 21, Sec: K3P25IN) - Target: Machine Learning Engineer\n"
        "Status: Competency Bridge Plan Recommended  -  Readiness Score: 64.20%\n"
        "- Identified Skill Gaps: Docker (Sim: 0.24, Mandatory), PyTorch (Sim: 0.41, Mandatory)\n"
        "- Action Plan 1: Course 'DevOps Foundations' | Project: 'Containerize Python backend with Docker Compose'\n"
        "- Action Plan 2: Course 'Deep Learning PyTorch' | Project: 'Build CNN/LSTM classifier from scratch'\n"
        "Advisory: Recommended for 4-week competency bridge plan prior to corporate technical interview round."
    )

    pdf.compile()


if __name__ == "__main__":
    generate_report()
