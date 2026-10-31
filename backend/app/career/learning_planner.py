"""Create a practical, gap-led 30-day portfolio project plan."""


class LearningPlanner:
    """Turn a short list of job gaps into six reviewable project milestones."""

    def create_plan(self, missing_skills, job_role="target role"):
        gaps = list(dict.fromkeys(
            str(skill).strip() for skill in (missing_skills or []) if str(skill).strip()
        ))[:5]
        focus = gaps or ["one skill from the target role"]
        primary = focus[0]
        role = " ".join(str(job_role or "target role").split()).strip()[:100]
        project_title, project_goal = self._project_for(primary, role)

        milestones = [
            {
                "days": "Days 1-5",
                "phase": "Understand the gap",
                "tasks": [
                    f"Write down what {primary} means in this role using one official learning resource.",
                    "Review fundamentals and note five terms you can explain in your own words.",
                    "Define a small project scope that can be completed in four more weeks.",
                ],
                "deliverable": "A one-page project brief, a short glossary, and a Git repository.",
            },
            {
                "days": "Days 6-10",
                "phase": "Build the first working version",
                "tasks": [
                    f"Build the smallest useful version of {project_title}.",
                    f"Use {primary} in a visible, testable part of the project.",
                    "Commit small changes and record any blockers you solve.",
                ],
                "deliverable": "A working first version with clear run instructions.",
            },
            {
                "days": "Days 11-15",
                "phase": "Add a second role skill",
                "tasks": [
                    f"Add {focus[1]} to the project." if len(focus) > 1 else "Add useful input validation and clear error messages.",
                    "Use realistic sample data and explain any assumptions.",
                    "Ask a peer to follow the setup instructions and note where they get stuck.",
                ],
                "deliverable": "A second working feature and a short peer-review note.",
            },
            {
                "days": "Days 16-20",
                "phase": "Test and improve quality",
                "tasks": [
                    "Add tests for normal use, missing data, and an error case.",
                    "Fix reproducible issues and remove unused code or dependencies.",
                    "Check privacy, input validation, and safe handling of credentials where relevant.",
                ],
                "deliverable": "Passing tests and a concise list of changes made from feedback.",
            },
            {
                "days": "Days 21-25",
                "phase": "Make the work easy to review",
                "tasks": [
                    "Write a README with the problem, setup, design choices, screenshots, and known limits.",
                    "Add a short demo or screenshots and link to the code.",
                    "Explain which parts you built and which libraries or examples you used.",
                ],
                "deliverable": "A public or shareable portfolio page with a reproducible demo.",
            },
            {
                "days": "Days 26-30",
                "phase": "Show evidence and practise explaining it",
                "tasks": [
                    "Update one resume bullet with the project, tools, and a verifiable outcome.",
                    "Practise a two-minute explanation of the design and one trade-off.",
                    f"Recheck the remaining focus skills: {', '.join(focus[1:]) or 'choose the next gap from your role comparison'}.",
                ],
                "deliverable": "A truthful resume bullet, project link, and short interview walkthrough.",
            },
        ]
        return {
            "title": f"30-day {role} project plan",
            "project_title": project_title,
            "project_goal": project_goal,
            "focus_skills": focus,
            "milestones": milestones,
            "score_note": "Learning or completing a course does not change the resume score. Recalculate only after adding completed project or experience evidence with a supporting link.",
        }

    @staticmethod
    def _project_for(skill, role):
        text = f"{skill} {role}".casefold()
        if any(term in text for term in ("cyber", "security", "siem", "incident", "network")):
            return (
                "Defensive security event triage lab",
                "Use sample or public training logs to document alert triage, evidence, severity, and safe remediation steps.",
            )
        if any(term in text for term in ("sql", "database", "data analyst", "analytics")):
            return (
                "Public dataset analysis",
                "Clean a public dataset, write documented queries, and explain three findings with reproducible charts or tables.",
            )
        if any(term in text for term in ("machine learning", "pandas", "data science", "tensorflow")):
            return (
                "Transparent prediction baseline",
                "Build a small model from a public dataset, compare it with a simple baseline, and explain the limits of the result.",
            )
        if any(term in text for term in ("web", "html", "css", "react", "javascript", "api", "backend")):
            return (
                "Role-focused web application",
                "Build a small accessible application with validation, tests, and a short explanation of its main design choices.",
            )
        return (
            f"{skill} portfolio project",
            f"Create a small, testable project that demonstrates {skill} in a realistic {role} task.",
        )
