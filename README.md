# CareerLens web platform

React + TypeScript frontend and a Python API, built as a modular monolith so a small team can own and explain the whole system.

## Current setup

- The project root contains the Vite entry files; React screens and styles live in `src/`.
- `backend/` is the FastAPI service. MySQL is accessed only by this service.
- Keep credentials in untracked local environment files or the deployment secret manager. Never commit real keys.

## Team boundaries

- Frontend owner: screens, accessible forms, upload states, and API client.
- Backend/security owner: authentication, authorization, upload validation, database, provider integrations, deployment, and security review.
- Both owners review API contract changes and pull requests.

## Authentication decisions

Use a persistent, revocable server-side session in an HttpOnly, Secure, SameSite cookie for the browser app. Require CSRF protection on state-changing cookie-authenticated routes. A guest may browse; clicking resume upload redirects to login and returns to upload afterward. Every resume and analysis must be checked against the authenticated user's ID.

The current milestone includes signup/login/logout, persistent sessions, private resume upload, and an owner-checked local resume-to-role analysis. Add resume deletion and automated ownership tests before public deployment.

## Frontend (React + TypeScript)

```powershell
npm install
npm run dev
```

## Backend and local analysis

The React workspace includes registration, login, persistent sessions, private PDF/DOCX uploads and original-file download, target-job-only resume analysis, recognized skill gaps, a six-milestone 30-day project plan, and a curated no-cost course catalog. Matching uses built-in role profiles for common jobs; unfamiliar titles use a clearly labeled general transferable-skills baseline. Scores are profile estimates, not a hiring probability or a substitute for checking a specific employer posting. Candidate-submitted project or work evidence can be compared with a stored baseline; the application labels that evidence as self-reported and does not verify it. Courses are not automatically counted as project or work evidence.

The workspace also includes public job search and Market Pulse, a private application tracker, international profile preferences, an offline career coach with optional Groq responses, and a five-question adaptive interview practice flow. Find Jobs uses public feeds where available and offers prefilled live Google, Indeed, and LinkedIn searches; GitHub project searches and role-specific roadmap.sh learning paths are shown separately. External searches open only when the user clicks them. Market Pulse uses Tavily when configured and otherwise summarizes connected public listing samples where available, with live search links as a fallback. Public listings are incomplete samples and must be checked at their source. The coach sends only the question and selected role/skill context to Groq after the user opts in; it does not send the stored resume. If AI is not selected or configured, it returns local rule-based suggestions. Interview answers remain in the private account and are sent to Groq only when the user opts into AI scoring for that answer. Without that opt-in, the app gives structure-only feedback and does not claim to verify technical correctness.

Access JWTs and rotating refresh tokens are HttpOnly cookies; refresh tokens are stored only as hashes. Mutating authenticated routes check a CSRF token and request origin. Passwords use Argon2. Uploaded files are size/type checked and stored under `backend/var`, outside the public frontend; the database stores file metadata and owner ID. Provider keys stay on the backend in `backend/.env`.

To configure MySQL, copy `backend/.env.example` to `backend/.env`, replace the database password and signing key, and create the database/user using `backend/create_database.sql`. Set `GROQ_API_KEY` for optional AI coach responses and AI interview scoring. `TAVILY_API_KEY` is optional and enables broader web research in Market Pulse; Find Jobs and its external search links work without it. The local coach also works with no provider keys. Do not commit `backend/.env`. With `APP_ENV=development`, the API creates tables at startup after it connects to the database. Before production deployment, apply the additive schema in `backend/migrations/20261031_career_tools.sql` and use `APP_ENV=production` (which also enables Secure cookies). The SQL adds tool tables and leaves existing user and resume tables intact.

The local API binds to `127.0.0.1:8001`; the Vite dev server proxies `/api` to it. Double-click `run_app.bat` to start the API and frontend in separate visible windows. Or run the backend from the project root with `backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir backend\app --app-dir backend --host 127.0.0.1 --port 8001`, then run `npm.cmd run dev -- --host 127.0.0.1 --port 5173` in a second terminal. The reload watcher is limited to `backend/app`, so dependency installs do not restart the API. Settings load from `backend/.env` relative to the config file, regardless of the terminal's current directory. Restart Uvicorn after editing `.env`. API docs: `http://127.0.0.1:8001/api/docs`. Database health: `http://127.0.0.1:8001/api/v1/health/database` (`503` means configuration or MySQL is unavailable).

Before public use, add rate limiting, email verification/password reset, security logging, reviewed database migrations, backup/deletion handling, and HTTPS deployment. The current database schema auto-creation is development-only.

## Existing project

The prior Streamlit project remains separate at `../resume-job-coach-secure` and is not required at runtime. It remains a reference for the parser, matcher, course catalog, and research workflow.
