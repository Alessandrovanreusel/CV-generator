"""CV Generator CLI - Tailor your CV to match job ads automatically."""
from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path

import click

from src.config import Config
from src.utils.file_utils import load_json


class CvPipeline:
    """Orchestrates the full CV generation pipeline."""

    def __init__(self, config: Config):
        self.config = config
        self.last_requirements = None

    def run(
        self,
        job_url: str | None,
        job_file: str | None,
        search: str | None,
        location: str,
        language: str | None,
        no_photo: bool,
        output: str | None,
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> Path:
        """Execute the full pipeline and return the output PDF path."""
        self.progress_callback = progress_callback

        # Step 1: Scrape
        click.echo("[1/6] Scraping job ad...")
        if self.progress_callback:
            self.progress_callback("Scraping job ad", 1)
        job_text = self._scrape(job_url, job_file, search, location)

        if not job_text or len(job_text.strip()) < 50:
            raise RuntimeError("Could not extract enough text from the job ad.")

        # Step 2: Detect language
        if self.progress_callback:
            self.progress_callback("Detecting language", 2)
        language = self._detect_language(job_text, language)

        # Step 3: Analyze
        click.echo("[3/6] Analyzing job requirements...")
        if self.progress_callback:
            self.progress_callback("Analyzing job requirements", 3)
        self.config.validate_settings()
        requirements = self._analyze(job_text)
        self.last_requirements = requirements
        click.echo(f"   -> {requirements.title} at {requirements.company}")
        click.echo(f"   -> {len(requirements.required_skills)} required skills, {len(requirements.keywords)} keywords")

        # Step 4: Load master CV
        click.echo("[4/6] Loading master CV...")
        if self.progress_callback:
            self.progress_callback("Loading master CV", 4)
        master_cv = self._load_cv()

        # Step 5: Tailor
        click.echo("[5/6] Tailoring CV to match job requirements...")
        if self.progress_callback:
            self.progress_callback("Tailoring CV", 5)
        tailored_cv = self._tailor(master_cv, requirements, language)

        # Step 6: Prepare output and generate PDF
        output_path = self._prepare_output(requirements, job_url, job_file, job_text, output)
        click.echo(f"[6/6] Generating PDF -> {output_path}")
        if self.progress_callback:
            self.progress_callback("Generating PDF", 6)
        result_path = self._generate(tailored_cv, output_path, no_photo)
        click.echo(f"Done! CV generated: {result_path}")
        return result_path

    def _scrape(
        self,
        job_url: str | None,
        job_file: str | None,
        search: str | None,
        location: str,
    ) -> str:
        """Scrape job ad text from the appropriate source."""
        if job_file:
            from src.scraper.file_scraper import FileScraper
            return FileScraper(job_file).scrape()

        if job_url:
            from src.scraper.url_scraper import UrlScraper
            return UrlScraper(job_url).scrape()

        if search:
            from src.scraper.board_scraper import BoardScraper
            results = BoardScraper(country=self.config.board_country).search(
                search, location=location, results_wanted=5
            )
            if not results:
                raise RuntimeError(f"No results found for '{search}' in {location}")

            click.echo(f"   Found {len(results)} results:")
            for i, r in enumerate(results, 1):
                click.echo(f"   {i}. {r['title']} at {r['company']} ({r['location']})")

            for r in results:
                if r.get("description") and len(r["description"]) > 100:
                    click.echo(f"   ->Using: {r['title']} at {r['company']}")
                    return r["description"]

            for r in results:
                if r.get("job_url") and r["job_url"] != "nan":
                    click.echo(f"   ->Fetching full description from: {r['job_url']}")
                    from src.scraper.url_scraper import UrlScraper
                    return UrlScraper(r["job_url"]).scrape()

            raise RuntimeError("No job ad descriptions or URLs found in search results.")

        raise RuntimeError("No input provided.")

    def _detect_language(self, job_text: str, language: str | None) -> str:
        """Detect or confirm the job ad language."""
        if language is None:
            from src.utils.language import detect_language
            language = detect_language(job_text)
            click.echo(f"[2/6] Detected language: {language}")
        else:
            click.echo(f"[2/6] Using language: {language}")
        return language

    def _analyze(self, job_text: str):
        """Analyze job ad text and return structured requirements."""
        from src.analyzer.job_analyzer import JobAnalyzer
        analyzer = JobAnalyzer()
        return analyzer.analyze(job_text)

    def _load_cv(self) -> dict:
        """Load the master CV from disk."""
        return load_json(self.config.master_cv_path)

    def _tailor(self, master_cv: dict, requirements, language: str):
        """Tailor the master CV to match job requirements."""
        from src.tailor.cv_tailor import CvTailor
        tailor = CvTailor()
        return tailor.tailor(master_cv, requirements, language)

    def _prepare_output(
        self,
        requirements,
        job_url: str | None,
        job_file: str | None,
        job_text: str,
        output: str | None,
    ) -> str:
        """Prepare output directory and return the output PDF path."""
        import re
        company_slug = re.sub(r'[^\w\-]', '_', requirements.company)[:30] or "Unknown"
        today = date.today().strftime("%Y%m%d")

        if output is None:
            job_folder = self.config.output_dir / f"{company_slug}_{today}"
            job_folder.mkdir(parents=True, exist_ok=True)

            if job_file:
                src_file = Path(job_file)
                shutil.copy2(src_file, job_folder / src_file.name)
            elif job_text:
                job_ad_path = job_folder / f"{company_slug}_job_ad.txt"
                job_ad_path.write_text(job_text, encoding="utf-8")

            return str(job_folder / "CV_Alessandro_van_Reusel.pdf")
        else:
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if job_file:
                src_file = Path(job_file)
                dest_file = out_path.parent / src_file.name
                if src_file.resolve() != dest_file.resolve():
                    shutil.copy2(src_file, dest_file)
            return output

    def _generate(self, tailored_cv, output_path: str, no_photo: bool) -> Path:
        """Generate the PDF CV."""
        from src.generator.pdf_generator import PdfGenerator
        generator = PdfGenerator(include_photo=not no_photo)
        return generator.generate(
            tailored_cv,
            output_path,
            photo_path=self.config.photo_path,
        )


@click.command()
@click.option("--job-url", type=str, default=None, help="URL of the job ad to analyze.")
@click.option("--job-file", type=click.Path(exists=True), default=None, help="Path to a local job ad file (PDF, HTML, TXT).")
@click.option("--search", type=str, default=None, help="Search term for job board scraping.")
@click.option("--location", type=str, default="Amsterdam", help="Location for job board search.")
@click.option("--language", type=click.Choice(["en", "fr"]), default=None, help="Force output language (default: auto-detect).")
@click.option("--no-photo", is_flag=True, default=False, help="Exclude photo from the PDF.")
@click.option("--output", type=click.Path(), default=None, help="Custom output PDF path.")
def main(
    job_url: str | None,
    job_file: str | None,
    search: str | None,
    location: str,
    language: str | None,
    no_photo: bool,
    output: str | None,
) -> None:
    """Generate a tailored CV from a job ad.

    Provide exactly one input: --job-url, --job-file, or --search.
    """
    inputs = [job_url, job_file, search]
    provided = sum(1 for x in inputs if x is not None)
    if provided == 0:
        click.echo("Error: Provide at least one input: --job-url, --job-file, or --search", err=True)
        sys.exit(1)
    if provided > 1:
        click.echo("Error: Provide only one input mode at a time.", err=True)
        sys.exit(1)

    config = Config()
    pipeline = CvPipeline(config)
    try:
        pipeline.run(job_url, job_file, search, location, language, no_photo, output)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
