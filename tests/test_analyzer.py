"""Tests for the job analyzer module."""

import json
from unittest.mock import patch

import pytest

from src.analyzer.job_analyzer import JobAnalyzer
from src.analyzer.models import JobRequirements


class TestJobAnalyzerReturnsRequirements:
    """Test that the analyzer correctly parses a valid JSON response."""

    @patch("src.analyzer.job_analyzer.call_claude")
    def test_job_analyzer_returns_requirements(self, mock_call, sample_job_text):
        """Mock call_claude, return valid JSON, and verify parsing."""
        response_data = {
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "location": "Amsterdam, Netherlands",
            "description": "Backend-focused senior engineer role.",
            "required_skills": ["Python", "AWS", "Docker"],
            "preferred_skills": ["Kubernetes"],
            "experience_years": 5,
            "language": "en",
            "keywords": ["CI/CD", "microservices"],
            "responsibilities": ["Design scalable APIs"],
        }
        mock_call.return_value = json.dumps(response_data)

        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_job_text)

        assert isinstance(result, JobRequirements)
        assert result.title == "Senior Software Engineer"
        assert result.company == "TechCorp"
        assert result.location == "Amsterdam, Netherlands"
        assert "Python" in result.required_skills
        assert "AWS" in result.required_skills
        assert result.experience_years == 5
        assert result.language == "en"
        assert "CI/CD" in result.keywords
        mock_call.assert_called_once()


class TestJobAnalyzerStripsMarkdownFences:
    """Test that markdown code fences are stripped before parsing."""

    @patch("src.analyzer.job_analyzer.call_claude")
    def test_job_analyzer_strips_markdown_fences(self, mock_call, sample_job_text):
        """Response wrapped in ```json``` fences should still parse correctly."""
        response_data = {
            "title": "Data Engineer",
            "company": "DataCorp",
            "location": "Berlin",
            "description": "Data pipeline engineer.",
            "required_skills": ["Python", "SQL"],
            "preferred_skills": [],
            "experience_years": 3,
            "language": "en",
            "keywords": ["ETL"],
            "responsibilities": ["Build data pipelines"],
        }
        mock_call.return_value = f"```json\n{json.dumps(response_data)}\n```"

        analyzer = JobAnalyzer()
        result = analyzer.analyze(sample_job_text)

        assert isinstance(result, JobRequirements)
        assert result.title == "Data Engineer"
        assert result.company == "DataCorp"
        assert "Python" in result.required_skills


class TestJobAnalyzerShortText:
    """Test that short text raises an error."""

    def test_job_analyzer_rejects_short_text(self):
        """Text shorter than 50 characters should be rejected."""
        analyzer = JobAnalyzer()
        with pytest.raises(ValueError, match="too short"):
            analyzer.analyze("Short text")


class TestJobAnalyzerCliError:
    """Test that CLI errors are propagated."""

    @patch("src.analyzer.job_analyzer.call_claude")
    def test_job_analyzer_cli_error(self, mock_call, sample_job_text):
        """RuntimeError from call_claude should propagate."""
        mock_call.side_effect = RuntimeError("Claude CLI failed")

        analyzer = JobAnalyzer()
        with pytest.raises(RuntimeError, match="Claude CLI failed"):
            analyzer.analyze(sample_job_text)


class TestJobRequirementsModel:
    """Test the JobRequirements Pydantic model."""

    def test_job_requirements_model_defaults(self):
        """JobRequirements should have sensible defaults."""
        req = JobRequirements()
        assert req.title == ""
        assert req.company == ""
        assert req.location == ""
        assert req.experience_years == 0
        assert req.language == "en"
        assert req.required_skills == []
        assert req.preferred_skills == []
        assert req.keywords == []
        assert req.responsibilities == []

    def test_job_requirements_model_with_fields(self):
        """JobRequirements should accept and store all fields."""
        req = JobRequirements(
            title="ML Engineer",
            company="AI Corp",
            location="San Francisco",
            description="Machine learning role",
            required_skills=["Python", "PyTorch", "TensorFlow"],
            preferred_skills=["Kubernetes", "MLflow"],
            experience_years=3,
            language="en",
            keywords=["deep learning", "NLP", "transformers"],
            responsibilities=["Train models", "Deploy to production"],
        )
        assert req.title == "ML Engineer"
        assert len(req.required_skills) == 3
        assert "PyTorch" in req.required_skills
        assert req.experience_years == 3
        assert "deep learning" in req.keywords
        assert len(req.responsibilities) == 2
