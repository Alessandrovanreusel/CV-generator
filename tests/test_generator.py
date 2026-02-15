"""Tests for the PDF generator module (without actual PDF generation)."""

import pytest
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from src.generator.pdf_generator import (
    LABELS,
    LANG_DOTS,
    PdfGenerator,
    TEMPLATES_DIR,
)


class TestFlattenSkills:
    """Test the _flatten_skills helper method."""

    def test_flatten_skills_limits_output(self):
        """Verify _flatten_skills respects the max_total parameter."""
        generator = PdfGenerator(include_photo=False)
        skills = {
            "Programming": ["Python", "Java", "TypeScript", "C++", "Kotlin"],
            "Cloud": ["AWS", "Docker", "Terraform", "Kubernetes"],
            "Frameworks": ["React", "FastAPI", "Django", "Angular"],
        }

        result = generator._flatten_skills(skills, max_total=5)
        assert len(result) == 5
        assert result[0] == "Python"

    def test_flatten_skills_no_duplicates(self):
        """Verify _flatten_skills does not include duplicates."""
        generator = PdfGenerator(include_photo=False)
        skills = {
            "Programming": ["Python", "Java"],
            "Scripting": ["Python", "Bash"],  # Python appears again
        }

        result = generator._flatten_skills(skills, max_total=10)
        assert result.count("Python") == 1
        assert "Bash" in result

    def test_flatten_skills_fewer_than_max(self):
        """When total skills < max_total, return all of them."""
        generator = PdfGenerator(include_photo=False)
        skills = {"Programming": ["Python", "Java"]}

        result = generator._flatten_skills(skills, max_total=12)
        assert result == ["Python", "Java"]


class TestLabelsExist:
    """Test that LABELS has both 'en' and 'fr' with required keys."""

    REQUIRED_KEYS = [
        "contact",
        "skills",
        "languages",
        "certifications",
        "volunteering",
        "summary",
        "experience",
        "education",
        "projects",
        "present",
    ]

    def test_labels_en_exist(self):
        """English labels should contain all required keys."""
        assert "en" in LABELS
        for key in self.REQUIRED_KEYS:
            assert key in LABELS["en"], f"Missing key '{key}' in LABELS['en']"
            assert isinstance(LABELS["en"][key], str)
            assert len(LABELS["en"][key]) > 0

    def test_labels_fr_exist(self):
        """French labels should contain all required keys."""
        assert "fr" in LABELS
        for key in self.REQUIRED_KEYS:
            assert key in LABELS["fr"], f"Missing key '{key}' in LABELS['fr']"
            assert isinstance(LABELS["fr"][key], str)
            assert len(LABELS["fr"][key]) > 0


class TestLangDotsMapping:
    """Test that LANG_DOTS has entries for all expected proficiency levels."""

    def test_lang_dots_english_levels(self):
        """All English proficiency levels should be mapped."""
        english_levels = ["Native", "Bilingual", "Fluent", "Intermediate", "Basic"]
        for level in english_levels:
            assert level in LANG_DOTS, f"Missing '{level}' in LANG_DOTS"
            assert 1 <= LANG_DOTS[level] <= 5

    def test_lang_dots_french_levels(self):
        """All French proficiency levels should be mapped, including 'Langue maternelle'."""
        french_levels = [
            "Natif",
            "Langue maternelle",
            "Bilingue",
            "Courant",
            "Intermédiaire",
            "Basique",
        ]
        for level in french_levels:
            assert level in LANG_DOTS, f"Missing '{level}' in LANG_DOTS"
            assert 1 <= LANG_DOTS[level] <= 5

    def test_lang_dots_native_is_five(self):
        """Native and Langue maternelle should map to 5 dots."""
        assert LANG_DOTS["Native"] == 5
        assert LANG_DOTS["Langue maternelle"] == 5
        assert LANG_DOTS["Bilingual"] == 5
        assert LANG_DOTS["Bilingue"] == 5


class TestTemplateRenders:
    """Test that the Jinja2 template renders with sample TailoredCV data."""

    def test_template_renders(self, sample_tailored_cv):
        """Render the CV template and verify it contains expected sections."""
        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,
        )
        template = env.get_template("cv_template.html")

        flat_skills = ["Python", "Java", "TypeScript", "AWS", "Docker"]
        skill_levels = {"Python": 90, "Java": 85, "TypeScript": 80, "AWS": 85, "Docker": 80}
        labels = LABELS["en"]

        html = template.render(
            cv=sample_tailored_cv,
            photo_base64=None,
            labels=labels,
            lang_dots=LANG_DOTS,
            skill_levels=skill_levels,
            flat_skills=flat_skills,
        )

        # Verify personal info
        assert "Alessandro van Reusel" in html
        assert "Software Engineer" in html
        assert "alessandro@example.com" in html

        # Verify summary
        assert "Experienced software engineer" in html

        # Verify experience
        assert "CloudTech BV" in html
        assert "DataSoft NV" in html
        assert "2024-01" in html

        # Verify education
        assert "Vrije Universiteit Amsterdam" in html
        assert "MSc Computer Science" in html

        # Verify skills in sidebar
        assert "Python" in html
        assert "AWS" in html

        # Verify languages
        assert "English" in html
        assert "French" in html

        # Verify section labels
        assert labels["summary"] in html
        assert labels["experience"] in html
        assert labels["education"] in html
        assert labels["skills"] in html

        # Verify certifications
        assert "AWS Solutions Architect Associate" in html

        # Verify projects
        assert "CV Generator" in html

        # Verify volunteering
        assert "Code for NL" in html
