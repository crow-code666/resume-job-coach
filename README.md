# CareerLens — Resume Job Coach

A Streamlit app that compares a resume with a target role, highlights detected skill gaps, and optionally generates an AI career plan, interview practice, and current job-market research.

## Run locally

Use Python 3.10 or newer.

1. Open a terminal in this project directory.
2. Create and activate a virtual environment if you use one.
3. Install dependencies:

   python -m pip install -r requirements.txt

4. For AI features, copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and add your own keys.
5. Start the app with Streamlit (do not run python app.py). On Windows you can double-click run_app.bat:

   python -m streamlit run app.py

The browser opens the app, usually at http://localhost:8501. Core resume parsing and skill matching work without API keys. The Groq key enables career plans and interview preparation. The Tavily key is only needed for live market research.

## Streamlit Community Cloud

Push this project to a GitHub repository and create a new app in Streamlit Community Cloud using app.py as the entry point. In the app settings, add these under Secrets:

    GROQ_API_KEY = "your-groq-key"
    TAVILY_API_KEY = "your-tavily-key"

Do not commit .streamlit/secrets.toml, .env, or real API keys.

## What it does

- Reads text from PDF and DOCX resumes
- Detects skills, job keywords, likely qualifications, and resume sections
- Reports matched skills, missing skills, and coverage by category
- Optionally creates a tailored career plan and interview question set with Groq
- Optionally searches current web results with Tavily and shows source links
- Downloads extracted text and generated reports

## Configuration

The app reads keys from Streamlit secrets first and environment variables second. GROQ_MODEL can override the default model (openai/gpt-oss-20b). Tavily is optional unless you use Market Pulse.

## Privacy and limitations

Resume text is held in Streamlit session state while the session is active. When you request an AI career plan or interview questions, the resume and job description are sent to Groq. Market research also sends the job description to Tavily and sends retrieved snippets to Groq. Use sample or redacted information while prototyping, and review the providers' current data terms and usage limits before using real candidate data.

Skill matching uses a finite vocabulary and may miss synonyms or skills it does not know. Coverage is a detected-skill comparison, not a hiring probability. Search snippets can be incomplete; verify findings on the original websites.

