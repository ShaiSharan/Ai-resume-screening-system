import streamlit as st
import pandas as pd
import altair as alt
import sys
import os
from collections import Counter

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from resume_parser import parse_resume
from jd_parser import parse_jd
from matcher import calculate_match

st.set_page_config(page_title="AI Resume Screener", layout="wide", page_icon="🎯")

st.title("🎯 AI Resume Screening System")
st.caption("Upload a job description and resumes to get a ranked, explainable shortlist — in seconds.")

SAMPLE_JD = """We are hiring a Data Analyst.

Required skills: Python, SQL, Machine Learning, Data Analysis.
Must have at least 2 years of experience.
Bachelor's degree in Computer Science or related field required.

Nice to have: Power BI, Tableau, AWS experience is a plus.
Strong communication skills preferred."""

st.sidebar.header("⚙️ Scoring Priority")
st.sidebar.caption("Choose what matters most for this role.")

preset = st.sidebar.radio(
    "Preset",
    ["Balanced", "Skills-Focused", "Experience-Focused", "Custom"],
    label_visibility="collapsed",
)

PRESETS = {
    "Balanced":            {"semantic": 40, "skills": 30, "experience": 15, "education": 15},
    "Skills-Focused":      {"semantic": 25, "skills": 55, "experience": 10, "education": 10},
    "Experience-Focused":  {"semantic": 25, "skills": 25, "experience": 40, "education": 10},
}

if preset == "Custom":
    with st.sidebar.expander("Advanced: fine-tune weights", expanded=True):
        st.caption("These auto-normalize to 100%.")
        w_semantic = st.slider("Overall fit (semantic meaning)", 0, 100, 40)
        w_skills = st.slider("Skill match", 0, 100, 30)
        w_experience = st.slider("Experience match", 0, 100, 15)
        w_education = st.slider("Education match", 0, 100, 15)
else:
    p = PRESETS[preset]
    w_semantic, w_skills, w_experience, w_education = (
        p["semantic"], p["skills"], p["experience"], p["education"]
    )
    st.sidebar.caption(
        f"Overall fit {w_semantic}% · Skills {w_skills}% · "
        f"Experience {w_experience}% · Education {w_education}%"
    )

total_w = max(w_semantic + w_skills + w_experience + w_education, 1)
weights = {
    "semantic": w_semantic / total_w,
    "skills": w_skills / total_w,
    "experience": w_experience / total_w,
    "education": w_education / total_w,
}

