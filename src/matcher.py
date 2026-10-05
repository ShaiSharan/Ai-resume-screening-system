import re
from sentence_transformers import SentenceTransformer, util

# Load the semantic model once (this may take a few seconds the first time)
print("Loading semantic model... (first run may take a minute)")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded.")


def semantic_similarity(resume_text, jd_text):
    """
    Compare the overall meaning of the resume against the JD,
    not just exact keyword overlap.
    Returns a score between 0 and 1.
    """
    embeddings = model.encode([resume_text, jd_text], convert_to_tensor=True)
    score = util.cos_sim(embeddings[0], embeddings[1]).item()
    return max(0.0, min(1.0, score))


def find_evidence_sentence(skill, resume_text):
    """
    Find the sentence in the resume where a skill was mentioned,
    to use as proof/explanation in the UI. Returns None if not found.
    """
    sentences = re.split(r'(?<=[.\n])\s*', resume_text)
    for sentence in sentences:
        clean = sentence.strip()
        if skill.lower() in clean.lower() and len(clean) > 3:
            return clean
    return None


def skill_match_score(resume_skills, must_have, nice_to_have, resume_text):
    """
    Calculate how well the candidate's skills cover the JD's requirements.
    Must-have skills matter much more than nice-to-have ones.
    Also collects an evidence sentence for each matched skill.
    """
    resume_skills_set = set(resume_skills)

    matched_must = [s for s in must_have if s in resume_skills_set]
    missing_must = [s for s in must_have if s not in resume_skills_set]
    matched_nice = [s for s in nice_to_have if s in resume_skills_set]
    missing_nice = [s for s in nice_to_have if s not in resume_skills_set]

    evidence = {}
    for skill in matched_must + matched_nice:
        sentence = find_evidence_sentence(skill, resume_text)
        if sentence:
            evidence[skill] = sentence

    must_have_ratio = len(matched_must) / len(must_have) if must_have else 1.0
    nice_to_have_ratio = len(matched_nice) / len(nice_to_have) if nice_to_have else 0.0

    combined_score = (must_have_ratio * 0.85) + (nice_to_have_ratio * 0.15)

    return {
        "score": combined_score,
        "matched_must_have": matched_must,
        "missing_must_have": missing_must,
        "matched_nice_to_have": matched_nice,
        "missing_nice_to_have": missing_nice,
        "evidence": evidence,
    }


def experience_score(resume_years, min_required_years):
    """
    1.0 if they meet or exceed the requirement.
    Partial credit if they're close but under.
    """
    if min_required_years == 0:
        return 1.0
    if resume_years >= min_required_years:
        return 1.0
    ratio = resume_years / min_required_years
    return max(0.0, ratio)


def education_score(resume_level_score, required_level_score):
    """
    1.0 if resume education meets or exceeds requirement, partial credit otherwise.
    """
    if required_level_score == 0:
        return 1.0
    if resume_level_score >= required_level_score:
        return 1.0
    diff = required_level_score - resume_level_score
    return max(0.0, 1.0 - (diff * 0.3))


def generate_interview_questions(missing_must_have, missing_nice_to_have, matched_must_have):
    """
    Auto-generate a few starter interview questions based on the candidate's
    skill gaps and strengths, to help the recruiter prep quickly.
    """
    questions = []

    for skill in missing_must_have[:2]:
        questions.append(
            f"This role requires {skill}, which wasn't found on the resume — "
            f"ask the candidate about any hands-on experience with {skill}, even informal or academic."
        )

    for skill in missing_nice_to_have[:1]:
        questions.append(
            f"{skill} is a nice-to-have for this role — worth asking if they have any exposure to it."
        )

    if matched_must_have:
        top_skill = matched_must_have[0]
        questions.append(
            f"Ask the candidate to walk through a specific project where they used {top_skill}, "
            f"to verify depth beyond a keyword match."
        )

    return questions


