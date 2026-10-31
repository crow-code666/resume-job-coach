
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
            "Terraform": ["terraform"],
            "Bash": ["bash", "shell scripting", "shell script"],
            "Linux": ["linux"],
            "Windows": ["windows"],
            "VS Code": ["vs code", "visual studio code"],
            "AWS": ["aws", "amazon web services"],
            "Microsoft Azure": ["microsoft azure", "azure"],
            "Google Cloud": ["google cloud", "gcp"],
            "Microsoft Excel": ["microsoft excel", "excel", "spreadsheets"],
            "Power BI": ["power bi", "powerbi"],
            "Tableau": ["tableau"],
            "Figma": ["figma"],
        },
        "Cybersecurity": {
            "Application Security": ["application security", "appsec"],
            "Cloud Security": ["cloud security"],
            "Cryptography": ["cryptography", "cryptographic"],
            "DevSecOps": ["devsecops"],
            "Digital Forensics": ["digital forensics", "computer forensics"],
            "Endpoint Security": ["endpoint security", "edr", "endpoint detection and response"],
            "Firewall Management": ["firewall", "firewalls", "firewall management"],
            "Identity and Access Management": ["identity and access management", "iam"],
            "Incident Response": ["incident response", "incident handling"],
            "Intrusion Detection and Prevention": ["ids/ips", "intrusion detection", "intrusion prevention"],
            "ISO 27001": ["iso 27001", "iso/iec 27001"],
            "MITRE ATT&CK": ["mitre att&ck", "mitre attack"],
            "Network Security": ["network security"],
            "NIST": ["nist"],
            "Penetration Testing": ["penetration testing", "penetration test", "pentesting", "pentest"],
            "Risk Assessment": ["risk assessment", "security risk assessment"],
            "Security Frameworks": ["security frameworks"],
            "SIEM": ["siem", "security information and event management"],
            "Security Operations": ["security operations", "security operations center", "soc"],
            "Threat Hunting": ["threat hunting"],
            "Vulnerability Management": ["vulnerability management", "vulnerability assessment", "vulnerability scanning"],
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
        "Technical Support": ["technical support", "support applications", "support users"],
        "Troubleshooting": ["troubleshoot", "troubleshooting", "resolve incidents"],
        "System Monitoring": ["monitor systems", "system monitoring", "monitor applications"],
        "Technical Documentation": ["technical documentation", "document code", "document solutions"],
        "Requirements Analysis": ["requirements analysis", "gather requirements", "analyze requirements"],
        "Solution Design": ["solution design", "design solutions", "system design"],
    }

    SECTION_HEADINGS = {
        "summary": [
            "summary",
            "profile",
            "professional summary",
            "career summary",
            "profile summary",
            "professional profile",
            "objective",
        ],
        "education": [
            "education",
            "academic background",
            "educational background",
            "educational qualifications",
            "academic qualifications",
            "qualification",
        ],
        "experience": [
            "work experience",
            "professional experience",
            "relevant experience",
            "work history",
            "career history",
            "employment history",
            "employment",
            "experience",
            "internship",
            "internships",
        ],
        "projects": [
            "projects",
            "personal projects",
            "academic projects",
            "project experience",
            "selected projects",
            "portfolio",
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
            "required_qualifications": self._extract_qualifications(required_text),
            "preferred_qualifications": self._extract_qualifications(preferred_text),
            "required_responsibilities": self._extract_responsibilities(required_text),
            "preferred_responsibilities": self._extract_responsibilities(preferred_text),
            "section_headings_found": headings_found,
        }

    @staticmethod
    def _extract_responsibilities(text: str) -> list:
        """Keep job-task statements visible so candidates can compare evidence."""
        action = re.compile(
            r"\b(build|create|design|develop|implement|maintain|test|debug|"
            r"deploy|monitor|analy[sz]e|collaborate|coordinate|support|"
            r"troubleshoot|document|automate|secure|review|manage|investigate|"
            r"respond|configure|deliver|improve|lead)\w*\b",
            re.IGNORECASE,
        )
        responsibilities = []
        for raw_line in text.splitlines():
            line = re.sub(r"^[\s•*\-–—\d.)]+", "", raw_line).strip()
            if len(line) >= 20 and action.search(line):
                if line.casefold() not in {item.casefold() for item in responsibilities}:
                    responsibilities.append(line[:280])
        return responsibilities[:12]

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
            cleaned = re.sub(r"^[\s•*\-–—\d.)]+", "", line).strip()

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
            "Summary": [],
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
