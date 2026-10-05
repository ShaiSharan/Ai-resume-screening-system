from docx import Document
import os

os.makedirs("../data/resumes", exist_ok=True)

samples = [
    {
        "filename": "resume_1_priya.docx",
        "content": """Priya Sharma
priya.sharma@email.com | +91 9876543210

Summary
Data Analyst with 3 years of experience in Python, SQL, and Machine Learning. Passionate about turning data into actionable insights.

Education
Bachelor of Technology (B.Tech) in Computer Science, 2021

Skills
Python, SQL, Machine Learning, Pandas, NumPy, Power BI, Excel, Data Analysis, Communication

Work Experience
Data Analyst, TechCorp Solutions (2021 - Present)
- Built ML models to predict customer churn, improving retention by 15%
- Automated reporting pipelines using Python and SQL, saving 10 hours/week
- Collaborated with cross-functional teams on data-driven decision making

Projects
Customer Segmentation using K-Means Clustering
Sales Forecasting Dashboard using Power BI
""",
    },
    {
        "filename": "resume_2_arjun.docx",
        "content": """Arjun Mehta
arjun.mehta@email.com | 9123456780

Summary
Software Engineer with 5+ years experience in full-stack development, cloud infrastructure, and leadership of small engineering teams.

Education
Master of Technology (M.Tech) in Software Engineering, 2019

Skills
Java, JavaScript, React, Node.js, AWS, Docker, Kubernetes, Git, Leadership, Project Management

Work Experience
Senior Software Engineer, CloudNine Systems (2020 - Present)
- Led a team of 4 engineers building a microservices platform on AWS
- Migrated legacy monolith to Kubernetes, reducing deployment time by 40%
- Mentored junior developers and ran sprint planning

Software Engineer, WebWorks Inc (2019 - 2020)
- Built customer-facing features using React and Node.js
- Improved API response times by 25% through caching strategies

Projects
E-commerce Platform Backend (Node.js, AWS)
Real-time Chat Application (React, WebSockets)
""",
    },
    {
        "filename": "resume_3_kavya.docx",
        "content": """Kavya Reddy
kavya.reddy@email.com | +91 9988776655

Summary
Fresh graduate with strong foundation in Python and Data Science, seeking entry-level opportunities.

Education
Bachelor of Science (B.Sc) in Computer Science, 2024

Skills
Python, SQL, Machine Learning, Data Analysis, Communication

Projects
Movie Recommendation System using Collaborative Filtering
Student Performance Prediction using Linear Regression
Titanic Survival Prediction (Kaggle competition, top 20%)

Certifications
Google Data Analytics Certificate
Python for Data Science - Coursera
""",
    },
]

for sample in samples:
    doc = Document()
    for line in sample["content"].strip().split("\n"):
        doc.add_paragraph(line)
    path = os.path.join("../data/resumes", sample["filename"])
    doc.save(path)
    print(f"Created: {path}")

print("\nDone! 3 sample resumes created in data/resumes/")