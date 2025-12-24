# resume_analyzer.py

import os
import re

from PyPDF2 import PdfReader

try:
    import docx  # for .docx files
except ImportError:
    docx = None


# -------------------------------------------------
# 1. Skill Dictionary
# -------------------------------------------------
SKILL_KEYWORDS = {
    "Python": ["python"],
    "Java": ["java"],
    "C++": ["c++", "cpp", "c ++"],
    "JavaScript": ["javascript", "js"],
    "HTML/CSS": ["html", "css", "html5", "css3"],
    "SQL": ["sql", "mysql", "postgresql", "oracle database", "sqlite"],
    "Data Structures": ["data structures", "linked list", "stack", "queue", "tree", "graph"],
    "Algorithms": ["algorithm", "time complexity", "sorting", "searching"],
    "Object Oriented Programming": ["oop", "object oriented", "object-oriented", "inheritance", "polymorphism"],
    "Machine Learning": ["machine learning", "ml", "supervised learning", "unsupervised learning"],
    "Deep Learning": ["deep learning", "neural network", "cnn", "rnn"],
    "Data Analysis": ["data analysis", "pandas", "numpy", "data cleaning"],
    "Version Control / Git": ["git", "github", "gitlab", "bitbucket"],
    "Operating Systems": ["operating system", "os", "process management", "deadlock"],
    "Communication Skills": ["communication skills", "presentation", "teamwork", "collaboration"],
    "Problem Solving": ["problem solving", "analytical skills"],
}

# Canonical section names, in display order (for UI only)
SECTION_ORDER = [
    "Summary",
    "Objective",
    "Education",
    "Experience",
    "Projects",
    "Skills",
    "Certifications",
    "Achievements",
    "Other",
]

# Mapping of possible headings to canonical section names
SECTION_ALIASES = {
    "Summary": [
        "summary",
        "professional summary",
        "profile",
        "about me",
    ],
    "Objective": [
        "objective",
        "career objective",
        "career summary",
    ],
    "Education": [
        "education",
        "academic background",
        "educational background",
        "academics",
        "qualifications",
    ],
    "Experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "internship experience",
    ],
    "Projects": [
        "projects",
        "academic projects",
        "personal projects",
        "major projects",
        "minor projects",
    ],
    "Skills": [
        "skills",
        "technical skills",
        "key skills",
        "core competencies",
    ],
    "Certifications": [
        "certifications",
        "certification",
        "licenses",
        "courses",
        "relevant courses",
    ],
    "Achievements": [
        "achievements",
        "accomplishments",
        "awards",
        "honors",
    ],
}


# -------------------------------------------------
# 2. Text Extraction
# -------------------------------------------------
def extract_text_from_pdf(file_path: str) -> str:
    text = []
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def extract_text_from_docx(file_path: str) -> str:
    if docx is None:
        return ""
    document = docx.Document(file_path)
    return "\n".join(para.text for para in document.paragraphs)


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        return ""


