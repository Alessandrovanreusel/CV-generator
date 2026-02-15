"""End-to-end integration test for the CV-generator pipeline.

Mocks the Claude CLI to avoid network calls.
Runs: scrape -> analyze -> tailor -> verify TailoredCV output.
Skips PDF generation (WeasyPrint may not be installed).
"""

import json
from unittest.mock import patch

import pytest

from src.analyzer.job_analyzer import JobAnalyzer
from src.analyzer.models import JobRequirements
from src.scraper.file_scraper import FileScraper
from src.tailor.cv_tailor import CvTailor
from src.tailor.models import TailoredCV


class TestFullPipelineWithFile:
    """End-to-end test: file scrape -> analyze -> tailor -> verify output."""

    @patch("src.tailor.cv_tailor.call_claude")
    @patch("src.analyzer.job_analyzer.call_claude")
    def test_full_pipeline_with_file(self, mock_analyzer_call, mock_tailor_call, tmp_path, sample_master_cv):
        """Run the full pipeline with a temp job ad file and mocked Claude CLI."""
        # ------------------------------------------------------------------
        # Step 1: Create a temporary job ad file
        # ------------------------------------------------------------------
        job_ad_text = (
            "Senior Software Engineer - TechCorp\n"
            "Location: Amsterdam, Netherlands\n"
            "Type: Full-time\n\n"
            "About the Role\n\n"
            "TechCorp is looking for a Senior Software Engineer to join our "
            "platform team in Amsterdam. You will design and build backend "
            "services and cloud infrastructure for our analytics platform.\n\n"
            "Requirements\n\n"
            "- 5+ years of professional software development experience\n"
            "- Strong proficiency in Python with REST API experience\n"
            "- Solid understanding of AWS cloud services\n"
            "- Experience with Docker and CI/CD pipelines\n"
            "- Experience with React and TypeScript\n"
            "- Knowledge of PostgreSQL\n"
            "- Proficiency with Git\n\n"
            "Responsibilities\n\n"
            "- Design and implement scalable microservices\n"
            "- Collaborate with product managers and engineers\n"
            "- Write clean, well-tested code\n"
        )
        job_file = tmp_path / "job_ad.txt"
        job_file.write_text(job_ad_text, encoding="utf-8")

        # ------------------------------------------------------------------
        # Step 2: Scrape the job ad
        # ------------------------------------------------------------------
        scraper = FileScraper(str(job_file))
        scraped_text = scraper.scrape()
        assert len(scraped_text) > 50
        assert "Senior Software Engineer" in scraped_text

        # ------------------------------------------------------------------
        # Step 3: Analyze the job ad (mock Claude CLI)
        # ------------------------------------------------------------------
        analyzer_requirements = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "location": "Amsterdam, Netherlands",
            "description": "Backend engineer building cloud infrastructure and APIs.",
            "required_skills": ["Python", "AWS", "Docker", "React", "TypeScript", "PostgreSQL", "Git"],
            "preferred_skills": ["Kubernetes"],
            "experience_years": 5,
            "language": "en",
            "keywords": ["CI/CD", "microservices", "REST API"],
            "responsibilities": [
                "Design and implement scalable microservices",
                "Collaborate with product managers and engineers",
                "Write clean, well-tested code",
            ],
        }

        mock_analyzer_call.return_value = json.dumps(analyzer_requirements)

        analyzer = JobAnalyzer()
        requirements = analyzer.analyze(scraped_text)

        assert isinstance(requirements, JobRequirements)
        assert requirements.title == "Senior Software Engineer"
        assert requirements.company == "TechCorp"
        assert "Python" in requirements.required_skills

        # ------------------------------------------------------------------
        # Step 4: Tailor the CV (mock Claude CLI for summary and bullets)
        # ------------------------------------------------------------------
        mock_tailor_call.side_effect = [
            "Seasoned software engineer with 5+ years of experience in Python, "
            "AWS, and scalable microservices development.",
            json.dumps([
                "Developed high-performance REST APIs using Python and FastAPI",
                "Architected and deployed AWS cloud infrastructure with Terraform",
                "Built automated CI/CD pipelines with GitHub Actions",
            ]),
            json.dumps([
                "Built responsive React front-end components with TypeScript",
                "Optimized PostgreSQL databases and complex query performance",
            ]),
            # Skills curation call
            json.dumps({
                "Programming": ["Python", "TypeScript", "Java"],
                "Cloud": ["AWS", "Docker", "Kubernetes", "Terraform"],
                "Frameworks": ["React", "FastAPI", "Django"],
            }),
        ]

        tailor = CvTailor()
        tailored_cv = tailor.tailor(
            sample_master_cv, requirements, language="en"
        )

        # ------------------------------------------------------------------
        # Step 5: Verify the TailoredCV output
        # ------------------------------------------------------------------
        assert isinstance(tailored_cv, TailoredCV)

        # Personal info
        assert tailored_cv.personal.name == "Alessandro van Reusel"
        assert tailored_cv.personal.title == "Software Engineer"
        assert tailored_cv.personal.email == "alessandro@example.com"
        assert tailored_cv.personal.location == "Amsterdam, Netherlands"

        # Summary was rewritten
        assert "software engineer" in tailored_cv.summary.lower()
        assert len(tailored_cv.summary) > 20

        # Experiences are present (parent entry should be excluded)
        assert len(tailored_cv.experience) >= 1
        exp_companies = [e.company for e in tailored_cv.experience]
        assert "CloudTech BV" in exp_companies
        # Parent entry should not appear
        assert all(e.id != "exp-parent" for e in tailored_cv.experience)

        # Each experience has bullets
        for exp in tailored_cv.experience:
            assert len(exp.bullets) > 0
            assert exp.title  # title is resolved to string
            assert exp.company

        # Education
        assert len(tailored_cv.education) == 1
        assert tailored_cv.education[0].institution == "Vrije Universiteit Amsterdam"
        assert tailored_cv.education[0].degree == "MSc Computer Science"
        assert "Data Structures" in tailored_cv.education[0].details

        # Skills are present and reordered
        assert len(tailored_cv.skills) > 0
        assert "Cloud" in tailored_cv.skills or "Programming" in tailored_cv.skills

        # Languages
        assert len(tailored_cv.languages) == 2
        lang_names = [l.language for l in tailored_cv.languages]
        assert "English" in lang_names

        # Certifications
        assert len(tailored_cv.certifications) >= 1
        assert tailored_cv.certifications[0].name == "AWS Solutions Architect Associate"

        # Projects
        assert len(tailored_cv.projects) == 1
        assert tailored_cv.projects[0].name == "CV Generator"

        # Volunteering
        assert len(tailored_cv.volunteering) == 1
        assert tailored_cv.volunteering[0].organization == "Code for NL"

        # Target language
        assert tailored_cv.target_language == "en"
