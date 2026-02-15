"""Tests for the experience selection strategy."""

import pytest

from src.analyzer.models import JobRequirements
from src.tailor.strategies import ExperienceStrategy


class TestSelectExperiences:
    """Test experience selection and ranking by relevance."""

    def test_selects_most_relevant(self, sample_job_requirements):
        experiences = [
            {
                "id": "exp-low",
                "company": "CoffeeCo",
                "title": {"en": "Barista"},
                "location": "Nowhere",
                "start_date": "2019-01",
                "end_date": "2020-01",
                "is_parent": False,
                "skills_used": ["Coffee"],
                "bullets": {"en": ["Made coffee"]},
            },
            {
                "id": "exp-high",
                "company": "CloudTech",
                "title": {"en": "Software Engineer"},
                "location": "Amsterdam",
                "start_date": "2024-01",
                "is_parent": False,
                "is_current": True,
                "skills_used": ["Python", "AWS", "Docker", "CI/CD"],
                "bullets": {"en": ["Built APIs"]},
            },
        ]

        strategy = ExperienceStrategy()
        selected = strategy.select(experiences, sample_job_requirements, max_experiences=2)

        ids = [e["id"] for e in selected]
        assert "exp-high" in ids


class TestSkipsParentEntries:
    """Test that parent/umbrella entries are excluded."""

    def test_parent_excluded(self, sample_job_requirements):
        experiences = [
            {
                "id": "parent",
                "company": "Umbrella",
                "title": {"en": "Consultant"},
                "location": "Paris",
                "start_date": "2021-01",
                "end_date": "2022-01",
                "is_parent": True,
                "skills_used": ["Python"],
                "bullets": {"en": []},
            },
            {
                "id": "child",
                "company": "Umbrella",
                "title": {"en": "Python Dev"},
                "location": "Paris",
                "start_date": "2021-06",
                "end_date": "2022-01",
                "is_parent": False,
                "skills_used": ["Python", "AWS"],
                "bullets": {"en": ["Coded"]},
            },
        ]

        strategy = ExperienceStrategy()
        selected = strategy.select(experiences, sample_job_requirements)
        ids = [e["id"] for e in selected]
        assert "parent" not in ids
        assert "child" in ids


class TestMaxExperiencesLimit:
    """Test that max_experiences is respected."""

    def test_limits_output(self, sample_job_requirements):
        experiences = [
            {
                "id": f"exp-{i}",
                "company": f"Co{i}",
                "title": {"en": f"Role{i}"},
                "location": "X",
                "start_date": f"202{i}-01",
                "end_date": f"202{i}-12",
                "is_parent": False,
                "skills_used": ["Python"],
                "bullets": {"en": [f"Did {i}"]},
            }
            for i in range(8)
        ]

        strategy = ExperienceStrategy()
        assert len(strategy.select(experiences, sample_job_requirements, max_experiences=3)) == 3
        assert len(strategy.select(experiences, sample_job_requirements, max_experiences=1)) == 1


class TestSelectCertifications:
    """Test certification selection."""

    def test_selects_relevant_certs(self, sample_job_requirements):
        certs = [
            {"name": "AWS SAA", "relevance_tags": ["AWS", "cloud"]},
            {"name": "PMP", "relevance_tags": ["management"]},
        ]

        strategy = ExperienceStrategy()
        result = strategy.select_certifications(certs, sample_job_requirements)

        # AWS cert should come first (more overlap)
        assert result[0]["name"] == "AWS SAA"
