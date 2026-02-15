"""CV Generator CLI — Tailor your CV to match job ads automatically."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import click

from src.config import Config
from src.utils.file_utils import load_json


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
    # Validate input mode
    inputs = [job_url, job_file, search]
    provided = sum(1 for x in inputs if x is not None)
    if provided == 0:
        click.echo("Error: Provide at least one input: --job-url, --job-file, or --search", err=True)
        sys.exit(1)
    if provided > 1:
        click.echo("Error: Provide only one input mode at a time.", err=True)
        sys.exit(1)

    config = Config()

    # ── Step 1: Scrape job ad ──
    click.echo("📄 Scraping job ad...")
    try:
        job_text = _scrape(job_url, job_file, search, location)
    except Exception as e:
        click.echo(f"Error scraping job ad: {e}", err=True)
        sys.exit(1)

    if not job_text or len(job_text.strip()) < 50:
        click.echo("Error: Could not extract enough text from the job ad.", err=True)
        sys.exit(1)

    # ── Step 2: Detect language ──
    if language is None:
        from src.utils.language import detect_language
        language = detect_language(job_text)
        click.echo(f"🌐 Detected language: {language}")
    else:
        click.echo(f"🌐 Using language: {language}")

    # ── Step 3: Analyze job requirements ──
    click.echo("🔍 Analyzing job requirements...")
    config.validate_settings()
    try:
        from src.analyzer.job_analyzer import JobAnalyzer
        analyzer = JobAnalyzer(model=config.claude_model)
        requirements = analyzer.analyze(job_text)
        click.echo(f"   → {requirements.title} at {requirements.company}")
        click.echo(f"   → {len(requirements.required_skills)} required skills, {len(requirements.keywords)} keywords")
    except Exception as e:
        click.echo(f"Error analyzing job ad: {e}", err=True)
        sys.exit(1)

    # ── Step 4: Load master CV ──
    click.echo("📋 Loading master CV...")
    try:
        master_cv = load_json(config.master_cv_path)
    except FileNotFoundError:
        click.echo(f"Error: Master CV not found at {config.master_cv_path}", err=True)
        sys.exit(1)

    # ── Step 5: Tailor CV ──
    click.echo("✂️  Tailoring CV to match job requirements...")
    try:
        from src.tailor.cv_tailor import CvTailor
        tailor = CvTailor(model=config.claude_model)
        tailored_cv = tailor.tailor(master_cv, requirements, language)
    except Exception as e:
        click.echo(f"Error tailoring CV: {e}", err=True)
        sys.exit(1)

    # ── Step 6: Generate PDF ──
    if output is None:
        company_slug = requirements.company.replace(" ", "_")[:30] or "Unknown"
        today = date.today().strftime("%Y%m%d")
        output = str(config.output_dir / f"CV_Alessandro_van_Reusel_{company_slug}_{today}.pdf")

    click.echo(f"📝 Generating PDF → {output}")
    try:
        from src.generator.pdf_generator import PdfGenerator
        generator = PdfGenerator(include_photo=not no_photo)
        result_path = generator.generate(
            tailored_cv,
            output,
            photo_path=config.photo_path,
        )
        click.echo(f"✅ CV generated successfully: {result_path}")
    except Exception as e:
        click.echo(f"Error generating PDF: {e}", err=True)
        sys.exit(1)


def _scrape(
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
        results = BoardScraper().search(search, location=location, results_wanted=5)
        if not results:
            raise RuntimeError(f"No results found for '{search}' in {location}")

        # Show results and pick the first with a description
        click.echo(f"   Found {len(results)} results:")
        for i, r in enumerate(results, 1):
            click.echo(f"   {i}. {r['title']} at {r['company']} ({r['location']})")

        for r in results:
            if r.get("description") and len(r["description"]) > 100:
                click.echo(f"   → Using: {r['title']} at {r['company']}")
                return r["description"]

        # If no descriptions, use URL scraper on the first result with a URL
        for r in results:
            if r.get("job_url") and r["job_url"] != "nan":
                click.echo(f"   → Fetching full description from: {r['job_url']}")
                from src.scraper.url_scraper import UrlScraper
                return UrlScraper(r["job_url"]).scrape()

        raise RuntimeError("No job ad descriptions or URLs found in search results.")

    raise RuntimeError("No input provided.")


if __name__ == "__main__":
    main()
