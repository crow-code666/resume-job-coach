
class JobMatcher:
    """Compare resume skills with skills detected in a job description."""

    @staticmethod
    def _flatten_skills(skill_data: dict) -> set:
        """Convert categorized skills into a single set."""
        all_skills = set()

        for skills in skill_data.values():
            all_skills.update(skills)

        return all_skills

    def compare(self, resume_skills: dict, job_skills: dict) -> dict:
        """Calculate skill coverage and identify skill gaps."""

        resume_set = self._flatten_skills(resume_skills)
        job_set = self._flatten_skills(job_skills)

        matched_skills = sorted(resume_set.intersection(job_set))
        missing_skills = sorted(job_set.difference(resume_set))
        additional_skills = sorted(resume_set.difference(job_set))

        total_required = len(job_set)
        total_matched = len(matched_skills)

        if total_required:
            coverage = round((total_matched / total_required) * 100, 2)
        else:
            coverage = None

        category_results = {}

        for category, required_skills in job_skills.items():
            matched = sorted(
                set(required_skills).intersection(resume_set)
            )
            missing = sorted(
                set(required_skills).difference(resume_set)
            )

            category_results[category] = {
                "matched": matched,
                "missing": missing,
                "required_count": len(required_skills),
            }

        return {
            "coverage": coverage,
            "total_required": total_required,
            "total_matched": total_matched,
            "total_missing": len(missing_skills),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "additional_skills": additional_skills,
            "category_results": category_results,
        }
