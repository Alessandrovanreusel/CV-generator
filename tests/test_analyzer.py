"""Tests for the job analyzer module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.analyzer.job_analyzer import JobAnalyzer
from src.analyzer.models import JobRequirements


def _make_mock_response(text: str) -> MagicMock:
    """Create a mock Anthropic API response with the given text content."""
    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = text
    mock_response.content = [mock_content_block]
    return mock_response


class TestJobAnalyzerReturnsRequirements:
    """Test that the analyzer correctly parses a valid JSON response."""

    def test_job_analyzer_returns_requirements(self, sample_job_text):
        """Mock the Anthropic client, return valid JSON, and verify parsing."""
        mock_client = MagicMock()
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
        mock_client.messages.create.return_value = _make_mock_response(
            json.dumps(response_data)
        )

        analyzer = JobAnalyzer(client=mock_client)
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
        mock_client.messages.create.assert_called_once()


class TestJobAnalyzerStripsMarkdownFences:
    """Test that markdown code fences are stripped before parsing."""

    def test_job_analyzer_strips_markdown_fences(self, sample_job_text):
        """Response wrapped in ```json``` fences should still parse correctly."""
        mock_client = MagicMock()
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
        fenced_json = f"```json\n{json.dumps(response_data)}\n```"
        mock_client.messages.create.return_value = _make_mock_response(fenced_json)

        analyzer = JobAnalyzer(client=mock_client)
        result = analyzer.analyze(sample_job_text)

        assert isinstance(result, JobRequirements)
        assert result.title == "Data Engineer"
        assert result.company == "DataCorp"
        assert "Python" in result.required_skills


class TestJobAnalyzerRetryOnFailure:
    """Test the retry mechanism when API calls fail."""

    @patch("src.analyzer.job_analyzer.time.sleep", return_value=None)
    def test_job_analyzer_retry_on_failure(self, mock_sleep, sample_job_text):
        """First call raises an error, second call succeeds -- verify retry works."""
        import anthropic

        mock_client = MagicMock()
        response_data = {
            "title": "Backend Engineer",
            "company": "RetryCorp",
            "location": "Remote",
            "description": "Backend role.",
            "required_skills": ["Python"],
            "preferred_skills": [],
            "experience_years": 2,
            "language": "en",
            "keywords": [],
            "responsibilities": [],
        }
        success_response = _make_mock_response(json.dumps(response_data))

        # First call raises RateLimitError, second call succeeds
        mock_client.messages.create.side_effect = [
            anthropic.RateLimitError(
                message="Rate limited",
                response=MagicMock(status_code=429, headers={}),
                body=None,
            ),
            success_response,
        ]

        analyzer = JobAnalyzer(client=mock_client)
        result = analyzer.analyze(sample_job_text)

        assert isinstance(result, JobRequirements)
        assert result.title == "Backend Engineer"
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once()


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
