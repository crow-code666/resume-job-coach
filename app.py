
import streamlit as st

from src.resume_parser.parser import ResumeParser
from src.matching.skill_extractor import SkillExtractor
from src.matching.job_matcher import JobMatcher


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Resume Job Coach",
    page_icon="📄",
    layout="wide",
)

parser = ResumeParser()
skill_extractor = SkillExtractor()
job_matcher = JobMatcher()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("Resume–Job Coach")

st.write(
    "Analyze your resume, research real job-market information, "
    "identify skill gaps, and prepare for your target career."
)

st.divider()


# --------------------------------------------------
# INPUTS
# --------------------------------------------------

st.header("1. Upload Your Resume")

uploaded_file = st.file_uploader(
    "Choose your resume",
    type=["pdf", "docx"],
    key="resume_upload",
)

st.header("2. Target Job Description")

job_description = st.text_area(
    "Paste the complete job description",
    height=250,
    placeholder="Paste the job description here...",
    key="job_description_input",
)


# --------------------------------------------------
# LIVE JOB MARKET RESEARCH
# --------------------------------------------------

st.divider()
st.header("3. Live Job Market Research")

st.write(
    "Search the internet for current job-market information "
    "related to the role described in your job description."
)

if st.button(
    "Research Job Market with AI",
    type="primary",
    use_container_width=True,
):

    if not job_description.strip():

        st.error("Please enter a job description first.")

    else:

        try:

            from src.ai.semantic_matcher import SemanticMatcher

            with st.spinner(
                "Searching the internet and analyzing job-market results..."
            ):

                ai = SemanticMatcher()

                research = ai.research_job_market(
                    job_description
                )

                st.session_state["market_research"] = research

            st.success("Job-market research completed.")

        except Exception as error:

            st.error("Unable to complete job-market research.")
            st.exception(error)


# --------------------------------------------------
# DISPLAY LIVE RESEARCH
# --------------------------------------------------

if "market_research" in st.session_state:

    research = st.session_state["market_research"]

    st.subheader("Job Market Research Results")

    st.metric(
        "Search Results Collected",
        len(research["sources"]),
    )

    st.markdown(
        f"**Detected Job Role:** {research['job_role']}"
    )

    st.markdown(research["report"])

    st.subheader("Research Sources")

    st.caption(
        "These links were returned by Tavily. Check the original "
        "pages to verify vacancies, dates and requirements."
    )

    for index, source in enumerate(research["sources"], start=1):

        with st.expander(
            f"{index}. {source['title']}"
        ):

            st.write(source["content"])

            if source["url"]:

                st.markdown(
                    f"[Open original source]({source['url']})"
                )

    report_text = research["report"]

    source_text = "\n\n".join(
        f"{index}. {source['title']}\n"
        f"{source['url']}\n"
        f"{source['content']}"
        for index, source in enumerate(
            research["sources"],
            start=1,
        )
    )

    st.download_button(
        "Download Job Market Research",
        data=(
            "# Job Market Research\n\n"
            + report_text
            + "\n\n# Research Sources\n\n"
            + source_text
        ),
        file_name="job_market_research.md",
        mime="text/markdown",
        use_container_width=True,
    )


# --------------------------------------------------
# RESUME AND JOB MATCHING
# --------------------------------------------------

st.divider()
st.header("4. Resume and Job Matching")

if st.button(
    "Analyze Resume and Job",
    type="primary",
    use_container_width=True,
):

    if uploaded_file is None:

        st.error("Please upload your resume.")

    elif not job_description.strip():

        st.error("Please enter a job description.")

    else:

        try:

            with st.spinner("Analyzing your resume..."):

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
            st.session_state["analyzed_job_description"] = job_description

            st.session_state.pop("ai_career_report", None)
            st.session_state.pop("ai_interview_questions", None)

            st.success("Resume analysis completed successfully.")

        except Exception as error:

            st.error("An error occurred during resume analysis.")
            st.exception(error)


# --------------------------------------------------
# DISPLAY RESUME MATCHING RESULTS
# --------------------------------------------------

