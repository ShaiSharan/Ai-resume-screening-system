import sys
sys.path.append(".")
from resume_parser import parse_resume
from jd_parser import parse_jd
import os

JOB_DESCRIPTION = """
We are hiring a Backend Software Engineer.

Required skills: Java, SQL, AWS, Docker, Git.
Must have at least 3 years of experience.
Bachelor's degree in Computer Science or related field required.

Nice to have: Kubernetes, Node.js, Leadership experience is a plus.
"""

jd_data = parse_jd(JOB_DESCRIPTION)
print(f"JD requires minimum experience: {jd_data['min_experience_years']} years")
print(f"JD requires minimum education: {jd_data['education']['min_level']} (score: {jd_data['education']['level_score']})")
print("-" * 60)

resume_folder = "../data/resumes"
for filename in sorted(os.listdir(resume_folder)):
    if filename.lower().endswith((".pdf", ".docx")):
        resume_data = parse_resume(os.path.join(resume_folder, filename))
        print(f"{resume_data['name'] or filename}: "
              f"{resume_data['experience_years']} years experience, "
              f"education = {resume_data['education']['highest_level']} "
              f"(score: {resume_data['education']['level_score']})")