from __future__ import annotations

from src.analyzer.models import JobRequirements


class ExperienceStrategy:
    """Rule-based strategy for selecting and ranking experiences by relevance to a job."""

    def select(
        self,
        experiences: list[dict],
        requirements: JobRequirements,
        max_experiences: int = 5,
    ) -> list[dict]:
        """Select the most relevant experiences for the given job requirements.

        Skips parent/umbrella entries and scores children individually.
        Returns up to max_experiences, sorted by date (most recent first).
        """
        scored = []
        for exp in experiences:
            if exp.get("is_parent"):
                continue
            score = self._compute_relevance(exp, requirements)
            scored.append((score, exp))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [exp for _, exp in scored[:max_experiences]]

        # Sort selected by date (most recent first)
        selected.sort(key=lambda e: e.get("start_date", ""), reverse=True)
        return selected

    def _compute_relevance(
        self, exp: dict, requirements: JobRequirements
    ) -> float:
        """Compute relevance score (0.0 to 1.0) based on skill overlap."""
        exp_skills = {s.lower() for s in exp.get("skills_used", [])}
        req_skills = {
            s.lower()
            for s in requirements.required_skills + requirements.preferred_skills
        }
        keywords = {k.lower() for k in requirements.keywords}

        if not req_skills and not keywords:
            return 0.0

        all_targets = req_skills | keywords
        overlap = exp_skills & all_targets
        return len(overlap) / max(len(all_targets), 1)

    def select_certifications(
        self, certifications: list[dict], requirements: JobRequirements
    ) -> list[dict]:
        """Select certifications relevant to the job requirements."""
        req_tags = {
            k.lower()
            for k in requirements.required_skills
            + requirements.preferred_skills
            + requirements.keywords
        }

        scored = []
        for cert in certifications:
            cert_tags = {t.lower() for t in cert.get("relevance_tags", [])}
            overlap = cert_tags & req_tags
            scored.append((len(overlap), cert))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [cert for _, cert in scored]