if "match_results" in st.session_state:

    results = st.session_state["match_results"]
    analysis = st.session_state["job_analysis"]
    resume_skills = st.session_state["resume_skills"]
    sections = st.session_state["resume_sections"]

    st.divider()
    st.header("Resume Matching Dashboard")

    # Required skill coverage

    st.subheader("1. Required Skill Coverage")

    if results["coverage"] is None:

        st.warning(
            "No recognized required skills were detected "
            "in the job description."
        )

    else:

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Required Skill Coverage",
            f"{results['coverage']}%",
        )

        col2.metric(
            "Matched Skills",
            results["total_matched"],
        )

        col3.metric(
            "Missing Skills",
            results["total_missing"],
        )

        st.progress(results["coverage"] / 100)

        st.caption(
            "This percentage represents recognized required skills "
            "found in your resume. It is not a hiring probability."
        )

    # Required skills

    st.subheader("2. Required Skills")

    if results["matched_skills"]:

        st.success(
            "Matched: " + ", ".join(results["matched_skills"])
        )

    if results["missing_skills"]:

        st.warning(
            "Missing: " + ", ".join(results["missing_skills"])
        )

    if not results["matched_skills"] and not results["missing_skills"]:

        st.info("No recognized required skills were found.")

    # Preferred skills

    st.subheader("3. Preferred Skills")

    preferred = analysis["preferred_skills"]

    if preferred:

        for category, skills in preferred.items():

            st.write(f"**{category}:** {', '.join(skills)}")

    else:

        st.info("No preferred skills were detected.")

    # Keywords

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

    # Qualifications

    st.subheader("5. Qualifications and Experience")

    if analysis["qualifications"]:

        for item in analysis["qualifications"]:

            st.write(f"- {item}")

    else:

        st.info("No clear qualification or experience criteria detected.")

    if not analysis["section_headings_found"]:

        st.caption(
            "No recognizable required/preferred headings were found. "
            "Detected skills were treated as required by default."
        )

    # Resume information

    st.divider()
    st.header("Resume Information")

    st.subheader("6. Detected Resume Skills")

    if resume_skills:

        for category, skills in resume_skills.items():

            st.write(f"**{category}:** {', '.join(skills)}")

    else:

        st.info("No predefined skills were detected.")

    with st.expander("Education"):

        for item in sections["Education"]:
            st.write(f"- {item}")

        if not sections["Education"]:
            st.info("No clear education section detected.")

    with st.expander("Experience"):

        for item in sections["Experience"]:
            st.write(f"- {item}")

        if not sections["Experience"]:
            st.info("No clear experience section detected.")

    with st.expander("Projects"):

        for item in sections["Projects"]:
            st.write(f"- {item}")

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


    # --------------------------------------------------
    # AI CAREER REPORT
    # --------------------------------------------------

    st.divider()
    st.header("5. AI Career Preparation")

    if st.button(
        "Generate AI Career Report",
        use_container_width=True,
    ):

        try:

            from src.ai.semantic_matcher import SemanticMatcher

            with st.spinner("Groq is analyzing your resume..."):

                ai = SemanticMatcher()

                system_prompt = """
You are an expert ATS resume analyst and career coach.

Compare the resume with the supplied job description.

Never invent experience, qualifications or skills.
Distinguish missing skills from skills that are not mentioned.
Give specific, practical recommendations.
Do not guarantee employment.
"""

                user_prompt = f"""
RESUME:

{st.session_state["resume_text"]}

JOB DESCRIPTION:

{st.session_state["analyzed_job_description"]}

MATCHED SKILLS:

{results["matched_skills"]}

MISSING SKILLS:

{results["missing_skills"]}

REQUIRED SKILL COVERAGE:

{results["coverage"]}%

Prepare a detailed report:

1. Candidate profile summary
2. Overall job compatibility
3. Strongest matching skills
4. Missing and unclear skills
5. Resume improvement recommendations
6. Practical project recommendations
7. Beginner-friendly learning roadmap
8. Technical interview preparation
9. Qualification and experience assessment
10. Priority action plan

Be specific to this candidate.
"""

                report = ai.generate_response(
                    system_prompt,
                    user_prompt,
                )

                st.session_state["ai_career_report"] = report

            st.success("AI career report generated.")

        except Exception as error:

            st.error("Unable to generate the AI career report.")
            st.exception(error)

    if "ai_career_report" in st.session_state:

        st.subheader("Personalized AI Career Report")

        st.markdown(
            st.session_state["ai_career_report"]
        )

        st.download_button(
            "Download AI Career Report",
            data=st.session_state["ai_career_report"],
            file_name="ai_career_report.md",
            mime="text/markdown",
        )


    # --------------------------------------------------
    # AI INTERVIEW PREPARATION
    # --------------------------------------------------

    st.divider()
    st.header("6. AI Interview Preparation")

    if st.button(
        "Generate Interview Questions",
        use_container_width=True,
    ):

        try:

            from src.ai.semantic_matcher import SemanticMatcher

            with st.spinner("Generating interview questions..."):

                ai = SemanticMatcher()

                system_prompt = """
You are an experienced technical interviewer.

Generate realistic interview questions based on the
candidate's resume and the target job description.

Adjust difficulty to the candidate's experience.
"""

                user_prompt = f"""
JOB DESCRIPTION:

{st.session_state["analyzed_job_description"]}

RESUME:

{st.session_state["resume_text"]}

Generate:

1. 10 technical questions
2. 5 programming and practical questions
3. 5 project and experience questions
4. 5 HR and behavioral questions
5. 5 questions about missing skills

For every question explain:
- Why it may be asked.
- Important points for answering it.
"""

                questions = ai.generate_response(
                    system_prompt,
                    user_prompt,
                )

                st.session_state["ai_interview_questions"] = questions

            st.success("Interview questions generated.")

        except Exception as error:

            st.error("Unable to generate interview questions.")
            st.exception(error)

    if "ai_interview_questions" in st.session_state:

        st.subheader("Interview Preparation Questions")

        st.markdown(
            st.session_state["ai_interview_questions"]
        )

        st.download_button(
            "Download Interview Questions",
            data=st.session_state["ai_interview_questions"],
            file_name="interview_preparation.md",
            mime="text/markdown",
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Resume Job Coach | Powered by Groq AI and Tavily Search. "
    "Research results should be verified against original sources."
)
