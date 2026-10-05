import re
from datetime import datetime
import spacy
import pdfplumber
from docx import Document

nlp = spacy.load("en_core_web_sm")

# --- Skill list & synonym map ---
# Add to this list as you find more skills in your dataset
SKILL_SYNONYMS = {
    "ml": "machine learning",
    "js": "javascript",
    "py": "python",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "dl": "deep learning",
    "db": "database",
    "oop": "object oriented programming",
    "ci/cd": "continuous integration",
}

KNOWN_SKILLS = [
    "python", "java", "c++", "sql", "javascript", "machine learning",
    "deep learning", "natural language processing", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "html", "css", "react", "node.js", "django", "flask",
    "aws", "azure", "gcp", "docker", "kubernetes", "git",
    "excel", "power bi", "tableau", "communication", "leadership",
    "project management", "data analysis", "data science",
]

EDUCATION_LEVELS = {
    "phd": 4, "doctorate": 4,
    "master": 3, "msc": 3, "mtech": 3, "mba": 3, "m.tech": 3, "m.sc": 3,
    "bachelor": 2, "bsc": 2, "btech": 2, "be": 2, "b.tech": 2, "b.sc": 2,
    "diploma": 1,
    "high school": 0, "12th": 0,
}


def extract_text(file_path):
    """Extract raw text from a PDF or DOCX resume."""
    if file_path.lower().endswith(".pdf"):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    elif file_path.lower().endswith(".docx"):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError("Unsupported file type. Use .pdf or .docx")


def extract_email(text):
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text):
    match = re.search(r"(\+?\d{1,3}[-.\s]?)?\d{10}", text)
    return match.group(0) if match else None


def extract_name(text):
    """Best-effort name extraction: try the first non-empty line first,
    since resumes almost always start with the candidate's name."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return None

    first_line = lines[0]

    # If the first line contains an email or phone, it's not a clean name line —
    # fall back to spaCy NER instead
    if "@" in first_line or re.search(r"\d{3,}", first_line):
        first_chunk = "\n".join(lines[:5])
        doc = nlp(first_chunk)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Only take the first line of a multi-line entity match
                return ent.text.split("\n")[0].strip()
        return None

    # First line looks like a clean name (short, no digits/symbols)
    if len(first_line.split()) <= 4 and not any(char.isdigit() for char in first_line):
        return first_line

    return None


def extract_skills(text):
    """Match known skills in the text, normalizing synonyms."""
    text_lower = text.lower()
    found = set()

    for skill in KNOWN_SKILLS:
        if skill in text_lower:
            found.add(skill)

    for short, full in SKILL_SYNONYMS.items():
        pattern = r"\b" + re.escape(short) + r"\b"
        if re.search(pattern, text_lower):
            found.add(full)

    return sorted(found)


def extract_education(text):
    """Return the highest education level found, plus the raw matches."""
    text_lower = text.lower()
    matches = []
    highest_level = -1
    highest_label = None

    for keyword, level in EDUCATION_LEVELS.items():
        if keyword in text_lower:
            matches.append(keyword)
            if level > highest_level:
                highest_level = level
                highest_label = keyword

    return {
        "highest_level": highest_label,
        "level_score": highest_level,
        "all_matches": matches,
    }


def extract_experience_years(text):
    """
    Estimate total years of experience two ways, and return the larger:
    1. Explicit phrases like '3 years', '5+ years of experience'
    2. Date ranges in work history like '2021 - Present', '2019-2023', 'Jan 2020 - Dec 2022'
    """
    text_lower = text.lower()
    current_year = datetime.now().year

    # --- Method 1: explicit "X years" phrases ---
    explicit_matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", text_lower)
    explicit_max = max((float(m) for m in explicit_matches), default=0.0)

    # --- Method 2: date ranges (YYYY - YYYY or YYYY - Present/Current) ---
    # Matches things like: 2021 - Present, 2019-2023, 2020 to current
    range_pattern = r"(20\d{2}|19\d{2})\s*[-\u2013\u2014to]+\s*(20\d{2}|19\d{2}|present|current|now)"
    range_matches = re.findall(range_pattern, text_lower)

    total_range_years = 0.0
    for start_str, end_str in range_matches:
        start_year = int(start_str)
        if end_str in ("present", "current", "now"):
            end_year = current_year
        else:
            end_year = int(end_str)
        duration = end_year - start_year
        if 0 <= duration <= 40:  # sanity check, ignore garbage matches
            total_range_years += duration

    return max(explicit_max, total_range_years)


def parse_resume(file_path):
    """Main entry point: turn a resume file into structured data."""
    text = extract_text(file_path)

    return {
        "file_path": file_path,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience_years": extract_experience_years(text),
        "raw_text": text,
    }


if __name__ == "__main__":
    # Quick manual test — update this path to a real resume file to try it
    import json
    test_file = "../data/resumes/resume_1_priya.docx"
    result = parse_resume(test_file)
    print(json.dumps(result, indent=2))