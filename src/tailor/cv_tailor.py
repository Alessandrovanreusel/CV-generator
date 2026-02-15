from __future__ import annotations

import json

from src.analyzer.models import JobRequirements
from src.analyzer.prompts import TAILOR_BULLETS_PROMPT, TAILOR_SUMMARY_PROMPT
from src.tailor.models import (
    PersonalInfo,
    TailoredCertification,
    TailoredCV,
    TailoredEducation,
    TailoredExperience,
    TailoredLanguageSkill,
    TailoredProject,
    TailoredVolunteering,
)
from src.tailor.strategies import ExperienceStrategy
from src.utils.claude_cli import call_claude


def _resolve_bilingual(field: dict | str, language: str) -> str:
    """Resolve a bilingual field to the target language."""
    if isinstance(field, dict):
        return field.get(language, field.get("en", ""))
    return field


def _resolve_bilingual_list(field: dict | list, language: str) -> list[str]:
    """Resolve a bilingual list field to the target language."""
    if isinstance(field, dict):
        return field.get(language, field.get("en", []))
    return field


def _resolve_coursework(field: dict | str | None, language: str) -> list[str]:
    """Resolve a bilingual coursework field to a list of items."""
    if field is None:
        return []
    text = _resolve_bilingual(field, language) if isinstance(field, dict) else field
    if not text:
        return []
    return [item.strip() for item in text.split(", ")]


