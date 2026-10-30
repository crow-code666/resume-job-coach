
import re


class SkillExtractor:
    """Extract skills and analyze job-description requirements."""

    SKILL_DATABASE = {
        "Programming Languages": {
            "Python": ["python"],
            "Java": ["java"],
            "C": ["c programming", "programming in c"],
            "C++": ["c++"],
            "C#": ["c#"],
            "JavaScript": ["javascript"],
            "TypeScript": ["typescript"],
            "PHP": ["php"],
            "R": ["r programming"],
        },
        "Web Development": {
            "HTML": ["html", "html5"],
            "CSS": ["css", "css3"],
            "React": ["react", "react.js", "reactjs"],
            "Angular": ["angular"],
            "Node.js": ["node.js", "nodejs"],
            "Express.js": ["express.js", "expressjs"],
            "Bootstrap": ["bootstrap"],
            "Tailwind CSS": ["tailwind css"],
        },
        "Databases": {
            "SQL": ["sql", "structured query language"],
            "MySQL": ["mysql"],
            "PostgreSQL": ["postgresql", "postgres"],
            "MongoDB": ["mongodb"],
            "SQLite": ["sqlite"],
            "Oracle Database": ["oracle database"],
        },
        "Frameworks and Libraries": {
            "Flask": ["flask"],
            "Django": ["django"],
            "FastAPI": ["fastapi"],
            "NumPy": ["numpy"],
            "Pandas": ["pandas"],
            "Matplotlib": ["matplotlib"],
            "TensorFlow": ["tensorflow"],
            "PyTorch": ["pytorch"],
            "Scikit-learn": ["scikit-learn", "sklearn"],
        },
        "Tools and Platforms": {
            "Git": ["git"],
            "GitHub": ["github"],
            "Docker": ["docker"],
            "Kubernetes": ["kubernetes"],
            "Linux": ["linux"],
            "Windows": ["windows"],
            "VS Code": ["vs code", "visual studio code"],
            "AWS": ["aws", "amazon web services"],
            "Microsoft Azure": ["microsoft azure", "azure"],
            "Google Cloud": ["google cloud", "gcp"],
        },
        "Soft Skills": {
            "Communication": ["communication", "communication skills"],
            "Teamwork": ["teamwork", "team work", "collaboration"],
            "Leadership": ["leadership", "team leadership"],
            "Problem Solving": ["problem solving", "problem-solving"],
            "Time Management": ["time management"],
            "Critical Thinking": ["critical thinking"],
            "Adaptability": ["adaptability", "adaptable"],
            "Creativity": ["creativity", "creative thinking"],
        },
    }

    JOB_KEYWORDS = {
        "REST APIs": ["rest api", "restful api", "rest apis"],
        "API Development": ["api development", "developing apis"],
        "Database Management": ["database management", "database design"],
        "Data Structures": ["data structures"],
        "Algorithms": ["algorithms", "algorithm design"],
        "Object-Oriented Programming": [
            "object oriented programming",
            "object-oriented programming",
            "oops",
        ],
        "Software Development": ["software development"],
        "Software Testing": ["software testing", "unit testing"],
        "Debugging": ["debugging", "debug code"],
        "Version Control": ["version control"],
        "Agile Methodology": ["agile", "scrum"],
        "Cloud Computing": ["cloud computing"],
        "Machine Learning": ["machine learning"],
        "Data Analysis": ["data analysis", "data analytics"],
        "Problem Solving": ["problem solving", "problem-solving"],
        "Communication": ["communication skills", "communication"],
        "Team Collaboration": ["team collaboration", "work in a team"],
        "CI/CD": ["ci/cd", "continuous integration", "continuous deployment"],
        "Deployment": ["deployment", "deploy applications"],
        "SDLC": ["software development life cycle", "sdlc"],
    }

    SECTION_HEADINGS = {
        "education": [
            "education",
            "academic background",
            "educational qualifications",
            "qualification",
        ],
        "experience": [
            "work experience",
            "professional experience",
            "employment history",
            "experience",
            "internship",
        ],
        "projects": [
            "projects",
            "personal projects",
            "academic projects",
            "project experience",
        ],
    }

    PREFERRED_HEADINGS = (
        "preferred qualifications",
        "preferred skills",
        "preferred requirements",
        "good to have",
        "nice to have",
        "bonus skills",
        "desired skills",
        "additional skills",
    )

    REQUIRED_HEADINGS = (
        "required qualifications",
        "required skills",
        "requirements",
        "minimum qualifications",
        "must have",
        "mandatory skills",
        "what you need",
    )

    @staticmethod
    def _contains_term(text: str, term: str) -> bool:
        """Check for a term without matching it inside unrelated words."""
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(term.lower())
            + r"(?![a-z0-9])"
        )
        return bool(re.search(pattern, text.lower()))

    def _find_terms(self, text: str, database: dict) -> dict:
        """Find known terms and return them grouped by category."""
        results = {}

        for category, items in database.items():
            found = []

            for display_name, aliases in items.items():
                if any(self._contains_term(text, alias) for alias in aliases):
                    found.append(display_name)

            if found:
                results[category] = sorted(set(found))

        return results

    def extract_skills(self, text: str) -> dict:
        """Extract predefined skills from resume or job-description text."""
        return self._find_terms(text, self.SKILL_DATABASE)

    def extract_keywords(self, text: str) -> list:
        """Extract important job-related phrases."""
        found = []

        for display_name, aliases in self.JOB_KEYWORDS.items():
            if any(self._contains_term(text, alias) for alias in aliases):
                found.append(display_name)

        return sorted(set(found))

    def analyze_job_description(self, text: str) -> dict:
        """
        Separate required and preferred skills and keywords.

        When no recognizable requirement headings are found,
        detected skills are treated as required by default.
        """
        required_lines = []
        preferred_lines = []
        current_group = "required"
        headings_found = False

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            normalized = re.sub(
                r"^[\s•*\-–—\d.)]+", "", line.lower()
            ).strip(" :")

            if any(
                normalized == heading
                or normalized.startswith(heading + " ")
                for heading in self.PREFERRED_HEADINGS
            ):
                current_group = "preferred"
                headings_found = True
                continue

            if any(
                normalized == heading
                or normalized.startswith(heading + " ")
                for heading in self.REQUIRED_HEADINGS
            ):
                current_group = "required"
                headings_found = True
                continue

            if re.search(
                r"\b(preferred|nice to have|good to have|bonus)\b",
                line,
                re.IGNORECASE,
            ):
                preferred_lines.append(line)
            elif current_group == "preferred":
                preferred_lines.append(line)
            else:
                required_lines.append(line)

        if not headings_found:
            required_lines = [text]
            preferred_lines = []

        required_text = "\n".join(required_lines)
        preferred_text = "\n".join(preferred_lines)

        required_skills = self.extract_skills(required_text)
        preferred_skills = self.extract_skills(preferred_text)

        # A skill listed as required should not also be preferred.
        required_flat = {
            skill
            for skills in required_skills.values()
            for skill in skills
        }

        for category in list(preferred_skills):
            preferred_skills[category] = [
                skill
                for skill in preferred_skills[category]
                if skill not in required_flat
            ]

            if not preferred_skills[category]:
                del preferred_skills[category]

        return {
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "required_keywords": self.extract_keywords(required_text),
            "preferred_keywords": self.extract_keywords(preferred_text),
            "qualifications": self._extract_qualifications(text),
            "section_headings_found": headings_found,
        }

    @staticmethod
    def _extract_qualifications(text: str) -> list:
        """Find lines mentioning likely education or experience criteria."""
        patterns = [
            r"\b(bachelor|master|diploma|degree|b\.?tech|m\.?tech|"
            r"bca|mca|b\.?sc|m\.?sc|graduate|graduation)\b",
            r"\b\d+\+?\s*(years?|yrs?)\b",
            r"\b(final[- ]year|freshers?|entry[- ]level)\b",
        ]

        results = []

        for line in text.splitlines():
            cleaned = line.strip()

            if any(
                re.search(pattern, cleaned, re.IGNORECASE)
                for pattern in patterns
            ):
                results.append(cleaned)

        return list(dict.fromkeys(results))[:20]

    def extract_sections(self, text: str) -> dict:
        """Extract likely education, experience and project sections."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        sections = {
            "Education": [],
            "Experience": [],
            "Projects": [],
        }

        active_section = None

        for line in lines:
            normalized = re.sub(
                r"[^a-z ]", "", line.lower()
            ).strip()

            matched_section = None

            for section, headings in self.SECTION_HEADINGS.items():
                if normalized in headings:
                    matched_section = section
                    break

            if matched_section:
                active_section = matched_section
                continue

            if self._is_heading(normalized):
                active_section = None
                continue

            if active_section:
                sections[active_section.capitalize()].append(line)

        if not sections["Education"]:
            education_terms = [
                "bachelor", "master", "diploma", "degree",
                "university", "college", "school", "b.tech",
                "bca", "mca", "b.sc", "m.sc", "12th", "10th",
            ]

            sections["Education"] = [
                line for line in lines
                if any(term in line.lower() for term in education_terms)
            ]

        if not sections["Projects"]:
            sections["Projects"] = [
                line for line in lines
                if "project" in line.lower()
            ]

        return {
            key: value[:30]
            for key, value in sections.items()
        }

    @staticmethod
    def _is_heading(line: str) -> bool:
        known_headings = {
            "summary",
            "profile",
            "objective",
            "skills",
            "technical skills",
            "certifications",
            "achievements",
            "languages",
            "contact",
            "interests",
            "hobbies",
            "references",
        }

        return line in known_headings
