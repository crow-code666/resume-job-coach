import os

import streamlit as st

from src.matching.job_matcher import JobMatcher
from src.matching.skill_extractor import SkillExtractor
from src.resume_parser.parser import ResumeParser


st.set_page_config(
    page_title="CareerLens | Career Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root {
  --bg:#080b17; --panel:#10172a; --panel-2:#141d35; --line:#2a3657;
  --text:#f2f4ff; --muted:#c2cbe0; --blue:#78a9ff; --purple:#b49aff;
}
html,body,[class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp {
  color:var(--text);
  background:
    radial-gradient(ellipse at 12% 3%,#172c57 0,transparent 31%),
    radial-gradient(ellipse at 92% 18%,#35205f 0,transparent 30%),
    var(--bg);
}
[data-testid="stHeader"] { background:rgba(8,11,23,.82); }
.block-container { max-width:1320px; padding-top:2rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1426,#0a1020); border-right:1px solid #293454; }
h1,h2,h3 { font-family:'Manrope',sans-serif; color:var(--text); letter-spacing:-.035em; }
h1 { font-size:2.35rem !important; }
p,label,[data-testid="stCaptionContainer"] { color:var(--muted); }
[data-testid="stWidgetLabel"] p,[data-testid="stSidebar"] label { color:#f1f3ff !important; font-weight:600; }
.hero {
  position:relative; overflow:hidden; isolation:isolate;
  border:1px solid #3c4773; border-radius:26px; padding:34px 38px; margin-bottom:24px;
  background:
    radial-gradient(circle at 83% 10%,#8b6cff42,transparent 30%),
    radial-gradient(circle at 65% 130%,#368dff40,transparent 43%),
    linear-gradient(120deg,#101a33,#171431 60%,#111b35);
  box-shadow:0 18px 55px #0008,0 0 30px #7f66ff12 inset;
  animation:rise-in .65s cubic-bezier(.2,.7,.2,1) both;
}
.hero:after {
  content:""; position:absolute; z-index:-1; width:24rem; height:24rem; right:-8rem; top:-14rem;
  border:1px solid #bdabff30; border-radius:50%; box-shadow:0 0 0 32px #bdabff09,0 0 0 64px #bdabff06;
}
.hero-kicker,.eyebrow { color:#b9a6ff; text-transform:uppercase; letter-spacing:.16em; font-size:.74rem; font-weight:800; }
.hero h1 { color:#fff !important; margin:.55rem 0 .4rem; text-shadow:0 0 28px #a892ff35; }
.hero p { color:#d0d8ee !important; margin:0; max-width:740px; font-size:1.02rem; }
.gradient-word {
  background:linear-gradient(95deg,#9dc4ff 5%,#c3aaff 54%,#f0c5ff);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.brand { font-family:'Manrope',sans-serif; font-size:1.2rem; font-weight:800; color:#f3f4ff; letter-spacing:-.04em; padding:.25rem 0 1rem; }
.brand span { color:#b9a6ff; text-shadow:0 0 18px #9e7bff80; }
.card,[data-testid="stMetric"] {
  background:linear-gradient(145deg,#121b30,#0e1527); border:1px solid #2b3858;
  border-radius:18px; box-shadow:0 10px 32px #0005;
  animation:rise-in .5s cubic-bezier(.2,.7,.2,1) both;
  transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease;
}
.card { padding:22px 24px; margin:.4rem 0 1rem; }
.card:hover,[data-testid="stMetric"]:hover { transform:translateY(-3px); border-color:#7564bc; box-shadow:0 14px 34px #0007,0 0 18px #765de21a; }
[data-testid="stMetric"] { padding:18px 20px; }
[data-testid="stMetricLabel"] p { color:#c1cbe0 !important; font-weight:600; }
[data-testid="stMetricValue"] { color:#fff !important; font-family:'Manrope',sans-serif; }
.pill { display:inline-block; border:1px solid #62519a; border-radius:999px; padding:5px 11px; margin:3px 4px 3px 0; background:#221c3f; color:#ded3ff; font-size:.84rem; font-weight:700; }
.missing { border-color:#835354; background:#321c2a; color:#ffd0c8; }
input,textarea,[data-baseweb="select"]>div { background:#0e172b !important; color:#f5f6ff !important; border-color:#354363 !important; }
input::placeholder,textarea::placeholder { color:#9eabc5 !important; }
.stButton>button,.stFormSubmitButton>button {
  border-radius:12px; min-height:2.75rem; font-weight:750 !important;
  transition:transform .18s ease,box-shadow .18s ease,filter .18s ease;
}
.stButton>button:hover,.stFormSubmitButton>button:hover { transform:translateY(-2px); filter:brightness(1.08); }
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"],button[data-testid="stBaseButton-primary"] {
  color:#fff !important; text-shadow:0 1px 2px #160e38; opacity:1 !important;
  background:linear-gradient(105deg,#425fd0,#7751bd 58%,#965ed3) !important;
  border:1px solid #a489ef !important; box-shadow:0 8px 24px #603fbd55;
}
.stButton>button:not([kind="primary"]),button[data-testid="stBaseButton-secondary"] {
  color:#f0edff !important; font-weight:700 !important; background:#19233a !important; border:1px solid #465274 !important;
}
[data-testid="stRadio"] label { color:#e9e8fa !important; font-weight:650; }
[data-testid="stExpander"] { background:#10182a; border:1px solid #303d5e; border-radius:14px; transition:border-color .2s ease; }
[data-testid="stExpander"]:hover { border-color:#806bc4; }
[data-testid="stExpander"] summary { color:#f1f1ff !important; }
[data-testid="stProgressBar"]>div>div { background:linear-gradient(90deg,#6d9dff,#b28cff); }
[data-testid="stAlert"] { background:#171d35; border-color:#51477a; color:#f0ecff; }
@keyframes rise-in { from {opacity:0; transform:translateY(12px)} to {opacity:1; transform:translateY(0)} }
@media (prefers-reduced-motion: reduce) {
  *,*:before,*:after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; }
}
</style>
""", unsafe_allow_html=True)

parser = ResumeParser()
extractor = SkillExtractor()
matcher = JobMatcher()


def generate_ai(system_prompt, user_prompt):
    from src.ai.semantic_matcher import SemanticMatcher
    return SemanticMatcher().generate_response(system_prompt, user_prompt)


def key_is_configured(name):
    try:
        return bool(st.secrets.get(name) or os.getenv(name))
    except Exception:
        return bool(os.getenv(name))


def show_pills(items, missing=False):
    if not items:
        st.caption("Nothing detected yet.")
        return
    css = "pill missing" if missing else "pill"
    safe = [str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for x in items]
    st.markdown(" ".join(f'<span class="{css}">{x}</span>' for x in safe), unsafe_allow_html=True)


def show_sources(sources):
    for i, source in enumerate(sources, 1):
        with st.expander(f"{i:02d} · {source.get('title') or 'Untitled result'}"):
            st.write(source.get("content", "No preview available."))
            if source.get("url"):
                st.markdown(f"[Open original source]({source['url']})")


with st.sidebar:
    st.markdown('<div class="brand">◈ Career<span>Lens</span></div>', unsafe_allow_html=True)
    st.markdown("### PROFILE INPUT")
    st.caption("Add a resume and target role to get a personalized plan.")
    with st.form("profile_form", clear_on_submit=False):
        uploaded_file = st.file_uploader("Resume file", type=["pdf", "docx"], help="PDF and Word documents are supported.")
        job_description = st.text_area("Target job description", height=200, placeholder="Paste the role description, requirements, and qualifications…")
        research_online = st.checkbox(
            "Find relevant skills online",
            value=True,
            help="Search current job postings and company career pages related to this JD. Uses Groq and Tavily.",
        )
        analyze_clicked = st.form_submit_button("✦  Analyze my fit", type="primary", width="stretch")
    with st.expander("AI setup"):
        st.write("Career plan and interview generation need Groq. Live Market pulse also needs Tavily.")
        st.write(f"Groq key: {'✅ configured' if key_is_configured('GROQ_API_KEY') else '⚠️ missing'}")
        st.write(f"Tavily key: {'✅ configured' if key_is_configured('TAVILY_API_KEY') else 'Optional — needed for Market pulse'}")
        st.markdown("[Create a Groq API key](https://console.groq.com/keys)")
        st.markdown("**Run locally in VS Code** — create .streamlit/secrets.toml and add:")
        st.code('GROQ_API_KEY = "paste-your-key-here"\nTAVILY_API_KEY = "paste-your-tavily-key-here"', language="toml")
        st.markdown("**Run on Streamlit Cloud** — open your app’s Settings → Secrets, paste the same lines, and save. Restart or reboot the app after adding the key.")
        st.caption("Tavily is optional unless you use Market pulse. Keep secrets private and never commit secrets.toml.")
    st.caption("Your resume is processed for this session. AI features send selected text to the configured provider.")

if analyze_clicked:
    if not job_description.strip():
        st.session_state["notice_error"] = "Paste a target job description to continue."
    else:
        # Every new JD submission starts a fresh research result set.
        for key in (
            "market_research",
            "ai_career_report",
            "ai_interview_questions",
            "online_skill_research",
            "online_skill_research_error",
            "online_skill_research_skipped",
        ):
            st.session_state.pop(key, None)

        st.session_state["analyzed_job_description"] = job_description

        # Resume comparison is optional. JD research can run on its own.
        if uploaded_file is not None:
            try:
                with st.spinner("Reading your resume and mapping role requirements…"):
                    resume_text = parser.extract_text(uploaded_file)
                    resume_skills = extractor.extract_skills(resume_text)
                    job_analysis = extractor.analyze_job_description(job_description)
                    sections = extractor.extract_sections(resume_text)
                    results = matcher.compare(
                        resume_skills,
                        job_analysis["required_skills"],
                    )

                st.session_state.update(
                    resume_text=resume_text,
                    resume_skills=resume_skills,
                    job_analysis=job_analysis,
                    resume_sections=sections,
                    match_results=results,
                    resume_filename=uploaded_file.name,
                )
            except Exception as error:
                st.session_state["notice_error"] = (
                    "The JD was saved, but the resume could not be analyzed: "
                    + str(error)
                )
                for key in (
                    "resume_text",
                    "resume_skills",
                    "job_analysis",
                    "resume_sections",
                    "match_results",
                    "resume_filename",
                ):
                    st.session_state.pop(key, None)
        else:
            for key in (
                "resume_text",
                "resume_skills",
                "job_analysis",
                "resume_sections",
                "match_results",
                "resume_filename",
            ):
                st.session_state.pop(key, None)

        # Run online skills research even when the user has not uploaded a resume.
        if research_online:
            try:
                from src.ai.semantic_matcher import SemanticMatcher

                with st.spinner(
                    "Searching current job postings and company career pages "
                    "for skills related to this JD…"
                ):
                    online_results = SemanticMatcher().research_job_skills(
                        job_description
                    )

                st.session_state["online_skill_research"] = online_results
            except Exception as error:
                st.session_state["online_skill_research_error"] = str(error)
        else:
            st.session_state["online_skill_research_skipped"] = True

        if "online_skill_research" in st.session_state:
            if "match_results" in st.session_state:
                st.session_state["notice_success"] = (
                    "Resume comparison and online JD skill research are ready."
                )
            else:
                st.session_state["notice_success"] = (
                    "Online JD skill research is ready. Upload a resume later "
                    "to compare your skills."
                )
        elif research_online:
            st.session_state["notice_error"] = (
                "Online research could not be completed. "
                + st.session_state.get(
                    "online_skill_research_error",
                    "Check your Groq and Tavily setup.",
                )
            )
        elif "match_results" in st.session_state:
            st.session_state["notice_success"] = (
                "Resume fit analysis is ready. Online research was turned off."
            )
        else:
            st.session_state["notice_success"] = (
                "JD saved. Turn on online research or upload a resume to continue."
            )

st.markdown("""
<div class="hero">
  <div class="hero-kicker">Career intelligence · built around you</div>
  <h1>Navigate your <span class="gradient-word">next move.</span></h1>
  <p>Map your experience to the role, reveal the gaps that matter, and turn your next step into a clear plan.</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.get("notice_error"):
    st.error(st.session_state.pop("notice_error"))
if st.session_state.get("notice_success"):
    st.success(st.session_state.pop("notice_success"))

page = st.segmented_control("Workspace section", ["Overview", "Market pulse", "Career plan", "Interview lab"], default="Overview", label_visibility="collapsed", key="workspace_page", width="stretch")

has_profile_or_research = (
    "match_results" in st.session_state
    or "online_skill_research" in st.session_state
    or "online_skill_research_error" in st.session_state
)

if not has_profile_or_research:
    st.markdown("### Start with your job description")
    one, two = st.columns(2)
    with one:
        st.markdown('<div class="card"><div class="eyebrow">Option 1</div><h3>Research a company JD</h3><p>Paste a job description in the left panel and run online skill research. A resume is not required.</p></div>', unsafe_allow_html=True)
    with two:
        st.markdown('<div class="card"><div class="eyebrow">Option 2</div><h3>Compare your resume</h3><p>Upload a PDF or DOCX as well to compare your detected skills with the role requirements.</p></div>', unsafe_allow_html=True)
    st.info("Add a JD in the left panel and select **Analyze my fit**. Online research is enabled by default.")
else:
    results = st.session_state.get("match_results")
    analysis = st.session_state.get("job_analysis")
    resume_skills = st.session_state.get("resume_skills", {})
    sections = st.session_state.get("resume_sections", {})
    if results:
        st.markdown(
            f'<div class="eyebrow">CURRENT PROFILE · '
            f'{st.session_state.get("resume_filename", "Resume")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="eyebrow">JOB DESCRIPTION RESEARCH · NO RESUME REQUIRED</div>',
            unsafe_allow_html=True,
        )

    if page == "Overview":
        if results:
            st.subheader("Your fit snapshot")
            c1, c2, c3 = st.columns(3)
            coverage = results["coverage"]
            c1.metric("Required skill coverage", f"{coverage:.0f}%" if coverage is not None else "—")
            c2.metric("Skills matched", results["total_matched"])
            c3.metric("Skills to build", results["total_missing"])
            if coverage is not None:
                st.progress(coverage / 100)
            st.caption("Coverage reflects detected skills only. It is not a hiring probability or a complete assessment of experience.")
        else:
            st.subheader("Job description research")
            st.caption("This research is based on the supplied JD and current online sources. Upload a resume whenever you want a personal skill-gap comparison.")

        st.markdown("### Skills researched online for this job description")
        online = st.session_state.get("online_skill_research")

        if online:
            st.caption(
                f"Detected role: {online.get('job_role', 'Target role')} · "
                f"{len(online.get('sources', []))} web results reviewed"
            )
            online_left, online_right = st.columns(2)
            with online_left:
                st.markdown("**Skills stated in the company JD**")
                show_pills(online.get("jd_required_skills", []))
                if online.get("jd_preferred_skills"):
                    st.markdown("**Preferred in the company JD**")
                    show_pills(online.get("jd_preferred_skills", []))
            with online_right:
                st.markdown("**Skills found in current job-market sources**")
                show_pills(online.get("market_required_skills", []))
                if online.get("market_preferred_skills"):
                    st.markdown("**Commonly preferred in those sources**")
                    show_pills(online.get("market_preferred_skills", []))

            st.markdown("**Overlap between this JD and the online market**")
            show_pills(online.get("shared_skills", []))
            if online.get("additional_market_skills"):
                st.markdown("**Additional skills worth considering**")
                show_pills(online.get("additional_market_skills", []))

            if online.get("market_tools_and_platforms"):
                st.markdown("**Tools and platforms found online**")
                show_pills(online.get("market_tools_and_platforms", []))

            for insight in online.get("market_insights", []):
                st.write(f"• {insight}")
            if online.get("research_limitations"):
                st.caption(online["research_limitations"])

            with st.expander("View online research sources"):
                show_sources(online.get("sources", []))
        elif st.session_state.get("online_skill_research_error"):
            st.warning(
                "Online skill research did not complete: "
                + st.session_state["online_skill_research_error"]
            )
            st.caption(
                "The resume comparison below is still based on the local skill vocabulary. "
                "Check the Groq and Tavily setup, then analyze the JD again."
            )
        elif st.session_state.get("online_skill_research_skipped"):
            st.info("Online skill research was turned off for this analysis.")
        else:
            st.info(
                "Online skill research has not run yet. Keep “Find relevant skills online” "
                "selected in the sidebar and choose “Analyze my fit”."
            )

        if results:
            left, right = st.columns([1.05, 1])
            with left:
                st.markdown("### Strong matches")
                show_pills(results["matched_skills"])
                st.markdown("### Priority gaps")
                show_pills(results["missing_skills"], missing=True)
            with right:
                st.markdown("### Preferred skills")
                if analysis["preferred_skills"]:
                    for category, skills in analysis["preferred_skills"].items():
                        st.write(f"**{category}** · {', '.join(skills)}")
                else:
                    st.caption("No separate preferred skills were identified.")
                if analysis["qualifications"]:
                    st.markdown("### Qualifications mentioned")
                    for item in analysis["qualifications"]:
                        st.write(f"• {item}")
            st.markdown("### Skill map")
            if results["category_results"]:
                for category, details in results["category_results"].items():
                    with st.expander(f"{category} · {len(details['matched'])}/{details['required_count']} matched"):
                        if details["matched"]:
                            st.write("Matched: " + ", ".join(details["matched"]))
                        if details["missing"]:
                            st.write("To build: " + ", ".join(details["missing"]))
            else:
                st.info("No recognized skills found in the job description. Add specific technologies or competencies for a more useful comparison.")
            with st.expander("Resume details"):
                st.markdown("**Detected skills**")
                for category, skills in resume_skills.items():
                    st.write(f"{category}: {', '.join(skills)}")
                for title in ("Education", "Experience", "Projects"):
                    st.markdown(f"**{title}**")
                    values = sections.get(title, [])
                    st.write("\n".join(f"• {item}" for item in values) if values else "No clear section detected.")
                st.download_button("Download extracted resume text", data=st.session_state["resume_text"], file_name="extracted_resume.txt", mime="text/plain")
        else:
            st.info("Resume comparison is not active. Upload a PDF or DOCX in the sidebar and run Analyze my fit to see matched and missing skills.")

    elif page == "Market pulse":
        st.subheader("Market pulse")
        st.write("Search current web results related to your target role, then summarize recurring skills and trends.")
        if not st.session_state.get("analyzed_job_description"):
            st.info("Paste a job description in the sidebar first.")
        elif st.button("Search the job market", type="primary", key="research_market"):
            try:
                from src.ai.semantic_matcher import SemanticMatcher
                with st.spinner("Searching sources and preparing your market summary…"):
                    st.session_state["market_research"] = SemanticMatcher().research_job_market(st.session_state["analyzed_job_description"])
            except (ValueError, RuntimeError) as error:
                st.error(str(error))
            except Exception:
                st.error("Market research couldn’t run. Check the configured AI and search keys, then try again.")
        research = st.session_state.get("market_research")
        if research:
            st.markdown(f"**Likely target role:** {research['job_role']}")
            st.markdown(research["report"])
            st.download_button("Download market report", data=research["report"], file_name="market_report.md", mime="text/markdown")
            st.markdown("### Sources to review")
            st.caption("Search snippets can be incomplete. Open source pages to verify dates, vacancies, and requirements.")
            show_sources(research["sources"])

    elif page == "Career plan":
        st.subheader("Career plan")
        st.write("Get tailored recommendations based on your resume, role description, and detected skill gaps.")
        if not results:
            st.info("Upload and analyze a resume to create a personalized career plan.")
        elif st.button("Create my career plan", type="primary", key="generate_career_plan"):
            system = "You are an expert ATS resume analyst and career coach. Never invent experience, qualifications, or skills. Distinguish missing skills from skills that are merely not mentioned. Give practical recommendations and do not guarantee employment."
            prompt = f"""RESUME:\n{st.session_state['resume_text']}\n\nJOB DESCRIPTION:\n{st.session_state['analyzed_job_description']}\n\nMATCHED SKILLS:\n{results['matched_skills']}\n\nMISSING SKILLS:\n{results['missing_skills']}\n\nCOVERAGE:\n{results['coverage']}%\n\nPrepare a specific career report covering candidate summary, fit, strengths, gaps, resume improvements, projects, learning roadmap, interview preparation, qualifications, and a priority action plan."""
            try:
                with st.spinner("Building your personalized career plan…"):
                    st.session_state["ai_career_report"] = generate_ai(system, prompt)
            except (ValueError, RuntimeError) as error:
                st.error(str(error))
            except Exception:
                st.error("The career plan couldn’t be generated. Check the Groq key and try again.")
        report = st.session_state.get("ai_career_report")
        if report:
            st.markdown(report)
            st.download_button("Download career plan", data=report, file_name="career_plan.md", mime="text/markdown")

    else:
        st.subheader("Interview lab")
        st.write("Practice technical, practical, project, and behavioral questions tailored to the role.")
        if not results:
            st.info("Upload and analyze a resume to generate personalized interview practice.")
        elif st.button("Generate interview practice set", type="primary", key="generate_interview"):
            system = "You are an experienced technical interviewer. Create realistic questions from the candidate's resume and target job description. Adjust difficulty to experience and do not assume skills not shown."
            prompt = f"""JOB DESCRIPTION:\n{st.session_state['analyzed_job_description']}\n\nRESUME:\n{st.session_state['resume_text']}\n\nGenerate 10 technical, 5 practical/programming, 5 project/experience, 5 behavioral, and 5 missing-skill questions. For every question explain why it may be asked and key points for answering."""
            try:
                with st.spinner("Preparing your interview practice set…"):
                    st.session_state["ai_interview_questions"] = generate_ai(system, prompt)
            except (ValueError, RuntimeError) as error:
                st.error(str(error))
            except Exception:
                st.error("Interview prep couldn’t be generated. Check the Groq key and try again.")
        questions = st.session_state.get("ai_interview_questions")
        if questions:
            st.markdown(questions)
            st.download_button("Download interview practice", data=questions, file_name="interview_practice.md", mime="text/markdown")

st.divider()
st.caption("CareerLens · A practical coaching aid. Verify market findings at the original source and treat AI suggestions as guidance, not guarantees.")


