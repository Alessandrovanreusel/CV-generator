"""Tests for the CLI entry point using Click's CliRunner."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.main import main


class TestCliNoInput:
    """Test CLI behavior when no input is provided."""

    def test_no_input_shows_error(self):
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Provide at least one input" in result.output


class TestCliMultipleInputs:
    """Test CLI rejects multiple input modes."""

    def test_multiple_inputs_shows_error(self, tmp_path):
        f = tmp_path / "job.txt"
        f.write_text("x" * 100, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["--job-url", "https://example.com", "--job-file", str(f)])
        assert result.exit_code != 0
        assert "only one input" in result.output.lower()


class TestCliWithFile:
    """Test CLI generate from file with mocked pipeline."""

    def test_generate_from_file(self, tmp_path, sample_master_cv, sample_job_requirements, sample_tailored_cv):
        # Create job ad file
        job_text = "Senior Software Engineer at TechCorp\n" + ("Requirements: Python, AWS, Docker. " * 10)
        job_file = tmp_path / "job.txt"
        job_file.write_text(job_text, encoding="utf-8")
        output_pdf = tmp_path / "output.pdf"

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_job_requirements

        mock_tailor = MagicMock()
        mock_tailor.tailor.return_value = sample_tailored_cv

        mock_gen = MagicMock()
        mock_gen.generate.return_value = output_pdf

        with patch("src.analyzer.job_analyzer.JobAnalyzer", return_value=mock_analyzer) as mock_a_cls, \
             patch("src.tailor.cv_tailor.CvTailor", return_value=mock_tailor) as mock_t_cls, \
             patch("src.generator.pdf_generator.PdfGenerator", return_value=mock_gen) as mock_g_cls, \
             patch("src.utils.file_utils.load_json", return_value=sample_master_cv):

            runner = CliRunner()
            result = runner.invoke(main, [
                "--job-file", str(job_file),
                "--language", "en",
                "--output", str(output_pdf),
            ])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "CV generated" in result.output