# -------------------------------------------------
# 3. Helpers
# -------------------------------------------------
def normalize_text(text: str) -> str:
    text = text.lower()
    # Keep letters, digits, +, #, ., / and whitespace; remove the rest
    text = re.sub(r"[^a-z0-9+\s#./]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_skills_from_text(raw_text: str):
    """
    Extract skills from RAW text (resume or job description).
    """
    text = normalize_text(raw_text)
    found_skills = set()

    for skill_name, keywords in SKILL_KEYWORDS.items():
        for kw in keywords:
            kw_norm = normalize_text(kw)
            if kw_norm and kw_norm in text:
                found_skills.add(skill_name)
                break

    return found_skills


# -------------------------------------------------
# 4. Section Extraction (for UI only)
# -------------------------------------------------
def detect_section_heading(line: str):
    stripped = line.strip()
    if not stripped:
        return None

    # Remove trailing colon/hyphen only at the end
    cleaned = re.sub(r"[:\-]+$", "", stripped).strip().lower()

    for canonical, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if cleaned == alias.lower():
                return canonical

    return None


def split_into_sections(raw_text: str):
    """
    Split resume into sections using heading detection.
    Used only to display 'Extracted Resume Sections', NOT for skill logic.
    """
    lines = [l.rstrip() for l in raw_text.splitlines()]
    sections = {name: [] for name in SECTION_ORDER}
    current_section = "Other"

    for line in lines:
        if not line.strip():
            continue

        detected = detect_section_heading(line)
        if detected:
            current_section = detected
            continue

        sections[current_section].append(line)

    cleaned_sections = {}
    for name, content_lines in sections.items():
        joined = "\n".join(content_lines).strip()
        if joined:
            cleaned_sections[name] = joined

    return cleaned_sections


# -------------------------------------------------
# 5. Main Analysis Function
# -------------------------------------------------
def analyze_resume(resume_text: str, job_description_text: str = ""):
    """
    Main analyzer:
    - Skills in resume: from ENTIRE resume text only.
    - Required skills: from job description (if any), else full dictionary.
    - Sections: for display only.
    - Suggestions: categorized.
    """
    # A) Sections for UI
    sections = split_into_sections(resume_text)

    # B) Skills in resume (ENTIRE text)
    resume_skills = extract_skills_from_text(resume_text)

    # C) Required skills
    if job_description_text and job_description_text.strip():
        jd_skills = extract_skills_from_text(job_description_text)
        required_skills = jd_skills if jd_skills else set(SKILL_KEYWORDS.keys())
    else:
        required_skills = set(SKILL_KEYWORDS.keys())

    matched_skills = resume_skills.intersection(required_skills)
    missing_skills = required_skills.difference(resume_skills)

    # D) Score calculation (0–100)
    if required_skills:
        score_raw = (len(matched_skills) / float(len(required_skills))) * 100.0
    else:
        score_raw = 0.0

    score = max(0.0, min(100.0, round(score_raw, 2)))

    # E) Categorized Suggestions
    tech_suggestions = []
    soft_suggestions = []
    content_suggestions = []
    ats_suggestions = []

    # 1) Technical Skill Gaps
    if missing_skills:
        tech_suggestions.append(
            "You are missing important technical skills required for this role: "
            + ", ".join(sorted(missing_skills))
            + ". Add these in your Projects, Experience, or Skills section."
        )

    # 2) Soft Skills & Professional Traits
    if "Communication Skills" not in resume_skills:
        soft_suggestions.append("Add communication or teamwork examples in Experience or Projects.")
    if "Problem Solving" not in resume_skills:
        soft_suggestions.append("Highlight strong problem-solving achievements or coding challenges solved.")

    # 3) Resume Content & Structure
    if len(normalize_text(resume_text).split()) < 200:
        content_suggestions.append(
            "Your resume looks short. Add more details to projects, responsibilities, and measurable achievements."
        )
    if "Projects" not in sections:
        content_suggestions.append(
            "Add at least 2–3 technical projects (with technologies and outcomes) to strengthen your resume."
        )

    # 4) ATS Optimization
    if "Version Control / Git" not in resume_skills:
        ats_suggestions.append("Mention Git/GitHub in skills and list repositories to improve ATS visibility.")
    ats_suggestions.append(
        "Include exact keywords from the job description (skills, tools, role titles) to improve ATS matching."
    )

    categorized_suggestions = {
        "Technical Skill Gaps": tech_suggestions,
        "Soft Skills & Professional Traits": soft_suggestions,
        "Resume Content & Structure": content_suggestions,
        "ATS Optimization": ats_suggestions,
    }

    # Optional flat list (if needed anywhere)
    flat_suggestions = (
        tech_suggestions + soft_suggestions + content_suggestions + ats_suggestions
    )

    # Only show the sections that actually exist
    section_order_present = [s for s in SECTION_ORDER if s in sections]

    result = {
        "score": score,
        "resume_skills": sorted(resume_skills),
        "required_skills": sorted(required_skills),
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills),
        "suggestions": flat_suggestions,
        "categorized_suggestions": categorized_suggestions,
        "sections": sections,
        "section_order": section_order_present,
    }

    return result
