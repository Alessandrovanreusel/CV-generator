"""Tests for the tailor engine (strategies, helpers, and CvTailor)."""

import json
from unittest.mock import patch

import pytest

from src.analyzer.models import JobRequirements
from src.tailor.cv_tailor import (
    CvTailor,
    _resolve_bilingual,
    _resolve_bilingual_list,
    _resolve_coursework,
)
from src.tailor.strategies import ExperienceStrategy


# ---------------------------------------------------------------------------
# ExperienceStrategy tests
# ---------------------------------------------------------------------------


class TestExperienceStrategySelect:
    """Test that ExperienceStrategy.select() picks the most relevant experiences."""

    def test_experience_strategy_select(self, sample_job_requirements):
        """Experiences with more skill overlap should be ranked higher."""
        experiences = [
            {
                "id": "exp-low",
                "company": "Irrelevant Co",
                "title": {"en": "Barista"},
                "location": "Nowhere",
                "start_date": "2020-01",
                "end_date": "2021-01",
                "is_current": False,
                "is_parent": False,
                "skills_used": ["Coffee", "Latte Art"],
                "bullets": {"en": ["Made coffee"]},
            },
            {
                "id": "exp-high",
                "company": "CloudTech BV",
                "title": {"en": "Software Engineer"},
                "location": "Amsterdam",
                "start_date": "2024-01",
                "end_date": None,
                "is_current": True,
                "is_parent": False,
                "skills_used": ["Python", "AWS", "Docker", "CI/CD"],
                "bullets": {"en": ["Built APIs"]},
            },
            {
                "id": "exp-mid",
                "company": "WebAgency",
                "title": {"en": "Frontend Dev"},
                "location": "Brussels",
                "start_date": "2022-01",
                "end_date": "2023-12",
                "is_current": False,
                "is_parent": False,
                "skills_used": ["React", "TypeScript"],
                "bullets": {"en": ["Built UIs"]},
            },
        ]

        strategy = ExperienceStrategy()
        selected = strategy.select(experiences, sample_job_requirements, max_experiences=3)

        assert len(selected) == 3
        # The high-relevance experience (Python, AWS, Docker) should be present
        selected_ids = [e["id"] for e in selected]
        assert "exp-high" in selected_ids
        assert "exp-mid" in selected_ids


class TestExperienceStrategySkipsParents:
    """Test that parent/umbrella entries are skipped."""

    def test_experience_strategy_skips_parents(self, sample_job_requirements):
        """Entries with is_parent=True should be excluded from selection."""
        experiences = [
            {
                "id": "exp-parent",
                "company": "Umbrella Corp",
                "title": {"en": "Consultant"},
                "location": "Paris",
                "start_date": "2021-01",
                "end_date": "2022-05",
                "is_current": False,
                "is_parent": True,
                "skills_used": ["Python"],
                "bullets": {"en": []},
            },
            {
                "id": "exp-child",
                "company": "Umbrella Corp",
                "title": {"en": "Python Developer"},
                "location": "Paris",
                "start_date": "2021-06",
                "end_date": "2022-05",
                "is_current": False,
                "is_parent": False,
                "skills_used": ["Python", "AWS"],
                "bullets": {"en": ["Developed tools"]},
            },
        ]

        strategy = ExperienceStrategy()
        selected = strategy.select(experiences, sample_job_requirements)

        selected_ids = [e["id"] for e in selected]
        assert "exp-parent" not in selected_ids
        assert "exp-child" in selected_ids


class TestExperienceStrategyMaxLimit:
    """Test that the max_experiences parameter is respected."""

    def test_experience_strategy_max_limit(self, sample_job_requirements):
        """Should return at most max_experiences entries."""
        experiences = [
            {
                "id": f"exp-{i}",
                "company": f"Company {i}",
                "title": {"en": f"Role {i}"},
                "location": "Somewhere",
                "start_date": f"202{i}-01",
                "end_date": f"202{i}-12",
                "is_current": False,
                "is_parent": False,
                "skills_used": ["Python"],
                "bullets": {"en": [f"Did thing {i}"]},
            }
            for i in range(8)
        ]

        strategy = ExperienceStrategy()

        selected_3 = strategy.select(experiences, sample_job_requirements, max_experiences=3)
        assert len(selected_3) == 3

        selected_2 = strategy.select(experiences, sample_job_requirements, max_experiences=2)
        assert len(selected_2) == 2


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestResolveBilingual:
    """Test the _resolve_bilingual helper."""

    def test_resolve_bilingual_with_dict_en(self):
        """Resolve a bilingual dict to English."""
        field = {"en": "Software Engineer", "fr": "Ingenieur Logiciel"}
        assert _resolve_bilingual(field, "en") == "Software Engineer"

    def test_resolve_bilingual_with_dict_fr(self):
        """Resolve a bilingual dict to French."""
        field = {"en": "Software Engineer", "fr": "Ingenieur Logiciel"}
        assert _resolve_bilingual(field, "fr") == "Ingenieur Logiciel"

    def test_resolve_bilingual_with_string(self):
        """Pass-through when field is already a plain string."""
        assert _resolve_bilingual("Already resolved", "en") == "Already resolved"
        assert _resolve_bilingual("Already resolved", "fr") == "Already resolved"

    def test_resolve_bilingual_fallback_to_en(self):
        """Fallback to 'en' when the target language key is missing."""
        field = {"en": "Fallback Title"}
        assert _resolve_bilingual(field, "fr") == "Fallback Title"

    def test_resolve_bilingual_empty_dict(self):
        """Return empty string for an empty dict."""
        assert _resolve_bilingual({}, "en") == ""


