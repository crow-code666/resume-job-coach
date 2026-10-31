"""Compare resume evidence with a job description using explainable rules."""

import re


class JobMatcher:
    """Calculate skill coverage and a broader, evidence-based fit snapshot."""

    COMPONENT_WEIGHTS = {
        "skills": 0.55,
        "keywords": 0.20,
        "responsibilities": 0.15,
        "qualifications": 0.10,
    }
    STOP_WORDS = {
        "the", "and", "for", "with", "from", "into", "their", "your", "our",
        "this", "that", "will", "work", "role", "team", "ability", "skills",
        "experience", "using", "ensure", "across", "including", "such", "as",
    }
    ACTION_GROUPS = (
        {"build", "built", "create", "created", "develop", "developed", "design", "designed", "implement", "implemented"},
        {"test", "tested", "testing", "validate", "validated", "verify", "verified", "ensure", "ensured"},
        {"deploy", "deployed", "deployment", "release", "released"},
        {"maintain", "maintained", "support", "supported", "troubleshoot", "troubleshot", "resolve", "resolved"},
        {"analyze", "analyzed", "analyse", "analysed", "investigate", "investigated", "review", "reviewed"},
        {"collaborate", "collaborated", "coordinate", "coordinated", "partner", "partnered", "work", "worked", "cooperate", "cooperated"},
        {"monitor", "monitored", "observe", "observed", "track", "tracked"},
        {"document", "documented", "write", "wrote", "author", "authored"},
        {"secure", "secured", "protect", "protected", "harden", "hardened"},
        {"manage", "managed", "lead", "led", "operate", "operated"},
    )

    @staticmethod
    def _flatten_skills(skill_data):
        return {
            skill
            for skills in (skill_data or {}).values()
            for skill in skills
        }

    @staticmethod
    def _normalized_text(text):
        return " ".join(str(text or "").casefold().split())

    @classmethod
    def _responsibility_match(cls, requirement, evidence_text):
        """Require both a related action and a task-specific noun in resume evidence."""
        def tokens(text):
            values = re.findall(r"[a-z0-9+#.]+", str(text or "").casefold())
            normalized = set()
            for value in values:
                if value == "restful":
                    normalized.add("rest")
                elif value == "apis":
                    normalized.add("api")
                else:
                    normalized.add(value.rstrip("s") if len(value) > 4 else value)
            return normalized

        required = tokens(requirement)
        evidence = tokens(evidence_text)
        action_groups = [group for group in cls.ACTION_GROUPS if required & group]
        action_supported = any(evidence & group for group in action_groups)
        content = required - cls.STOP_WORDS
        content -= {action for group in cls.ACTION_GROUPS for action in group}
        return bool(action_supported and content & evidence)

    @classmethod
    def _coverage(cls, matches, requirements):
        if not requirements:
            return None
        return round(len(matches) / len(requirements) * 100, 2)

    def compare(
        self,
        resume_skills,
        job_skills,
        *,
        resume_keywords=None,
        required_keywords=None,
        resume_text="",
        required_qualifications=None,
        required_responsibilities=None,
        additional_evidence_text="",
        additional_skill_evidence=None,
    ):
        """Compare skills, JD keywords, and explicit qualification phrases.

        ``coverage`` remains the original skill-only percentage for backwards
        compatibility. ``overall_coverage`` combines the evidence dimensions
        that are actually present in this job description, reweighting the
        available dimensions so a missing section does not lower the score.
        """
        resume_set = self._flatten_skills(resume_skills)
        evidence_set = self._flatten_skills(additional_skill_evidence)
        required_set = self._flatten_skills(job_skills)
        supported_set = resume_set | evidence_set
        matched_skills = sorted(supported_set & required_set)
        resume_matched_skills = sorted(resume_set & required_set)
        evidence_matched_skills = sorted((evidence_set - resume_set) & required_set)
        missing_skills = sorted(required_set - supported_set)

        resume_keyword_set = {str(item).casefold() for item in resume_keywords or []}
        required_keyword_set = {str(item).casefold() for item in required_keywords or []}
        matched_keywords = sorted(required_keyword_set & resume_keyword_set)
        missing_keywords = sorted(required_keyword_set - resume_keyword_set)

        normalized_resume = self._normalized_text(resume_text)
        qualifications = list(dict.fromkeys(required_qualifications or []))
        matched_qualifications = [
            item for item in qualifications
            if self._normalized_text(item) and self._normalized_text(item) in normalized_resume
        ]
        missing_qualifications = [
            item for item in qualifications if item not in matched_qualifications
        ]
        responsibilities = list(dict.fromkeys(required_responsibilities or []))
        responsibility_text = f"{resume_text or ''}\n{additional_evidence_text or ''}"
        matched_responsibilities = [
            item for item in responsibilities
            if self._responsibility_match(item, responsibility_text)
        ]
        missing_responsibilities = [
            item for item in responsibilities if item not in matched_responsibilities
        ]

        component_data = {
            "skills": (matched_skills, sorted(required_set)),
            "keywords": (matched_keywords, sorted(required_keyword_set)),
            "responsibilities": (matched_responsibilities, responsibilities),
            "qualifications": (matched_qualifications, qualifications),
        }
        score_components = {}
        weighted_total = 0.0
        active_weight = 0.0
        for name, (matched, required) in component_data.items():
            coverage = self._coverage(matched, required)
            weight = self.COMPONENT_WEIGHTS[name] if required else 0.0
            score_components[name] = {
                "matched": matched,
                "missing": [item for item in required if item not in matched],
                "required_count": len(required),
                "coverage": coverage,
                "weight": weight,
            }
            if name == "skills":
                score_components[name]["supported_by_resume"] = resume_matched_skills
                score_components[name]["supported_by_submitted_evidence"] = evidence_matched_skills
            if coverage is not None:
                weighted_total += coverage * weight
                active_weight += weight

        category_results = {}
        for category, required_skills in (job_skills or {}).items():
            required = set(required_skills)
            category_results[category] = {
                "matched": sorted(required & supported_set),
                "missing": sorted(required - supported_set),
                "required_count": len(required),
            }

        skills_coverage = self._coverage(matched_skills, sorted(required_set))
        return {
            # Keep the old meaning of coverage so existing callers remain valid.
            "coverage": skills_coverage,
            "skills_coverage": skills_coverage,
            "keyword_coverage": score_components["keywords"]["coverage"],
            "responsibility_coverage": score_components["responsibilities"]["coverage"],
            "qualification_coverage": score_components["qualifications"]["coverage"],
            "overall_coverage": round(weighted_total / active_weight, 2) if active_weight else None,
            "score_components": score_components,
            "total_required": len(required_set),
            "total_matched": len(matched_skills),
            "total_missing": len(missing_skills),
            "matched_skills": matched_skills,
            "resume_matched_skills": resume_matched_skills,
            "evidence_matched_skills": evidence_matched_skills,
            "missing_skills": missing_skills,
            "additional_skills": sorted(resume_set - required_set),
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "matched_responsibilities": matched_responsibilities,
            "missing_responsibilities": missing_responsibilities,
            "matched_qualifications": matched_qualifications,
            "missing_qualifications": missing_qualifications,
            "category_results": category_results,
        }
