"""End-to-end integration test for the CV-generator pipeline.

Exercises the full pipeline: scrape -> analyze -> tailor -> verify output.
All external calls (Claude API) are mocked.
"""

import json
from unittest.mock import MagicMock

import pytest

from src.analyzer.job_analyzer import JobAnalyzer
from src.analyzer.models import JobRequirements
from src.scraper.file_scraper import FileScraper
from src.tailor.cv_tailor import CvTailor
from src.tailor.models import TailoredCV
from src.utils.language import detect_language


def _make_mock_response(text: str) -> MagicMock:
    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = text
    mock_response.content = [mock_content_block]
    return mock_response


@pytest.mark.integration
class TestFullPipelineEnglish:
    """Full pipeline test in English."""

    def test_pipeline_english(self, tmp_path, sample_master_cv):
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

        # Step 4: Analyze (mock Claude)
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
        mock_analyzer_client = MagicMock()
        mock_analyzer_client.messages.create.return_value = _make_mock_response(json.dumps(analyzer_data))

        requirements = JobAnalyzer(client=mock_analyzer_client).analyze(scraped)
        assert isinstance(requirements, JobRequirements)
        assert requirements.title == "Senior Software Engineer"

        # Step 5: Tailor (mock Claude)
        mock_tailor_client = MagicMock()
        summary_resp = _make_mock_response("Experienced engineer specializing in Python and AWS.")
        bullets_resp = _make_mock_response(json.dumps(["Enhanced bullet 1", "Enhanced bullet 2", "Enhanced bullet 3"]))
        mock_tailor_client.messages.create.side_effect = [summary_resp, bullets_resp, bullets_resp]

        tailored = CvTailor(client=mock_tailor_client).tailor(sample_master_cv, requirements, language="en")

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

    def test_pipeline_french(self, tmp_path, sample_master_cv):
        job_text = (
            "Ingénieur Logiciel Senior - TechCorp\n"
            "Lieu: Amsterdam, Pays-Bas\n\n"
            "Exigences:\n"
            "- 5+ ans d'expérience en Python\n"
            "- Services cloud AWS\n"
            "- Docker et CI/CD\n"
            "- React et TypeScript\n\n"
            "Responsabilités:\n"
            "- Concevoir des microservices évolutifs\n"
            "- Collaborer avec les équipes produit\n"
        )
        job_file = tmp_path / "job_fr.txt"
        job_file.write_text(job_text, encoding="utf-8")

        scraped = FileScraper(str(job_file)).scrape()
        lang = detect_language(scraped)
        assert lang == "fr"

        analyzer_data = {
            "title": "Ingénieur Logiciel Senior",
            "company": "TechCorp",
            "location": "Amsterdam",
            "description": "Poste d'ingénieur backend.",
            "required_skills": ["Python", "AWS", "Docker"],
            "preferred_skills": [],
            "experience_years": 5,
            "language": "fr",
            "keywords": ["CI/CD", "microservices"],
            "responsibilities": ["Concevoir des microservices évolutifs"],
        }
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(json.dumps(analyzer_data))
        requirements = JobAnalyzer(client=mock_client).analyze(scraped)

        mock_tailor_client = MagicMock()
        summary_resp = _make_mock_response("Ingénieur expérimenté spécialisé en Python et AWS.")
        bullets_resp = _make_mock_response(json.dumps(["Bullet amélioré 1", "Bullet amélioré 2"]))
        mock_tailor_client.messages.create.side_effect = [summary_resp, bullets_resp, bullets_resp]

        tailored = CvTailor(client=mock_tailor_client).tailor(sample_master_cv, requirements, language="fr")

        assert isinstance(tailored, TailoredCV)
        assert tailored.target_language == "fr"
        assert tailored.personal.title == "Ingénieur Logiciel"
        assert len(tailored.experience) >= 1
