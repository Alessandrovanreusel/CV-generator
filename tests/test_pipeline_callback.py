"""Tests for the CvPipeline progress_callback and last_requirements."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.main import CvPipeline


class TestPipelineCallback:

    def test_progress_callback_called_6_times(self, tmp_path, sample_master_cv, sample_job_requirements, sample_tailored_cv):
        """Verify that the progress callback is called once per pipeline stage."""
        job_text = "Senior Engineer at TestCorp\n" + ("Requirements: Python, AWS. " * 10)
        job_file = tmp_path / "job.txt"
        job_file.write_text(job_text, encoding="utf-8")
        output_pdf = tmp_path / "output.pdf"

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_job_requirements

        mock_tailor = MagicMock()
        mock_tailor.tailor.return_value = sample_tailored_cv

        mock_gen = MagicMock()
        mock_gen.generate.return_value = output_pdf

        callback = MagicMock()

        from src.config import Config
        config = Config()
        pipeline = CvPipeline(config)

        with patch("src.analyzer.job_analyzer.JobAnalyzer", return_value=mock_analyzer), \
             patch("src.tailor.cv_tailor.CvTailor", return_value=mock_tailor), \
             patch("src.generator.pdf_generator.PdfGenerator", return_value=mock_gen), \
             patch("src.utils.file_utils.load_json", return_value=sample_master_cv):
            result = pipeline.run(
                job_url=None,
                job_file=str(job_file),
                search=None,
                location="Amsterdam",
                language="en",
                no_photo=False,
                output=str(output_pdf),
                progress_callback=callback,
            )

        assert callback.call_count == 6
        calls = callback.call_args_list
        steps = [call.args[1] for call in calls]
        assert steps == [1, 2, 3, 4, 5, 6]

    def test_last_requirements_set_after_run(self, tmp_path, sample_master_cv, sample_job_requirements, sample_tailored_cv):
        """Verify that last_requirements is populated after a successful run."""
        job_text = "Senior Engineer at TestCorp\n" + ("Requirements: Python, AWS. " * 10)
        job_file = tmp_path / "job.txt"
        job_file.write_text(job_text, encoding="utf-8")
        output_pdf = tmp_path / "output.pdf"

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_job_requirements

        mock_tailor = MagicMock()
        mock_tailor.tailor.return_value = sample_tailored_cv

        mock_gen = MagicMock()
        mock_gen.generate.return_value = output_pdf

        from src.config import Config
        config = Config()
        pipeline = CvPipeline(config)

        assert pipeline.last_requirements is None

        with patch("src.analyzer.job_analyzer.JobAnalyzer", return_value=mock_analyzer), \
             patch("src.tailor.cv_tailor.CvTailor", return_value=mock_tailor), \
             patch("src.generator.pdf_generator.PdfGenerator", return_value=mock_gen), \
             patch("src.utils.file_utils.load_json", return_value=sample_master_cv):
            pipeline.run(
                job_url=None,
                job_file=str(job_file),
                search=None,
                location="Amsterdam",
                language="en",
                no_photo=False,
                output=str(output_pdf),
            )

        assert pipeline.last_requirements is not None
        assert pipeline.last_requirements.company == "TechCorp"
        assert pipeline.last_requirements.title == "Senior Software Engineer"

    def test_no_callback_no_error(self, tmp_path, sample_master_cv, sample_job_requirements, sample_tailored_cv):
        """Verify pipeline works without a callback (backward compatibility)."""
        job_text = "Senior Engineer at TestCorp\n" + ("Requirements: Python, AWS. " * 10)
        job_file = tmp_path / "job.txt"
        job_file.write_text(job_text, encoding="utf-8")
        output_pdf = tmp_path / "output.pdf"

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_job_requirements

        mock_tailor = MagicMock()
        mock_tailor.tailor.return_value = sample_tailored_cv

        mock_gen = MagicMock()
        mock_gen.generate.return_value = output_pdf

        from src.config import Config
        config = Config()
        pipeline = CvPipeline(config)

        with patch("src.analyzer.job_analyzer.JobAnalyzer", return_value=mock_analyzer), \
             patch("src.tailor.cv_tailor.CvTailor", return_value=mock_tailor), \
             patch("src.generator.pdf_generator.PdfGenerator", return_value=mock_gen), \
             patch("src.utils.file_utils.load_json", return_value=sample_master_cv):
            result = pipeline.run(
                job_url=None,
                job_file=str(job_file),
                search=None,
                location="Amsterdam",
                language="en",
                no_photo=False,
                output=str(output_pdf),
            )

        assert result == output_pdf
