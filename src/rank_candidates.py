import json
import os
import sys

sys.path.append(".")
from resume_parser import parse_resume
from jd_parser import parse_jd
from matcher import calculate_match

RESUME_FOLDER = "../data/resumes"

# Same sample JD as before — feel free to edit this to test different roles
JOB_DESCRIPTION = """
We are hiring a Data Analyst.

Required skills: Python, SQL, Machine Learning, Data Analysis.
Must have at least 2 years of experience.
Bachelor's degree in Computer Science or related field required.

Nice to have: Power BI, Tableau, AWS experience is a plus.
Strong communication skills preferred.
"""


def rank_all_resumes(resume_folder, jd_text):
    jd_data = parse_jd(jd_text)
    results = []

    for filename in os.listdir(resume_folder):
        if filename.lower().endswith((".pdf", ".docx")):
            file_path = os.path.join(resume_folder, filename)
            print(f"Parsing: {filename}...")
            resume_data = parse_resume(file_path)
            match_result = calculate_match(resume_data, jd_data)
            results.append(match_result)

    # Sort by final_score, highest first
    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results


if __name__ == "__main__":
    ranked = rank_all_resumes(RESUME_FOLDER, JOB_DESCRIPTION)

    print("\n" + "=" * 60)
    print("CANDIDATE RANKING")
    print("=" * 60)

    for i, result in enumerate(ranked, 1):
        print(f"\n#{i} — {result['candidate_name']} — Score: {result['final_score']}/100")
        print(f"   Semantic: {result['breakdown']['semantic_similarity']}% | "
              f"Skills: {result['breakdown']['skill_match']}% | "
              f"Experience: {result['breakdown']['experience_match']}% | "
              f"Education: {result['breakdown']['education_match']}%")
        print(f"   Matched must-haves: {result['explanation']['matched_must_have_skills']}")
        if result['explanation']['missing_must_have_skills']:
            print(f"   ⚠ Missing must-haves: {result['explanation']['missing_must_have_skills']}")

    # Also save full results as JSON for later use in the UI
    with open("../data/ranking_results.json", "w") as f:
        json.dump(ranked, f, indent=2)
    print("\n\nFull results saved to data/ranking_results.json")