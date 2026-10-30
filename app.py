
import streamlit as st

from src.resume_parser.parser import ResumeParser
from src.matching.skill_extractor import SkillExtractor


# -------------------- PAGE CONFIGURATION --------------------

st.set_page_config(
    page_title="Resume Job Coach",
    page_icon="📄",
    layout="wide"
)

# -------------------- INITIALIZATION --------------------

parser = ResumeParser()
skill_extractor = SkillExtractor()

# -------------------- HEADER --------------------

st.title("📄 Resume–Job Matching and Skill-Gap Coach")

st.write(
    "Upload your resume and enter a target job description. "
    "Analyze your skills and prepare for intelligent job matching."
)

st.divider()

# -------------------- RESUME UPLOAD --------------------

st.subheader("1. Upload Your Resume")

uploaded_file = st.file_uploader(
    "Choose your resume",
    type=["pdf", "docx"]
)

# -------------------- JOB DESCRIPTION --------------------

st.subheader("2. Target Job Description")

job_description = st.text_area(
    "Paste the job description",
    height=220,
    placeholder="Paste the job description here..."
)

# -------------------- ANALYSIS --------------------

if st.button("Analyze Resume", type="primary", use_container_width=True):

    if uploaded_file is None:
        st.error("Please upload your resume.")

    elif not job_description.strip():
        st.error("Please enter a job description.")

    else:
        try:
            with st.spinner("Analyzing your resume..."):
                resume_text = parser.extract_text(uploaded_file)

                extracted_skills = skill_extractor.extract_skills(
                    resume_text
                )

                extracted_sections = skill_extractor.extract_sections(
                    resume_text
                )

            st.session_state["resume_text"] = resume_text
            st.session_state["job_description"] = job_description
            st.session_state["resume_filename"] = uploaded_file.name
            st.session_state["extracted_skills"] = extracted_skills
            st.session_state["extracted_sections"] = extracted_sections

            st.success("Resume analysis completed!")

        except ValueError as error:
            st.error(str(error))

        except Exception as error:
            st.error("An error occurred during resume analysis.")
            st.exception(error)

# -------------------- DISPLAY RESULTS --------------------

if "resume_text" in st.session_state:

    st.divider()
    st.header("📊 Resume Analysis Dashboard")

    resume_text = st.session_state["resume_text"]
    extracted_skills = st.session_state["extracted_skills"]
    extracted_sections = st.session_state["extracted_sections"]

    # Resume statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Words", len(resume_text.split()))

    with col2:
        total_skills = sum(
            len(skills) for skills in extracted_skills.values()
        )
        st.metric("Skills Identified", total_skills)

    with col3:
        st.metric(
            "Skill Categories",
            len(extracted_skills)
        )

    # Skills
    st.subheader("1. Identified Skills")

    if extracted_skills:
        for category, skills in extracted_skills.items():
            with st.expander(
                f"{category} ({len(skills)})",
                expanded=True
            ):
                st.write(" • ".join(skills))
    else:
        st.warning(
            "No skills from the current skill database were detected. "
            "You can still review the extracted resume text below."
        )

    # Education
    st.subheader("2. Education")

    education = extracted_sections["Education"]

    if education:
        for item in education:
            st.write(f"• {item}")
    else:
        st.info("No clear education section was detected.")

    # Experience
    st.subheader("3. Work Experience")

    experience = extracted_sections["Experience"]

    if experience:
        for item in experience:
            st.write(f"• {item}")
    else:
        st.info("No clear experience section was detected.")

    # Projects
    st.subheader("4. Projects")

    projects = extracted_sections["Projects"]

    if projects:
        for item in projects:
            st.write(f"• {item}")
    else:
        st.info("No clear project section was detected.")

    # Original resume text
    with st.expander("View Complete Extracted Resume Text"):
        st.text_area(
            "Extracted content",
            value=resume_text,
            height=350,
            disabled=True
        )

    st.download_button(
        "Download Extracted Resume Text",
        data=resume_text,
        file_name="extracted_resume.txt",
        mime="text/plain"
    )

    st.info(
        "This version uses a predefined skill database and basic "
        "section detection. Semantic AI recognition and job matching "
        "will be added in upcoming phases."
    )
