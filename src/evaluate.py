import sys
import os
sys.path.append(".")
from resume_parser import parse_resume
from jd_parser import parse_jd
from matcher import calculate_match
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import spearmanr

JOB_DESCRIPTION = """
We are hiring a Data Analyst.

Required skills: Python, SQL, Machine Learning, Data Analysis.
Must have at least 2 years of experience.
Bachelor's degree in Computer Science or related field required.

Nice to have: Power BI, Tableau, AWS experience is a plus.
Strong communication skills preferred.
"""

# My own honest, manually-assigned relevance scores (1-5) for each resume,
# based on reading each one against the JD above.
HUMAN_SCORES = {
    "resume_1_priya.docx": 5,
    "resume_2_arjun.docx": 1,
    "resume_3_kavya.docx": 3,
    "resume_04_rohan.docx": 5,
    "resume_05_ananya.docx": 1,
    "resume_06_vikram.docx": 1,
    "resume_07_sneha.docx": 3,
    "resume_08_karthik.docx": 2,
    "resume_09_meera.docx": 3,
    "resume_10_aditya.docx": 4,
    "resume_11_ishita.docx": 5,
    "resume_12_rahul.docx": 1,
    "resume_13_divya.docx": 3,
    "resume_14_siddharth.docx": 1,
    "resume_15_pooja.docx": 3,
    "resume_16_farhan.docx": 1,
    "resume_17_neha.docx": 3,
    "resume_18_arvind.docx": 1,
}

RESUME_FOLDER = "../data/resumes"


def run_hybrid_model(jd_data, resume_data):
    result = calculate_match(resume_data, jd_data)
    return result["final_score"]


def run_tfidf_baseline(jd_text, resume_texts):
    """The 'everyone else's approach' baseline: plain TF-IDF + cosine similarity."""
    vectorizer = TfidfVectorizer(stop_words="english")
    all_texts = [jd_text] + resume_texts
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    jd_vector = tfidf_matrix[0:1]
    resume_vectors = tfidf_matrix[1:]
    scores = cosine_similarity(jd_vector, resume_vectors)[0]
    return scores


def main():
    jd_data = parse_jd(JOB_DESCRIPTION)

    filenames = []
    human_scores = []
    hybrid_scores = []
    resume_texts = []

    print("Parsing resumes and computing hybrid model scores...\n")
    for filename, human_score in HUMAN_SCORES.items():
        path = os.path.join(RESUME_FOLDER, filename)
        if not os.path.exists(path):
            print(f"⚠ Skipping {filename} — file not found")
            continue

        resume_data = parse_resume(path)
        hybrid_score = run_hybrid_model(jd_data, resume_data)

        filenames.append(filename)
        human_scores.append(human_score)
        hybrid_scores.append(hybrid_score)
        resume_texts.append(resume_data["raw_text"])

        print(f"{resume_data['name'] or filename}: "
              f"human={human_score}, hybrid_model={hybrid_score:.1f}")

    print("\nComputing TF-IDF baseline scores...")
    tfidf_scores = run_tfidf_baseline(JOB_DESCRIPTION, resume_texts)

    # Spearman correlation: how well does each ranking match human judgment?
    hybrid_corr, hybrid_p = spearmanr(human_scores, hybrid_scores)
    tfidf_corr, tfidf_p = spearmanr(human_scores, tfidf_scores)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Number of candidates evaluated: {len(filenames)}")
    print(f"\nSpearman correlation with human judgment:")
    print(f"  Hybrid Model (ours):     {hybrid_corr:.3f}  (p={hybrid_p:.4f})")
    print(f"  TF-IDF Baseline (basic): {tfidf_corr:.3f}  (p={tfidf_p:.4f})")

    if hybrid_corr > tfidf_corr:
        improvement = ((hybrid_corr - tfidf_corr) / abs(tfidf_corr)) * 100 if tfidf_corr != 0 else float("inf")
        print(f"\n✅ Hybrid model correlates {improvement:.1f}% better with human judgment than the TF-IDF baseline.")
    else:
        print(f"\n⚠ Baseline performed as well or better — worth investigating why.")

    # Save results to CSV for the README / report
    import csv
    with open("../data/evaluation_results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Human Score", "Hybrid Model Score", "TF-IDF Score"])
        for i in range(len(filenames)):
            writer.writerow([filenames[i], human_scores[i], round(hybrid_scores[i], 1), round(tfidf_scores[i], 3)])

    print("\nDetailed results saved to data/evaluation_results.csv")


if __name__ == "__main__":
    main()