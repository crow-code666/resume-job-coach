
import streamlit as st

from src.resume_parser.parser import ResumeParser


# -------------------- PAGE CONFIGURATION --------------------

st.set_page_config(
    page_title="Resume Job Coach",
    page_icon="📄",
    layout="wide"
)

# -------------------- INITIALIZATION --------------------

parser = ResumeParser()

# -------------------- HEADER --------------------

st.title("📄 Resume–Job Matching and Skill-Gap Coach")

st.write(
    "Upload your resume and enter a target job description. "
    "The application will extract your resume content and prepare "
    "it for job matching and skill-gap analysis."
)

st.divider()

# -------------------- RESUME UPLOAD --------------------

st.subheader("1. Upload Your Resume")

uploaded_file = st.file_uploader(
    "Choose your resume",
    type=["pdf", "docx"],
    help="Supported formats: PDF and DOCX"
)

# -------------------- JOB DESCRIPTION --------------------

st.subheader("2. Enter the Target Job Description")

job_description = st.text_area(
    "Paste the job description here",
    height=220,
    placeholder=(
        "Paste the complete job description here, including "
        "required skills, qualifications and experience..."
    )
)

st.divider()

# -------------------- PROCESSING --------------------

if st.button("Analyze Resume", type="primary", use_container_width=True):

    if uploaded_file is None:
        st.error("Please upload your resume first.")

    elif not job_description.strip():
        st.error("Please enter a job description.")

    else:
        try:
            with st.spinner("Extracting resume text..."):
                resume_text = parser.extract_text(uploaded_file)

            st.success("Resume text extracted successfully!")

            st.session_state["resume_text"] = resume_text
            st.session_state["job_description"] = job_description
            st.session_state["resume_filename"] = uploaded_file.name

        except ValueError as error:
            st.error(str(error))

        except Exception as error:
            st.error(
                "Something went wrong while processing your resume."
            )
            st.exception(error)

# -------------------- RESULTS --------------------

if "resume_text" in st.session_state:

    st.divider()
    st.subheader("3. Extracted Resume Content")

    st.caption(
        f"File: {st.session_state['resume_filename']}"
    )

    resume_text = st.session_state["resume_text"]

    word_count = len(resume_text.split())
    character_count = len(resume_text)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Words", word_count)

    with col2:
        st.metric("Total Characters", character_count)

    with st.expander("View Extracted Resume Text", expanded=True):
        st.text_area(
            "Resume content",
            value=resume_text,
            height=350,
            disabled=True
        )

    st.download_button(
        label="Download Extracted Text",
        data=resume_text,
        file_name="extracted_resume.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.info(
        "Resume extraction is complete. "
        "Skill extraction and job matching will be added in the next phase."
    )