def generate_verdict(resume_data, jd_data, skill_result, exp_score, edu_score, final_score):
    """
    Produce a short, natural-language recruiter verdict instead of raw lists —
    a quick 'what should I do with this candidate' summary.
    """
    name = resume_data.get("name") or "This candidate"

    if final_score >= 75:
        action = "Strong Hire — Fast-track"
    elif final_score >= 60:
        action = "Interview"
    elif final_score >= 40:
        action = "Consider with reservations"
    else:
        action = "Likely Pass"

    parts = []

    must_have = jd_data["must_have_skills"]
    matched_count = len(skill_result["matched_must_have"])
    total_must = len(must_have)

    if must_have:
        if matched_count == total_must:
            parts.append(f"{name} meets all {total_must} core skill requirements")
        elif matched_count > 0:
            parts.append(
                f"{name} meets {matched_count} of {total_must} core skill requirements, "
                f"missing {', '.join(skill_result['missing_must_have'])}"
            )
        else:
            parts.append(f"{name} does not match the core skills required for this role")

    if exp_score >= 1.0:
        parts.append(f"has sufficient experience ({resume_data['experience_years']} years)")
    elif exp_score > 0:
        parts.append(f"is somewhat under the experience bar ({resume_data['experience_years']} years)")
    else:
        parts.append("has no clearly stated relevant experience")

    if skill_result["matched_nice_to_have"]:
        parts.append(f"and brings bonus skills in {', '.join(skill_result['matched_nice_to_have'][:2])}")

    summary = ". ".join(p.capitalize() for p in parts) + "."

    return {
        "action": action,
        "summary": summary,
    }


def calculate_match(resume_data, jd_data, weights=None):
    """
    Combine all sub-scores into one final weighted match score (0-100),
    with a full explanation of how the score was reached.
    """
    if weights is None:
        weights = {
            "semantic": 0.40,
            "skills": 0.30,
            "experience": 0.15,
            "education": 0.15,
        }

    sem_score = semantic_similarity(resume_data["raw_text"], jd_data["raw_text"])
    skill_result = skill_match_score(
        resume_data["skills"],
        jd_data["must_have_skills"],
        jd_data["nice_to_have_skills"],
        resume_data["raw_text"],
    )
    exp_score = experience_score(
        resume_data["experience_years"],
        jd_data["min_experience_years"],
    )
    edu_score = education_score(
        resume_data["education"]["level_score"],
        jd_data["education"]["level_score"],
    )

    final_score = (
        sem_score * weights["semantic"]
        + skill_result["score"] * weights["skills"]
        + exp_score * weights["experience"]
        + edu_score * weights["education"]
    )

    final_score_rounded = round(final_score * 100, 1)

    interview_questions = generate_interview_questions(
        skill_result["missing_must_have"],
        skill_result["missing_nice_to_have"],
        skill_result["matched_must_have"],
    )

    verdict = generate_verdict(
        resume_data, jd_data, skill_result, exp_score, edu_score, final_score_rounded
    )

    return {
        "candidate_name": resume_data.get("name"),
        "final_score": final_score_rounded,
        "breakdown": {
            "semantic_similarity": round(sem_score * 100, 1),
            "skill_match": round(skill_result["score"] * 100, 1),
            "experience_match": round(exp_score * 100, 1),
            "education_match": round(edu_score * 100, 1),
        },
        "explanation": {
            "matched_must_have_skills": skill_result["matched_must_have"],
            "missing_must_have_skills": skill_result["missing_must_have"],
            "matched_nice_to_have_skills": skill_result["matched_nice_to_have"],
            "missing_nice_to_have_skills": skill_result["missing_nice_to_have"],
            "candidate_experience_years": resume_data["experience_years"],
            "required_experience_years": jd_data["min_experience_years"],
            "candidate_education": resume_data["education"]["highest_level"],
            "required_education": jd_data["education"]["min_level"],
            "evidence": skill_result["evidence"],
        },
        "interview_questions": interview_questions,
        "verdict": verdict,
    }


if __name__ == "__main__":
    import json
    import sys
    sys.path.append(".")
    from resume_parser import parse_resume
    from jd_parser import parse_jd

    sample_jd_text = """
    We are hiring a Data Analyst.

    Required skills: Python, SQL, Machine Learning, Data Analysis.
    Must have at least 2 years of experience.
    Bachelor's degree in Computer Science or related field required.

    Nice to have: Power BI, Tableau, AWS experience is a plus.
    Strong communication skills preferred.
    """

    jd_data = parse_jd(sample_jd_text)
    resume_data = parse_resume("../data/resumes/resume_1_priya.docx")

    result = calculate_match(resume_data, jd_data)
    print(json.dumps(result, indent=2))