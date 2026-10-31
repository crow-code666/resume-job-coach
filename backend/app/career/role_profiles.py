"""Curated role baselines for analysis when a job description is not supplied."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RoleProfile:
    key: str
    label: str
    aliases: tuple[str, ...]
    required_skills: tuple[str, ...]
    preferred_skills: tuple[str, ...]
    required_keywords: tuple[str, ...]
    preferred_keywords: tuple[str, ...]
    roadmap_slug: str


PROFILES = (
    RoleProfile("full-stack", "Full-stack developer", ("full stack", "full-stack", "fullstack"),
        ("JavaScript", "HTML", "CSS", "React", "Node.js", "SQL", "Git"),
        ("TypeScript", "Express.js", "PostgreSQL", "GitHub", "Docker"),
        ("REST APIs", "Software Testing", "Version Control", "Debugging", "Deployment"),
        ("CI/CD", "Cloud Computing", "Agile Methodology"), "full-stack"),
    RoleProfile("frontend", "Frontend developer", ("frontend", "front-end", "front end", "ui developer"),
        ("JavaScript", "HTML", "CSS", "React", "Git"),
        ("TypeScript", "Angular", "Tailwind CSS", "Bootstrap"),
        ("Software Testing", "Debugging", "Version Control", "REST APIs"),
        ("Agile Methodology", "Communication"), "frontend"),
    RoleProfile("backend", "Backend developer", ("backend", "back-end", "back end", "api developer"),
        ("Python", "SQL", "Git"), ("FastAPI", "Flask", "Django", "Node.js", "PostgreSQL", "Docker"),
        ("REST APIs", "API Development", "Database Management", "Software Testing", "Debugging", "Version Control", "Deployment"),
        ("CI/CD", "Cloud Computing", "SDLC"), "backend"),
    RoleProfile("software", "Software engineer / developer", ("software engineer", "software developer", "application developer", "programmer"),
        ("Python", "Java", "JavaScript", "Git"), ("C++", "C#", "TypeScript", "SQL", "Docker"),
        ("Data Structures", "Algorithms", "Object-Oriented Programming", "Software Testing", "Debugging", "Version Control", "SDLC"),
        ("Agile Methodology", "CI/CD", "Communication"), "backend"),
    RoleProfile("data-analyst", "Data analyst", ("data analyst", "business intelligence analyst", "bi analyst"),
        ("Python", "SQL", "Pandas", "Communication", "Problem Solving"), ("NumPy", "Matplotlib", "Microsoft Excel", "Tableau", "Power BI"),
        ("Data Analysis", "Database Management"),
        ("Requirements Analysis", "Technical Documentation"), "data-analyst"),
    RoleProfile("data-scientist", "Data scientist / machine learning engineer", ("data scientist", "machine learning", "ai engineer", "artificial intelligence engineer"),
        ("Python", "SQL", "Pandas", "NumPy", "Scikit-learn"), ("TensorFlow", "PyTorch", "Matplotlib"),
        ("Data Analysis", "Machine Learning", "Algorithms", "Problem Solving"),
        ("Technical Documentation", "Communication"), "ai-data-scientist"),
    RoleProfile("cybersecurity", "Cybersecurity analyst", ("cybersecurity", "cyber security", "security analyst", "soc analyst", "security operations"),
        ("Network Security", "SIEM", "Incident Response", "Vulnerability Management"),
        ("Python", "Linux", "MITRE ATT&CK", "NIST", "Firewall Management"),
        ("Troubleshooting", "System Monitoring", "Technical Documentation", "Risk Assessment"),
        ("Cloud Security", "Application Security", "Communication"), "cyber-security"),
    RoleProfile("devops", "Cloud / DevOps engineer", ("devops", "dev ops", "site reliability", "sre", "cloud engineer"),
        ("Linux", "Git", "Docker"), ("Kubernetes", "AWS", "Microsoft Azure", "Google Cloud", "Terraform", "Bash"),
        ("CI/CD", "Deployment", "Cloud Computing", "System Monitoring", "Troubleshooting"),
        ("Technical Documentation", "Problem Solving"), "devops"),
    RoleProfile("qa", "QA / software test engineer", ("qa engineer", "quality assurance", "software tester", "test engineer"),
        ("Python", "Git", "SQL"), ("Java", "JavaScript", "Docker"),
        ("Software Testing", "Debugging", "SDLC", "Technical Documentation", "Problem Solving"),
        ("Agile Methodology", "CI/CD"), "qa"),
    RoleProfile("it-support", "IT support specialist", ("it support", "technical support", "help desk", "helpdesk"),
        ("Windows", "Linux", "Communication", "Problem Solving"), ("Python", "Git"),
        ("Technical Support", "Troubleshooting", "System Monitoring", "Technical Documentation"),
        ("Team Collaboration", "Time Management"), "backend"),
    RoleProfile("ux-design", "UX / UI designer", ("ux designer", "ui designer", "product designer", "ux design", "user experience"),
        ("Communication", "Problem Solving", "Creativity", "Teamwork"), ("Figma", "HTML", "CSS", "JavaScript"),
        ("Requirements Analysis", "Solution Design"),
        ("Technical Documentation",), "ux-design"),
    RoleProfile("product-manager", "Product manager", ("product manager", "product management", "product owner"),
        ("Communication", "Problem Solving", "Teamwork", "Critical Thinking"), ("SQL", "Python"),
        ("Requirements Analysis", "Solution Design", "Data Analysis"),
        ("Agile Methodology", "Technical Documentation"), "product-manager"),
)

GENERAL_PROFILE = RoleProfile(
    "general", "General transferable-skills baseline", (),
    ("Communication", "Problem Solving", "Teamwork", "Adaptability"), (),
    ("Technical Documentation",), (), "",
)


def _normalize(value: str) -> str:
    value = re.sub(r"[^a-z0-9+#]+", " ", str(value or "").casefold())
    return " ".join(value.split())


def get_role_profile(target_role: str) -> tuple[RoleProfile, bool]:
    """Return the most specific known profile, or an explicitly general baseline."""
    normalized = _normalize(target_role)
    for profile in PROFILES:
        for alias in sorted(profile.aliases, key=len, reverse=True):
            normalized_alias = _normalize(alias)
            if re.search(rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])", normalized):
                return profile, True
    return GENERAL_PROFILE, False