class TestResolveBilingualList:
    """Test the _resolve_bilingual_list helper."""

    def test_resolve_bilingual_list_dict_en(self):
        """Resolve a bilingual list dict to English."""
        field = {
            "en": ["Built APIs", "Deployed on AWS"],
            "fr": ["Construit des API", "Deploye sur AWS"],
        }
        result = _resolve_bilingual_list(field, "en")
        assert result == ["Built APIs", "Deployed on AWS"]

    def test_resolve_bilingual_list_dict_fr(self):
        """Resolve a bilingual list dict to French."""
        field = {
            "en": ["Built APIs"],
            "fr": ["Construit des API"],
        }
        result = _resolve_bilingual_list(field, "fr")
        assert result == ["Construit des API"]

    def test_resolve_bilingual_list_already_list(self):
        """Pass-through when field is already a plain list."""
        field = ["Already", "resolved"]
        result = _resolve_bilingual_list(field, "en")
        assert result == ["Already", "resolved"]

    def test_resolve_bilingual_list_fallback(self):
        """Fallback to 'en' when target language key is missing."""
        field = {"en": ["Fallback bullet"]}
        result = _resolve_bilingual_list(field, "fr")
        assert result == ["Fallback bullet"]


class TestResolveCoursework:
    """Test the _resolve_coursework helper."""

    def test_resolve_coursework_none(self):
        """None should return an empty list."""
        assert _resolve_coursework(None, "en") == []

    def test_resolve_coursework_bilingual_dict(self):
        """Bilingual dict should be resolved and split by comma."""
        field = {
            "en": "Data Structures, Algorithms, Cloud Computing",
            "fr": "Structures de donnees, Algorithmes, Cloud Computing",
        }
        result = _resolve_coursework(field, "en")
        assert result == ["Data Structures", "Algorithms", "Cloud Computing"]

        result_fr = _resolve_coursework(field, "fr")
        assert result_fr == ["Structures de donnees", "Algorithmes", "Cloud Computing"]

    def test_resolve_coursework_plain_string(self):
        """A plain string should be split by comma."""
        result = _resolve_coursework("Math, Physics, Chemistry", "en")
        assert result == ["Math", "Physics", "Chemistry"]

    def test_resolve_coursework_empty_string(self):
        """An empty string should return an empty list."""
        assert _resolve_coursework("", "en") == []


# ---------------------------------------------------------------------------
# Reorder skills test
# ---------------------------------------------------------------------------


class TestReorderSkills:
    """Test _reorder_skills puts matching categories first."""

    def test_reorder_skills(self, sample_job_requirements):
        """Categories with more matching skills should appear first."""
        skills = {
            "Frameworks": ["Angular", "Vue"],
            "Cloud": ["AWS", "Docker", "Terraform"],
            "Programming": ["Python", "Java"],
        }

        tailor = CvTailor.__new__(CvTailor)
        reordered = tailor._reorder_skills(skills, sample_job_requirements)

        categories = list(reordered.keys())
        # Cloud has AWS, Docker, Terraform -- all in required/preferred/keywords
        # Programming has Python -- in required_skills
        # Frameworks has none matching
        assert categories[0] == "Cloud"
        assert categories[-1] == "Frameworks"


# ---------------------------------------------------------------------------
# CvTailor PersonalInfo build test
# ---------------------------------------------------------------------------


class TestCvTailorBuildsPersonalInfo:
    """Test that CvTailor builds PersonalInfo correctly from master_cv."""

    @patch("src.tailor.cv_tailor.call_claude")
    def test_cv_tailor_builds_personal_info(
        self, mock_call, sample_master_cv, sample_job_requirements
    ):
        """Mock call_claude and verify PersonalInfo is built correctly."""
        # First call is _rewrite_summary, subsequent calls are _enhance_experience
        mock_call.side_effect = [
            "Tailored summary for the job.",
            json.dumps(["Enhanced bullet 1", "Enhanced bullet 2", "Enhanced bullet 3"]),
            json.dumps(["Enhanced bullet 1", "Enhanced bullet 2"]),
        ]

        tailor = CvTailor()
        result = tailor.tailor(sample_master_cv, sample_job_requirements, language="en")

        personal = result.personal
        assert personal.name == "Alessandro van Reusel"
        assert personal.title == "Software Engineer"
        assert personal.email == "alessandro@example.com"
        assert personal.phone == "+31 6 12345678"
        assert personal.location == "Amsterdam, Netherlands"
        assert personal.linkedin == "https://linkedin.com/in/alessandrovr"
        assert personal.photo_path == "data/photo.jpg"
