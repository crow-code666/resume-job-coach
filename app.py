
import streamlit as st

from src.resume_parser.parser import ResumeParser
from src.matching.skill_extractor import SkillExtractor
from src.matching.job_matcher import JobMatcher


st.set_page_config(
    page_title="Resume Job Coach",
    page_icon="📄",
    layout="wide",
)

parser = ResumeParser()
skill_extractor = SkillExtractor()
job_matcher = JobMatcher()

st.title("📄 Resume–Job Matching and Skill-Gap Coach")
st.write(
    "Understand how your resume compares with a target job, "
    "including required skills, preferred skills and important keywords."
)

st.divider()

st.header("1. Upload Your Resume")

uploaded_file = st.file_uploader(
    "Choose your resume",
    type=["pdf", "docx"],
)

st.header("2. Target Job Description")

job_description = st.text_area(
    "Paste the complete job description",
    height=250,
    placeholder="Paste the job description here...",
)

if st.button("Analyze Resume and Job", type="primary", use_container_width=True):

    if uploaded_file is None:
        st.error("Please upload your resume.")

    elif not job_description.strip():
        st.error("Please enter a job description.")

    else:
        try:
            with st.spinner("Analyzing resume and job requirements..."):
                resume_text = parser.extract_text(uploaded_file)

                resume_skills = skill_extractor.extract_skills(
                    resume_text
                )

                job_analysis = skill_extractor.analyze_job_description(
                    job_description
                )

                resume_sections = skill_extractor.extract_sections(
                    resume_text
                )

                match_results = job_matcher.compare(
                    resume_skills,
                    job_analysis["required_skills"],
                )

            st.session_state["resume_text"] = resume_text
            st.session_state["resume_skills"] = resume_skills
            st.session_state["job_analysis"] = job_analysis
            st.session_state["resume_sections"] = resume_sections
            st.session_state["match_results"] = match_results
            st.session_state["resume_filename"] = uploaded_file.name

            st.success("Analysis completed successfully!")

        except ValueError as error:
            st.error(str(error))

        except Exception as error:
            st.error("An error occurred during analysis.")
            st.exception(error)


if "match_results" in st.session_state:

    results = st.session_state["match_results"]
    analysis = st.session_state["job_analysis"]
    resume_skills = st.session_state["resume_skills"]
    sections = st.session_state["resume_sections"]

    st.divider()
    st.header("📊 Job Matching Dashboard")

    st.subheader("1. Required Skill Coverage")

    if results["coverage"] is None:
        st.warning(
            "No skills from the current skill database were detected "
            "in the required job description."
        )
    else:
        col1, col2, col3 = st.columns(3)

        col1.metric("Required Skill Coverage", f"{results['coverage']}%")
        col2.metric("Matched Skills", results["total_matched"])
        col3.metric("Missing Skills", results["total_missing"])

        st.progress(results["coverage"] / 100)

        st.caption(
            "This is the percentage of recognized required skills "
            "found in the resume. It is not a hiring probability."
        )

    st.subheader("2. Required Skills")

    if results["matched_skills"]:
        st.success("Matched: " + ", ".join(results["matched_skills"]))

    if results["missing_skills"]:
        st.warning("Missing: " + ", ".join(results["missing_skills"]))

    if not results["matched_skills"] and not results["missing_skills"]:
        st.info("No recognized required skills were found.")

    st.subheader("3. Preferred Skills")

    preferred = analysis["preferred_skills"]

    if preferred:
        for category, skills in preferred.items():
            st.write(f"**{category}:** {', '.join(skills)}")
    else:
        st.info("No preferred skills were detected.")

    st.subheader("4. Important Job Keywords")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Required keywords**")
        if analysis["required_keywords"]:
            st.write(", ".join(analysis["required_keywords"]))
        else:
            st.info("No recognized required keywords found.")

    with col2:
        st.markdown("**Preferred keywords**")
        if analysis["preferred_keywords"]:
            st.write(", ".join(analysis["preferred_keywords"]))
        else:
            st.info("No recognized preferred keywords found.")

    st.subheader("5. Qualifications and Experience")

    if analysis["qualifications"]:
        for item in analysis["qualifications"]:
            st.write(f"• {item}")
    else:
        st.info("No clear qualification or experience criteria detected.")

    if not analysis["section_headings_found"]:
        st.caption(
            "No recognizable required/preferred headings were found. "
            "Detected skills were treated as required by default."
        )

    st.divider()
    st.header("📄 Resume Information")

    st.subheader("Detected Resume Skills")

    if resume_skills:
        for category, skills in resume_skills.items():
            st.write(f"**{category}:** {', '.join(skills)}")
    else:
        st.info("No predefined skills were detected.")

    with st.expander("Education"):
        for item in sections["Education"]:
            st.write(f"• {item}")
        if not sections["Education"]:
            st.info("No clear education section detected.")

    with st.expander("Experience"):
        for item in sections["Experience"]:
            st.write(f"• {item}")
        if not sections["Experience"]:
            st.info("No clear experience section detected.")

    with st.expander("Projects"):
        for item in sections["Projects"]:
            st.write(f"• {item}")
        if not sections["Projects"]:
            st.info("No clear project section detected.")

    with st.expander("Complete Extracted Resume Text"):
        st.text_area(
            "Resume content",
            value=st.session_state["resume_text"],
            height=300,
            disabled=True,
        )

    st.download_button(
        "Download Extracted Resume Text",
        data=st.session_state["resume_text"],
        file_name="extracted_resume.txt",
        mime="text/plain",
    )
