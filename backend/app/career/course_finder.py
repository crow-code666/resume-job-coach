"""Recommend a small catalog of official, no-cost learning resources.

This catalog works without API credentials. Provider pages are the authority
for current price and course details; learners should recheck those pages.
"""


COURSES = [
    {
        "title": "Python",
        "provider": "Kaggle Learn",
        "url": "https://www.kaggle.com/learn/python",
        "difficulty": "Beginner",
        "estimated_time": "5 hours (provider estimate)",
        "cost": "No cost, according to Kaggle Learn",
        "skills": {"python", "programming"},
    },
    {
        "title": "Get started with Python programming: Part 1 - Fundamentals",
        "provider": "Microsoft Learn",
        "url": "https://learn.microsoft.com/en-us/training/paths/get-started-with-python-fundamentals/",
        "difficulty": "Beginner",
        "estimated_time": "3 hr 12 min (provider estimate)",
        "cost": "Free training, according to Microsoft Learn",
        "skills": {"python", "programming", "vs code"},
    },
    {
        "title": "Intro to SQL",
        "provider": "Kaggle Learn",
        "url": "https://www.kaggle.com/learn/intro-to-sql",
        "difficulty": "Beginner",
        "estimated_time": "3 hours (provider estimate)",
        "cost": "No cost, according to Kaggle Learn",
        "skills": {"sql", "mysql", "postgresql", "database management"},
    },
    {
        "title": "Advanced SQL",
        "provider": "Kaggle Learn",
        "url": "https://www.kaggle.com/learn/advanced-sql/course",
        "difficulty": "Intermediate",
        "estimated_time": "4 hours (provider estimate)",
        "cost": "No cost, according to Kaggle Learn",
        "skills": {"sql", "mysql", "postgresql", "database management"},
    },
    {
        "title": "Pandas",
        "provider": "Kaggle Learn",
        "url": "https://www.kaggle.com/learn/pandas",
        "difficulty": "Beginner",
        "estimated_time": "4 hours (provider estimate)",
        "cost": "No cost, according to Kaggle Learn",
        "skills": {"pandas", "data analysis", "data cleaning"},
    },
    {
        "title": "Intro to Machine Learning",
        "provider": "Kaggle Learn",
        "url": "https://www.kaggle.com/learn/intro-to-machine-learning",
        "difficulty": "Beginner",
        "estimated_time": "3 hours (provider estimate)",
        "cost": "No cost, according to Kaggle Learn",
        "skills": {"machine learning", "scikit learn", "data science"},
    },
    {
        "title": "Introduction to Cybersecurity",
        "provider": "Cisco Networking Academy",
        "url": "https://www.netacad.com/courses/introduction-to-cybersecurity",
        "difficulty": "Beginner",
        "estimated_time": "6 hours (provider estimate)",
        "cost": "Free, according to Cisco Networking Academy",
        "skills": {"cybersecurity", "network security", "threat detection"},
    },
    {
        "title": "Introduction to cloud infrastructure: guided projects",
        "provider": "Microsoft Learn",
        "url": "https://learn.microsoft.com/en-us/training/paths/introduction-cloud-infrastructure-apply-azure-skills-guided-projects/",
        "difficulty": "Beginner",
        "estimated_time": "5 hr 8 min (provider estimate)",
        "cost": "Free Microsoft Learn training; check any cloud-account terms before deploying",
        "skills": {"cloud computing", "microsoft azure", "azure", "deployment"},
    },
]


ALIASES = {
    "mysql": "sql",
    "postgresql": "sql",
    "sqlite": "sql",
    "oracle database": "sql",
    "programming languages": "programming",
    "programming fundamentals": "programming",
    "data analytics": "data analysis",
    "scikit-learn": "scikit learn",
    "microsoft azure": "azure",
}


def _normalize(value):
    text = " ".join(str(value or "").casefold().replace("&", "and").split())
    return ALIASES.get(text, text)


class CourseFinder:
    """Match detected gaps to reviewed, provider-hosted free courses."""

    def __init__(self, courses=None):
        self.courses = COURSES if courses is None else courses

    def recommend(self, missing_skills, limit=6):
        """Return unique courses plus the gaps with no verified catalog match."""
        gaps = list(dict.fromkeys(
            str(skill).strip() for skill in (missing_skills or []) if str(skill).strip()
        ))
        normalized_gaps = {_normalize(skill): skill for skill in gaps}
        recommendations = []
        covered = set()

        for course in self.courses:
            tags = {_normalize(tag) for tag in course.get("skills", set())}
            matches = [
                original for normalized, original in normalized_gaps.items()
                if normalized in tags
            ]
            if not matches:
                continue
            recommendations.append({
                key: value for key, value in course.items() if key != "skills"
            } | {"matched_skills": matches})
            covered.update(matches)

        recommendations.sort(key=lambda course: (-len(course["matched_skills"]), course["title"]))
        return {
            "courses": recommendations[:max(0, limit)],
            "unmatched_skills": [skill for skill in gaps if skill not in covered],
        }
