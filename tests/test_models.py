"""Tests for Pydantic data models (JobRequirements and TailoredCV)."""

import pytest
from pydantic import ValidationError

from src.analyzer.models import JobRequirements
from src.tailor.models import (
    BilingualText,
    PersonalInfo,
    TailoredCertification,
    TailoredCV,
    TailoredEducation,
    TailoredExperience,
    TailoredLanguageSkill,
    TailoredProject,
    TailoredVolunteering,
)


class TestBilingualText:
    """Test the BilingualText model."""

    def test_bilingual_text_defaults(self):
        bt = BilingualText()
        assert bt.en == ""
        assert bt.fr == ""

    def test_bilingual_text_with_values(self):
        bt = BilingualText(en="Hello", fr="Bonjour")
        assert bt.en == "Hello"
        assert bt.fr == "Bonjour"

    def test_bilingual_text_serialization(self):
        bt = BilingualText(en="Hello", fr="Bonjour")
        data = bt.model_dump()
        assert data == {"en": "Hello", "fr": "Bonjour"}


class TestJobRequirementsModel:
    """Test the JobRequirements Pydantic model."""

    def test_defaults(self):
        req = JobRequirements()
        assert req.title == ""
        assert req.company == ""
        assert req.required_skills == []
        assert req.preferred_skills == []
        assert req.experience_years == 0
        assert req.language == "en"
        assert req.responsibilities == []

    def test_with_all_fields(self):
        req = JobRequirements(
            title="ML Engineer",
            company="AI Corp",
            location="San Francisco",
            description="Machine learning role",
            required_skills=["Python", "PyTorch"],
            preferred_skills=["Kubernetes"],
            experience_years=3,
            language="en",
            keywords=["deep learning"],
            responsibilities=["Train models"],
        )
        assert req.title == "ML Engineer"
        assert len(req.required_skills) == 2
        assert req.experience_years == 3

    def test_serialization_roundtrip(self):
        req = JobRequirements(title="Dev", company="Co", required_skills=["Python"])
        data = req.model_dump()
        req2 = JobRequirements(**data)
        assert req == req2


class TestTailoredCVModel:
    """Test the TailoredCV Pydantic model."""

    def test_minimal_tailored_cv(self):
        cv = TailoredCV(
            personal=PersonalInfo(
                name="Test User",
                title="Developer",
                email="test@test.com",
                phone="+1234",
                location="Amsterdam",
            ),
            summary="A summary.",
            experience=[],
            education=[],
            skills={},
            languages=[],
        )
        assert cv.personal.name == "Test User"
        assert cv.summary == "A summary."
        assert cv.target_language == "en"

    def test_full_tailored_cv(self, sample_tailored_cv):
        assert sample_tailored_cv.personal.name == "Alessandro van Reusel"
        assert len(sample_tailored_cv.experience) == 3
        assert len(sample_tailored_cv.education) == 1
        assert len(sample_tailored_cv.skills) == 3
        assert len(sample_tailored_cv.languages) == 2
        assert len(sample_tailored_cv.certifications) == 1
        assert len(sample_tailored_cv.projects) == 1
        assert len(sample_tailored_cv.volunteering) == 1

    def test_tailored_cv_serialization(self, sample_tailored_cv):
        data = sample_tailored_cv.model_dump()
        cv2 = TailoredCV(**data)
        assert cv2.personal.name == sample_tailored_cv.personal.name
        assert cv2.summary == sample_tailored_cv.summary
        assert len(cv2.experience) == len(sample_tailored_cv.experience)


class TestTailoredExperienceModel:
    """Test TailoredExperience model."""

    def test_experience_required_fields(self):
        exp = TailoredExperience(
            id="exp-1",
            company="TestCo",
            title="Dev",
            location="Amsterdam",
            start_date="2024-01",
            summary="Did things.",
            bullets=["Bullet 1"],
        )
        assert exp.id == "exp-1"
        assert exp.end_date is None
        assert exp.is_current is False
        assert exp.skills_used == []


class TestPersonalInfoModel:
    """Test PersonalInfo model."""

    def test_personal_info_required_fields(self):
        pi = PersonalInfo(
            name="Test",
            title="Dev",
            email="t@t.com",
            phone="+1",
            location="NL",
        )
        assert pi.linkedin == ""
        assert pi.photo_path == ""
