import re

# Reuse the same skill list as the resume parser for consistent matching
KNOWN_SKILLS = [
    "python", "java", "c++", "sql", "javascript", "machine learning",
    "deep learning", "natural language processing", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "html", "css", "react", "node.js", "django", "flask",
    "aws", "azure", "gcp", "docker", "kubernetes", "git",
    "excel", "power bi", "tableau", "communication", "leadership",
    "project management", "data analysis", "data science",
]

SKILL_SYNONYMS = {
    "ml": "machine learning",
    "js": "javascript",
    "py": "python",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "dl": "deep learning",
}

EDUCATION_LEVELS = {
    "phd": 4, "doctorate": 4,
    "master": 3, "msc": 3, "mtech": 3, "mba": 3, "m.tech": 3, "m.sc": 3,
    "bachelor": 2, "bsc": 2, "btech": 2, "be": 2, "b.tech": 2, "b.sc": 2,
    "diploma": 1,
    "high school": 0, "12th": 0,
}

# Words that signal a requirement is mandatory vs. just preferred
MUST_HAVE_SIGNALS = ["required", "must have", "must-have", "mandatory", "essential", "need to have"]
NICE_TO_HAVE_SIGNALS = ["preferred", "nice to have", "nice-to-have", "bonus", "plus", "good to have", "a plus"]


def extract_skills_with_priority(text):
    """
    Find skills in the JD text and classify each as must-have or nice-to-have
    based on nearby signal words in the same sentence.
    """
    text_lower = text.lower()
    sentences = re.split(r'[.\n]', text_lower)

    must_have = set()
    nice_to_have = set()

    all_skill_terms = list(KNOWN_SKILLS)

    for sentence in sentences:
        is_must = any(signal in sentence for signal in MUST_HAVE_SIGNALS)
        is_nice = any(signal in sentence for signal in NICE_TO_HAVE_SIGNALS)

        for skill in all_skill_terms:
            if skill in sentence:
                if is_nice and not is_must:
                    nice_to_have.add(skill)
                else:
                    # Default: if no signal word found, treat as must-have
                    # (most JDs list core requirements without explicitly saying "required")
                    must_have.add(skill)

        for short, full in SKILL_SYNONYMS.items():
            pattern = r"\b" + re.escape(short) + r"\b"
            if re.search(pattern, sentence):
                if is_nice and not is_must:
                    nice_to_have.add(full)
                else:
                    must_have.add(full)

    # A skill shouldn't appear in both lists — must-have takes priority
    nice_to_have -= must_have

    return sorted(must_have), sorted(nice_to_have)


def extract_min_experience(text):
    """Look for patterns like '3+ years', 'minimum 5 years', '2-4 years'."""
    text_lower = text.lower()
    matches = re.findall(r"(\d+)\s*\+?\s*-?\s*(?:to\s*\d+\s*)?years?", text_lower)
    if matches:
        return min(int(m) for m in matches)  # take the lowest as the minimum bar
    return 0


def extract_required_education(text):
    """Return the minimum education level mentioned in the JD."""
    text_lower = text.lower()
    lowest_level = None
    lowest_score = 99

    for keyword, level in EDUCATION_LEVELS.items():
        if keyword in text_lower:
            if level < lowest_score:
                lowest_score = level
                lowest_level = keyword

    return {
        "min_level": lowest_level,
        "level_score": lowest_score if lowest_level else 0,
    }


def parse_jd(text):
    """Main entry point: turn raw JD text into structured requirements."""
    must_have, nice_to_have = extract_skills_with_priority(text)

    return {
        "must_have_skills": must_have,
        "nice_to_have_skills": nice_to_have,
        "min_experience_years": extract_min_experience(text),
        "education": extract_required_education(text),
        "raw_text": text,
    }


if __name__ == "__main__":
    import json

    sample_jd = """
    We are hiring a Data Analyst.

    Required skills: Python, SQL, Machine Learning, Data Analysis.
    Must have at least 2 years of experience.
    Bachelor's degree in Computer Science or related field required.

    Nice to have: Power BI, Tableau, AWS experience is a plus.
    Strong communication skills preferred.
    """

    result = parse_jd(sample_jd)
    print(json.dumps(result, indent=2))