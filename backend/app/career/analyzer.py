from dataclasses import dataclass

from app.career.course_finder import CourseFinder
from app.career.job_matcher import JobMatcher
from app.career.learning_planner import LearningPlanner
from app.career.parser import ResumeParser
from app.career.role_profiles import RoleProfile, get_role_profile
from app.career.skill_extractor import SkillExtractor


@dataclass
class ResumeBytes:
    name: str
    data: bytes

    def getvalue(self) -> bytes:
        return self.data


def _evidence_excerpt(skill: str, text: str, extractor: SkillExtractor) -> str | None:
    aliases = [skill.casefold()]
    for category in extractor.SKILL_DATABASE.values():
        if skill in category:
            aliases.extend(category[skill])
    for line in str(text or "").splitlines():
        clean = " ".join(line.split())
        if clean and any(extractor._contains_term(clean, alias) for alias in aliases):
            return clean[:320]
    return None


def _profile_skill_groups(skill_names: tuple[str, ...], extractor: SkillExtractor) -> dict[str, list[str]]:
    wanted = set(skill_names)
    groups = {
        category: sorted(name for name in skills if name in wanted)
        for category, skills in extractor.SKILL_DATABASE.items()
    }
    grouped = {category: skills for category, skills in groups.items() if skills}
    recognized = {name for skills in grouped.values() for name in skills}
    missing = wanted - recognized
    if missing:
        raise ValueError(f"Role profile contains an unsupported skill: {', '.join(sorted(missing))}.")
    return grouped


def _profile_analysis(profile: RoleProfile, extractor: SkillExtractor) -> dict:
    """Keep profile skills and focus keywords separate so a signal is not double-counted."""
    return {
        "required_skills": _profile_skill_groups(profile.required_skills, extractor),
        "preferred_skills": _profile_skill_groups(profile.preferred_skills, extractor),
        "required_keywords": list(profile.required_keywords),
        "preferred_keywords": list(profile.preferred_keywords),
        "required_qualifications": [],
        "required_responsibilities": [],
    }


def analyze_resume(
    data: bytes,
    filename: str,
    target_role: str,
    additional_evidence_text: str = "",
) -> dict:
    """Parse one private resume and compare it with a transparent role baseline."""
    parser = ResumeParser()
    extractor = SkillExtractor()
    matcher = JobMatcher()

    try:
        resume_text = parser.extract_text(ResumeBytes(name=filename, data=data))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("This file could not be read. Try exporting a text-based PDF or DOCX.") from exc

    resume_skills = extractor.extract_skills(resume_text)
    evidence_skills = extractor.extract_skills(additional_evidence_text)
    profile, profile_is_specialized = get_role_profile(target_role)
    job_analysis = _profile_analysis(profile, extractor)
    resume_sections = extractor.extract_sections(resume_text)
    searchable_text = f"{resume_text}\n{additional_evidence_text}"
    match = matcher.compare(
        resume_skills,
        job_analysis["required_skills"],
        resume_keywords=extractor.extract_keywords(searchable_text),
        required_keywords=job_analysis["required_keywords"],
        resume_text=searchable_text,
        required_qualifications=job_analysis["required_qualifications"],
        required_responsibilities=job_analysis["required_responsibilities"],
        additional_skill_evidence=evidence_skills,
    )
    missing = list(dict.fromkeys(match["missing_skills"] + match["missing_keywords"]))
    learning_plan = LearningPlanner().create_plan(missing, job_role=target_role)
    course_recommendations = CourseFinder().recommend(missing)
    evidence_items = []
    for skill in match["matched_skills"]:
        excerpt = _evidence_excerpt(skill, resume_text, extractor)
        source = "resume"
        if excerpt is None:
            excerpt = _evidence_excerpt(skill, additional_evidence_text, extractor)
            source = "candidate-submitted project or experience"
        if excerpt:
            evidence_items.append({"skill": skill, "source": source, "excerpt": excerpt})

    return {
        "target_role": target_role,
        "role_profile": {
            "key": profile.key,
            "label": profile.label,
            "specialized": profile_is_specialized,
            "note": (
                f"This comparison uses a curated {profile.label} baseline. Requirements vary by employer, so check each actual posting."
                if profile_is_specialized else
                "This title has no specialized built-in profile yet. The score uses general transferable skills only and is not an estimate of employer requirements."
            ),
        },
        "resume_sections": resume_sections,
        "resume_skills": resume_skills,
        "candidate_evidence_skills": evidence_skills,
        "required_skills": job_analysis["required_skills"],
        "preferred_skills": job_analysis["preferred_skills"],
        "match": {
            "skill_coverage": match["skills_coverage"],
            "overall_coverage": match["overall_coverage"],
            "total_required": match["total_required"],
            "total_matched": match["total_matched"],
            "matched_skills": match["matched_skills"],
            "resume_matched_skills": match["resume_matched_skills"],
            "evidence_matched_skills": match["evidence_matched_skills"],
            "missing_skills": match["missing_skills"],
            "additional_skills": match["additional_skills"],
            "matched_keywords": match["matched_keywords"],
            "missing_keywords": match["missing_keywords"],
            "matched_responsibilities": match["matched_responsibilities"],
            "missing_responsibilities": match["missing_responsibilities"],
            "matched_qualifications": match["matched_qualifications"],
            "missing_qualifications": match["missing_qualifications"],
            "score_components": match["score_components"],
            "evidence": evidence_items,
        },
        "learning_plan": learning_plan,
        "course_recommendations": course_recommendations["courses"],
        "unmatched_learning_gaps": course_recommendations["unmatched_skills"],
        "note": (
            "This local comparison reports evidence found in the resume text. "
            "A missing term may be a parser miss, and the result is not a hiring probability."
        ),
    }
