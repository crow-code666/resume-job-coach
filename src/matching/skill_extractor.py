
import re


class SkillExtractor:
    """Lightweight resume skill and section extraction engine."""

    SKILL_DATABASE = {
        "Programming Languages": {
            "Python": ["python"],
            "Java": ["java"],
            "C": ["c programming", "programming in c"],
            "C++": ["c++"],
            "C#": ["c#"],
            "JavaScript": ["javascript", "js"],
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

    def extract_skills(self, text: str) -> dict:
        """Find skills mentioned in the supplied resume text."""
        text_lower = text.lower()
        results = {}

        for category, skills in self.SKILL_DATABASE.items():
            found = []

            for skill_name, keywords in skills.items():
                for keyword in keywords:
                    pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"

                    if re.search(pattern, text_lower):
                        found.append(skill_name)
                        break

            if found:
                results[category] = sorted(set(found))

        return results

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
            normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()

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
                display_name = active_section.capitalize()
                sections[display_name].append(line)

        # Fallback: identify likely education lines if no education heading exists.
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

        # Fallback: identify likely project lines if no project heading exists.
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
        """Check whether a line looks like another resume section heading."""
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