class CvTailor:
    """Tailor a master CV to match job requirements using Claude CLI + rules."""

    def __init__(self, model: str | None = None, client=None):
        # model and client kept for backward compatibility but not used
        self.strategy = ExperienceStrategy()

    def tailor(
        self,
        master_cv: dict,
        requirements: JobRequirements,
        language: str = "en",
    ) -> TailoredCV:
        """Produce a tailored CV from master data and job requirements."""
        # Step 1: Select relevant experiences
        selected_exps = self.strategy.select(
            master_cv["experience"], requirements
        )

        # Step 2: Rewrite summary via Claude CLI
        original_summary = _resolve_bilingual(
            master_cv["professional_summary"], language
        )
        tailored_summary = self._rewrite_summary(
            original_summary, requirements, language
        )

        # Step 3: Enhance bullet points via Claude CLI
        tailored_experiences = []
        for exp in selected_exps:
            enhanced = self._enhance_experience(exp, requirements, language)
            tailored_experiences.append(enhanced)

        # Step 4: Reorder skills
        reordered_skills = self._reorder_skills(
            master_cv["skills"], requirements
        )

        # Step 5: Select certifications
        certs = self.strategy.select_certifications(
            master_cv.get("certifications", []), requirements
        )

        # Step 6: Resolve remaining fields to target language
        personal = master_cv["personal_info"]
        personal_info = PersonalInfo(
            name=personal["name"],
            title=_resolve_bilingual(personal["title"], language),
            email=personal["email"],
            phone=personal["phone"],
            location=personal["location"],
            linkedin=personal.get("linkedin", ""),
            commercial_email=personal.get("commercial_email", ""),
            photo_path=personal.get("photo", ""),
        )

        education = [
            TailoredEducation(
                institution=e["institution"],
                degree=_resolve_bilingual(e["degree"], language),
                location=e.get("location", ""),
                start_date=e["start_date"],
                end_date=e["end_date"],
                details=_resolve_coursework(
                    e.get("coursework"), language
                ),
            )
            for e in master_cv.get("education", [])
        ]

        projects = [
            TailoredProject(
                name=_resolve_bilingual(p["name"], language),
                description=_resolve_bilingual(
                    p.get("description", ""), language
                ),
                technologies=p.get("technologies", []),
            )
            for p in master_cv.get("projects", [])
        ]

        languages = [
            TailoredLanguageSkill(
                language=_resolve_bilingual(lang["language"], language),
                level=_resolve_bilingual(lang["level"], language),
                code=lang.get("code", ""),
            )
            for lang in master_cv.get("languages", [])
        ]

        volunteering = [
            TailoredVolunteering(
                organization=v["organization"],
                role=_resolve_bilingual(v["role"], language),
                description=_resolve_bilingual(
                    v.get("description", ""), language
                ),
            )
            for v in master_cv.get("volunteering", [])
        ]

        tailored_certs = [
            TailoredCertification(
                name=c["name"],
                issuer=c.get("issuer", ""),
                date=c.get("date", ""),
            )
            for c in certs
        ]

        return TailoredCV(
            personal=personal_info,
            summary=tailored_summary,
            experience=tailored_experiences,
            education=education,
            skills=reordered_skills,
            languages=languages,
            certifications=tailored_certs,
            projects=projects,
            volunteering=volunteering,
            target_language=language,
        )

    def _rewrite_summary(
        self,
        current_summary: str,
        requirements: JobRequirements,
        language: str,
    ) -> str:
        """Rewrite the professional summary to match job requirements."""
        lang_name = "French" if language == "fr" else "English"
        prompt = TAILOR_SUMMARY_PROMPT.format(
            current_summary=current_summary,
            job_title=requirements.title,
            company=requirements.company,
            required_skills=", ".join(requirements.required_skills),
            responsibilities="; ".join(requirements.responsibilities[:5]),
            language=lang_name,
        )

        return call_claude(prompt)

    def _enhance_experience(
        self,
        exp: dict,
        requirements: JobRequirements,
        language: str,
    ) -> TailoredExperience:
        """Enhance an experience entry's bullet points for the target job."""
        bullets = _resolve_bilingual_list(exp.get("bullets", {}), language)

        # Limit to 4 best bullets for brevity
        bullets = bullets[:4]

        lang_name = "French" if language == "fr" else "English"
        prompt = TAILOR_BULLETS_PROMPT.format(
            bullets=json.dumps(bullets, ensure_ascii=False),
            required_skills=", ".join(requirements.required_skills),
            keywords=", ".join(requirements.keywords),
            responsibilities="; ".join(requirements.responsibilities[:5]),
            num_bullets=len(bullets),
            language=lang_name,
        )

        raw = call_claude(prompt)

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]

        try:
            enhanced_bullets = json.loads(raw)
        except json.JSONDecodeError:
            enhanced_bullets = bullets  # Fallback to original

        return TailoredExperience(
            id=exp["id"],
            company=exp["company"],
            title=_resolve_bilingual(exp["title"], language),
            location=exp["location"],
            start_date=exp["start_date"],
            end_date=exp.get("end_date"),
            is_current=exp.get("is_current", False),
            summary=_resolve_bilingual(exp.get("summary", ""), language),
            bullets=enhanced_bullets,
            skills_used=exp.get("skills_used", []),
        )

    # Skills with proficiency >= this threshold are always kept
    STRONG_SKILL_THRESHOLD = 85
    STRONG_SKILLS = {
        "Python", "Java", "JavaScript", "React.js", "AWS", "CI/CD",
        "Git", "Agile/Scrum", "Test Automation", "Docker",
    }

    def _reorder_skills(
        self, skills: dict, requirements: JobRequirements
    ) -> dict[str, list[str]]:
        """Reorder skills and inject missing job-required skills.

        1. Add required/preferred skills from the job ad that are missing
           from the master CV (placed in a 'Job-Relevant' category at the top).
        2. Sort skills within each category: job-relevant first, then
           strong/core skills, then the rest.
        3. Sort categories by relevance.
        """
        req_skills = (
            requirements.required_skills + requirements.preferred_skills
        )
        req_skills_lower = {
            s.lower()
            for s in req_skills + requirements.keywords
        }

        # Collect all existing skills (lowercase) for lookup
        existing_lower = set()
        for skills_list in skills.values():
            for s in skills_list:
                existing_lower.add(s.lower())

        # Find job-required skills not already in the master CV
        missing_skills = []
        for s in req_skills:
            if s.lower() not in existing_lower and s not in missing_skills:
                missing_skills.append(s)

        # Build the reordered dict, injecting missing skills first
        reordered = {}
        if missing_skills:
            reordered["Job-Relevant"] = missing_skills

        def skill_sort_key(skill: str) -> tuple[int, int]:
            is_relevant = skill.lower() in req_skills_lower
            is_strong = skill in self.STRONG_SKILLS
            priority = 0 if is_relevant else (1 if is_strong else 2)
            return (priority, 0)

        for name, skills_list in skills.items():
            sorted_skills = sorted(skills_list, key=skill_sort_key)
            reordered[name] = sorted_skills

        def category_relevance(category_skills: list[str]) -> int:
            return sum(
                1 for s in category_skills if s.lower() in req_skills_lower
            )

        scored = [
            (category_relevance(skills_list), name, skills_list)
            for name, skills_list in reordered.items()
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        return {name: skills_list for _, name, skills_list in scored}
