"""End-to-end integration test for the CV-generator pipeline.

Exercises the full pipeline: scrape -> analyze -> tailor -> verify output.
All external calls (Claude CLI) are mocked.
"""

import json
from unittest.mock import patch

import pytest

from src.analyzer.job_analyzer import JobAnalyzer
from src.analyzer.models import JobRequirements
from src.scraper.file_scraper import FileScraper
from src.tailor.cv_tailor import CvTailor
from src.tailor.models import TailoredCV
from src.utils.language import detect_language


@pytest.mark.integration
class TestFullPipelineEnglish:
    """Full pipeline test in English."""

    @patch("src.tailor.cv_tailor.call_claude")
    @patch("src.analyzer.job_analyzer.call_claude")
    def test_pipeline_english(self, mock_analyzer_call, mock_tailor_call, tmp_path, sample_master_cv):
        # Step 1: Create job ad file
        job_text = (
            "Senior Software Engineer - TechCorp\n"
            "Location: Amsterdam, Netherlands\n\n"
            "Requirements:\n"
            "- 5+ years of Python\n"
            "- AWS cloud services\n"
            "- Docker and CI/CD\n"
            "- React and TypeScript\n\n"
            "Responsibilities:\n"
            "- Design scalable microservices\n"
            "- Collaborate with product teams\n"
            "- Write well-tested code\n"
        )
        job_file = tmp_path / "job.txt"
        job_file.write_text(job_text, encoding="utf-8")

        # Step 2: Scrape
        scraped = FileScraper(str(job_file)).scrape()
        assert len(scraped) > 50

        # Step 3: Detect language
        lang = detect_language(scraped)
        assert lang == "en"

        # Step 4: Analyze (mock Claude CLI)
        analyzer_data = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "location": "Amsterdam",
            "description": "Backend engineer role.",
            "required_skills": ["Python", "AWS", "Docker", "React", "TypeScript"],
            "preferred_skills": ["Kubernetes"],
            "experience_years": 5,
            "language": "en",
            "keywords": ["CI/CD", "microservices"],
            "responsibilities": ["Design scalable microservices", "Write well-tested code"],
        }
        mock_analyzer_call.return_value = json.dumps(analyzer_data)

        requirements = JobAnalyzer().analyze(scraped)
        assert isinstance(requirements, JobRequirements)
        assert requirements.title == "Senior Software Engineer"

        # Step 5: Tailor (mock Claude CLI)
        mock_tailor_call.side_effect = [
            "Experienced engineer specializing in Python and AWS.",
            json.dumps(["Enhanced bullet 1", "Enhanced bullet 2", "Enhanced bullet 3"]),
            json.dumps(["Enhanced bullet 1", "Enhanced bullet 2"]),
        ]

        tailored = CvTailor().tailor(sample_master_cv, requirements, language="en")

        # Step 6: Verify output
        assert isinstance(tailored, TailoredCV)
        assert tailored.personal.name == "Alessandro van Reusel"
        assert tailored.target_language == "en"
        assert len(tailored.experience) >= 1
        assert all(e.id != "exp-parent" for e in tailored.experience)
        assert len(tailored.summary) > 10
        assert len(tailored.education) == 1
        assert len(tailored.skills) > 0
        assert len(tailored.languages) == 2


@pytest.mark.integration
class TestFullPipelineFrench:
    """Full pipeline test in French."""

    @patch("src.tailor.cv_tailor.call_claude")
    @patch("src.analyzer.job_analyzer.call_claude")
    def test_pipeline_french(self, mock_analyzer_call, mock_tailor_call, tmp_path, sample_master_cv):
        job_text = (
            "Ingenieur Logiciel Senior - TechCorp\n"
            "Lieu: Amsterdam, Pays-Bas\n\n"
            "Exigences:\n"
            "- 5+ ans d'experience en Python\n"
            "- Services cloud AWS\n"
            "- Docker et CI/CD\n"
            "- React et TypeScript\n\n"
            "Responsabilites:\n"
            "- Concevoir des microservices evolutifs\n"
            "- Collaborer avec les equipes produit\n"
        )
        job_file = tmp_path / "job_fr.txt"
        job_file.write_text(job_text, encoding="utf-8")

        scraped = FileScraper(str(job_file)).scrape()
        lang = detect_language(scraped)
        assert lang == "fr"

        analyzer_data = {
            "title": "Ingenieur Logiciel Senior",
            "company": "TechCorp",
            "location": "Amsterdam",
            "description": "Poste d'ingenieur backend.",
            "required_skills": ["Python", "AWS", "Docker"],
            "preferred_skills": [],
            "experience_years": 5,
            "language": "fr",
            "keywords": ["CI/CD", "microservices"],
            "responsibilities": ["Concevoir des microservices evolutifs"],
        }
        mock_analyzer_call.return_value = json.dumps(analyzer_data)
        requirements = JobAnalyzer().analyze(scraped)

        mock_tailor_call.side_effect = [
            "Ingenieur experimente specialise en Python et AWS.",
            json.dumps(["Bullet ameliore 1", "Bullet ameliore 2", "Bullet ameliore 3"]),
            json.dumps(["Bullet ameliore 1", "Bullet ameliore 2"]),
        ]

        tailored = CvTailor().tailor(sample_master_cv, requirements, language="fr")

        assert isinstance(tailored, TailoredCV)
        assert tailored.target_language == "fr"
        assert "Logiciel" in tailored.personal.title
        assert len(tailored.experience) >= 1