st.sidebar.markdown("---")
anonymize = st.sidebar.checkbox("🕶️ Bias-reduction mode (hide names)", value=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Job Description")
    if st.button("↺ Load sample JD (for quick demo)"):
        st.session_state["jd_text"] = SAMPLE_JD
    jd_text = st.text_area(
        "Paste the job description here",
        height=220,
        placeholder="e.g. We are hiring a Data Analyst. Required skills: Python, SQL...",
        key="jd_text",
    )

with col2:
    st.subheader("2. Upload Resumes")
    uploaded_files = st.file_uploader(
        "Upload one or more resumes (PDF or DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        st.caption(f"✅ {len(uploaded_files)} resume(s) ready")

run_button = st.button("🚀 Rank Candidates", type="primary", use_container_width=True)

if run_button:
    if not jd_text.strip():
        st.error("Please paste a job description first.")
    elif not uploaded_files:
        st.error("Please upload at least one resume.")
    else:
        with st.spinner("Parsing and scoring candidates..."):
            jd_data = parse_jd(jd_text)

            results = []
            for uploaded_file in uploaded_files:
                temp_path = os.path.join("temp_" + uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                resume_data = parse_resume(temp_path)
                match_result = calculate_match(resume_data, jd_data, weights=weights)
                results.append(match_result)

                os.remove(temp_path)

            results.sort(key=lambda r: r["final_score"], reverse=True)

        st.success(f"Scored {len(results)} candidates.")

        # --- Headline summary metrics ---
        top = results[0]
        avg_score = round(sum(r["final_score"] for r in results) / len(results), 1)
        strong_fits = sum(1 for r in results if r["final_score"] >= 70)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🏆 Top Candidate",
                   "Candidate 1" if anonymize else top["candidate_name"],
                   f"{top['final_score']}/100")
        m2.metric("👥 Total Screened", len(results))
        m3.metric("📊 Average Score", f"{avg_score}/100")
        m4.metric("✅ Strong Fits (70+)", strong_fits)

        st.markdown("---")

        with st.expander("📋 Parsed Job Requirements"):
            st.write("**Must-have skills:**", ", ".join(jd_data["must_have_skills"]) or "None detected")
            st.write("**Nice-to-have skills:**", ", ".join(jd_data["nice_to_have_skills"]) or "None detected")
            st.write("**Minimum experience:**", f"{jd_data['min_experience_years']} years")
            st.write("**Minimum education:**", jd_data["education"]["min_level"] or "Not specified")

        # --- Ranked table with color-coded scores ---
        st.subheader("Ranked Candidates")

        table_rows = []
        for i, r in enumerate(results, 1):
            display_name = f"Candidate {i}" if anonymize else r["candidate_name"]
            table_rows.append({
                "Rank": i,
                "Candidate": display_name,
                "Final Score": r["final_score"],
                "Semantic %": r["breakdown"]["semantic_similarity"],
                "Skills %": r["breakdown"]["skill_match"],
                "Experience %": r["breakdown"]["experience_match"],
                "Education %": r["breakdown"]["education_match"],
            })

        df = pd.DataFrame(table_rows)

        def score_color(val):
            if val >= 70:
                return "background-color: rgba(46, 204, 113, 0.25)"
            elif val >= 50:
                return "background-color: rgba(241, 196, 15, 0.25)"
            else:
                return "background-color: rgba(231, 76, 60, 0.25)"

        styled_df = df.style.map(score_color, subset=["Final Score"]).format({
            "Final Score": "{:.1f}",
            "Semantic %": "{:.1f}",
            "Skills %": "{:.1f}",
            "Experience %": "{:.1f}",
            "Education %": "{:.1f}",
        })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # --- Score comparison chart with clear labels, sorted, value labels on bars ---
        st.subheader("Score Comparison")
        chart_df = df[["Candidate", "Final Score"]].copy()

        bars = alt.Chart(chart_df).mark_bar(color="#5B9BF7").encode(
            x=alt.X("Final Score:Q", title="Final Score (out of 100)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Candidate:N", sort="-x", title=None),
            tooltip=["Candidate", "Final Score"],
        )
        text = bars.mark_text(align="left", dx=3, color="white").encode(text="Final Score:Q")
        st.altair_chart((bars + text).properties(height=28 * len(chart_df)), use_container_width=True)

        # --- Talent pool insights: aggregate, company-level view, not per-candidate repeats ---
        st.subheader("Talent Pool Insights")
        st.caption("What this batch of candidates tells you about your hiring pool overall.")

        missing_skill_counter = Counter()
        for r in results:
            for skill in r["explanation"]["missing_must_have_skills"]:
                missing_skill_counter[skill] += 1

        insight_col1, insight_col2 = st.columns(2)

        with insight_col1:
            st.markdown("**🔍 Hardest-to-find required skills**")
            st.caption("Number of candidates missing each required skill — higher bar = harder to find.")
            if missing_skill_counter:
                gap_df = pd.DataFrame(
                    missing_skill_counter.most_common(),
                    columns=["Skill", "Missing Count"],
                )
                gap_bars = alt.Chart(gap_df).mark_bar(color="#F76B6B").encode(
                    x=alt.X("Missing Count:Q", title=f"Candidates missing this skill (out of {len(results)})"),
                    y=alt.Y("Skill:N", sort="-x", title=None),
                    tooltip=["Skill", "Missing Count"],
                )
                gap_text = gap_bars.mark_text(align="left", dx=3, color="white").encode(text="Missing Count:Q")
                st.altair_chart((gap_bars + gap_text).properties(height=28 * len(gap_df)), use_container_width=True)

                top_gap_skill, top_gap_count = missing_skill_counter.most_common(1)[0]
                st.caption(
                    f"💡 **{top_gap_skill}** is missing from **{top_gap_count} of {len(results)}** candidates — "
                    f"consider whether this requirement is too strict, or plan training for it."
                )
            else:
                st.write("All candidates cover every must-have skill. No gaps found.")

        with insight_col2:
            st.markdown("**📊 Candidate quality spread**")
            st.caption("How many candidates fall into each score band.")
            strong = sum(1 for r in results if r["final_score"] >= 70)
            moderate = sum(1 for r in results if 50 <= r["final_score"] < 70)
            weak = sum(1 for r in results if r["final_score"] < 50)

            spread_df = pd.DataFrame({
                "Category": ["Strong (70+)", "Moderate (50-69)", "Weak (<50)"],
                "Candidates": [strong, moderate, weak],
            })
            spread_bars = alt.Chart(spread_df).mark_bar().encode(
                x=alt.X("Candidates:Q", title="Number of candidates"),
                y=alt.Y("Category:N", sort=None, title=None),
                color=alt.Color(
                    "Category:N",
                    scale=alt.Scale(
                        domain=["Strong (70+)", "Moderate (50-69)", "Weak (<50)"],
                        range=["#2ECC71", "#F1C40F", "#E74C3C"],
                    ),
                    legend=None,
                ),
                tooltip=["Category", "Candidates"],
            )
            spread_text = spread_bars.mark_text(align="left", dx=3, color="white").encode(text="Candidates:Q")
            st.altair_chart((spread_bars + spread_text).properties(height=140), use_container_width=True)

            if strong == 0:
                st.caption("⚠️ No strong fits in this batch — consider widening sourcing or relaxing requirements.")
            elif strong >= len(results) * 0.5:
                st.caption(f"✅ Healthy pool — {strong} of {len(results)} candidates are strong fits.")
            else:
                st.caption(f"{strong} of {len(results)} candidates are strong fits — a moderate pool.")

        st.markdown("**🏅 Strongest candidate for each required skill**")
        must_have_skills = jd_data["must_have_skills"]
        if must_have_skills:
            best_per_skill = []
            for skill in must_have_skills:
                candidates_with_skill = [
                    r for r in results if skill in r["explanation"]["matched_must_have_skills"]
                ]
                if candidates_with_skill:
                    best = max(candidates_with_skill, key=lambda r: r["final_score"])
                    name = "Candidate (anonymized)" if anonymize else best["candidate_name"]
                    best_per_skill.append({"Skill": skill, "Best Candidate": name, "Their Score": best["final_score"]})
                else:
                    best_per_skill.append({"Skill": skill, "Best Candidate": "None found", "Their Score": "—"})
            st.dataframe(pd.DataFrame(best_per_skill), use_container_width=True, hide_index=True)
        else:
            st.write("No must-have skills detected in the JD to analyze.")

        # --- Export ---
        st.subheader("Export Results")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download as CSV", csv, "ranked_candidates.csv", "text/csv")