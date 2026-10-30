
import streamlit as st

from src.resume_parser.parser import ResumeParser
from src.matching.skill_extractor import SkillExtractor
from src.matching.job_matcher import JobMatcher


# -------------------- PAGE CONFIGURATION --------------------

st.set_page_config(
    page_title="Resume Job Coach",
    page_icon="📄",
    layout="wide"
)

# -------------------- INITIALIZATION --------------------

parser = ResumeParser()
skill_extractor = SkillExtractor()
job_matcher = JobMatcher()


# -------------------- HEADER --------------------

st.title("📄 Resume–Job Matching and Skill-Gap Coach")

st.write(
    "Upload your resume, enter a target job description, "
    "and discover how your skills match the job requirements."
)

st.divider()


# -------------------- INPUTS --------------------

st.header("1. Upload Your Resume")

uploaded_file = st.file_uploader(
    "Choose your resume",
    type=["pdf", "docx"]
)

st.header("2. Enter the Job Description")

job_description = st.text_area(
    "Paste the complete job description",
    height=220,
    placeholder="Paste the job description here..."
)


# -------------------- ANALYSIS BUTTON --------------------

if st.button(
    "Analyze Resume and Match Job",
    type="primary",
    use_container_width=True
):

    if uploaded_file is None:
        st.error("Please upload your resume.")

    elif not job_description.strip():
        st.error("Please enter a job description.")

    else:
        try:
            with st.spinner("Analyzing resume and job requirements..."):

                # Extract resume text
                resume_text = parser.extract_text(uploaded_file)

                # Extract skills from resume
                resume_skills = skill_extractor.extract_skills(
                    resume_text
                )

                # Extract skills from job description
                job_skills = skill_extractor.extract_skills(
                    job_description
                )

                # Extract resume sections
                resume_sections = skill_extractor.extract_sections(
                    resume_text
                )

                # Compare resume and job skills
                match_results = job_matcher.compare(
                    resume_skills,
                    job_skills
                )

            # Save results
            st.session_state["resume_text"] = resume_text
            st.session_state["resume_skills"] = resume_skills
            st.session_state["job_skills"] = job_skills
            st.session_state["resume_sections"] = resume_sections
            st.session_state["match_results"] = match_results
            st.session_state["job_description"] = job_description
            st.session_state["resume_filename"] = uploaded_file.name

            st.success("Resume and job analysis completed!")

        except ValueError as error:
            st.error(str(error))

        except Exception as error:
            st.error("An error occurred during analysis.")
            st.exception(error)


# -------------------- RESULTS DASHBOARD --------------------

if "match_results" in st.session_state:

    results = st.session_state["match_results"]
    resume_skills = st.session_state["resume_skills"]
    job_skills = st.session_state["job_skills"]
    resume_sections = st.session_state["resume_sections"]

    st.divider()
    st.header("📊 Job Matching Dashboard")

    # Check if job description contains recognized skills
    if results["coverage"] is None:

        st.warning(
            "No skills from our current skill database were detected "
            "in the job description. Try a description containing "
            "specific technologies or skills."
        )

    else:

        # -------------------- MATCH SCORE --------------------

        st.subheader("1. Skill Coverage")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Skill Coverage",
                f"{results['coverage']}%"
            )

        with col2:
            st.metric(
                "Matched Skills",
                results["total_matched"]
            )

        with col3:
            st.metric(
                "Missing Skills",
                results["total_missing"]
            )

        st.progress(results["coverage"] / 100)

        st.caption(
            "Skill coverage = detected job skills found in the resume "
            "divided by all detected job skills. This is not an overall "
            "measure of employability or hiring probability."
        )

        # -------------------- MATCHED SKILLS --------------------

        st.subheader("2. Matched Skills")

        if results["matched_skills"]:
            st.success(
                "Skills found in both the resume and job description:"
            )
            st.write(" • ".join(results["matched_skills"]))
        else:
            st.info("No matching skills were detected.")

        # -------------------- MISSING SKILLS --------------------

        st.subheader("3. Missing Skills")

        if results["missing_skills"]:
            st.warning(
                "These job requirements were not detected in the resume:"
            )
            st.write(" • ".join(results["missing_skills"]))
        else:
            st.success(
                "All detected job skills were found in the resume."
            )

        # -------------------- ADDITIONAL SKILLS --------------------

        st.subheader("4. Additional Resume Skills")

        if results["additional_skills"]:
            st.write(
                "These skills were detected in your resume but not "
                "in the job description:"
            )
            st.write(" • ".join(results["additional_skills"]))
        else:
            st.info("No additional skills were detected.")

        # -------------------- CATEGORY ANALYSIS --------------------

        st.subheader("5. Category-wise Matching")

        for category, details in results["category_results"].items():

            with st.expander(category, expanded=True):

                st.write(
                    f"Required skills: {details['required_count']}"
                )

                if details["matched"]:
                    st.success(
                        "Matched: " + ", ".join(details["matched"])
                    )

                if details["missing"]:
                    st.warning(
                        "Missing: " + ", ".join(details["missing"])
                    )

        # -------------------- RESUME DETAILS --------------------

    st.divider()
    st.header("📄 Resume Details")

    with st.expander("Identified Resume Skills"):
        for category, skills in resume_skills.items():
            st.write(f"**{category}:** {', '.join(skills)}")

    with st.expander("Education"):
        education = resume_sections["Education"]

        if education:
            for item in education:
                st.write(f"• {item}")
        else:
            st.info("No clear education section detected.")

    with st.expander("Experience"):
        experience = resume_sections["Experience"]

        if experience:
            for item in experience:
                st.write(f"• {item}")
        else:
            st.info("No clear experience section detected.")

    with st.expander("Projects"):
        projects = resume_sections["Projects"]

        if projects:
            for item in projects:
                st.write(f"• {item}")
        else:
            st.info("No clear project section detected.")

    with st.expander("Complete Extracted Resume Text"):
        st.text_area(
            "Resume content",
            value=st.session_state["resume_text"],
            height=300,
            disabled=True
        )

    st.download_button(
        "Download Extracted Resume Text",
        data=st.session_state["resume_text"],
        file_name="extracted_resume.txt",
        mime="text/plain"
    )
