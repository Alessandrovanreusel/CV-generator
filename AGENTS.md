# CV Generator - Codebase Knowledge Base

## Architecture

Pipeline: Input → Scraper → Raw Text → Analyzer (Claude API) → JobRequirements → Tailor (Claude API + rules) → TailoredCV → PDF Generator (Jinja2 + WeasyPrint) → Stylish ATS PDF

Inter-module contracts:
- `src/analyzer/models.py` → JobRequirements (Pydantic)
- `src/tailor/models.py` → TailoredCV (Pydantic)

## Master CV

`data/master_cv.json` is READ-ONLY during normal operation.
Contains ALL experience in EN + FR. Tailor selects and reshapes; never adds fake data.

Key design:
- Experience parent/child: Capgemini umbrella → sub-projects (TomTom, Geppetto, WFP, Quantum)
- Skills categorized: programming, frontend, cloud, AI, testing, data, tools
- Bilingual: `{"en": "...", "fr": "..."}`
- Each entry has `id` field for reference

## Dependencies

- anthropic — Claude API
- click — CLI
- pydantic — data models
- python-dotenv — env loading
- weasyprint + jinja2 — HTML/CSS → PDF
- beautifulsoup4 + lxml — HTML parsing
- PyMuPDF (fitz) — PDF text extraction
- requests — HTTP
- langdetect — language detection
- python-jobspy — job board scraping
- playwright — optional, JS-rendered pages

## Testing

- pytest with fixtures in conftest.py
- Mock external calls (anthropic, requests, playwright, jobspy)
- Test fixtures in tests/fixtures/
- Integration tests skip by default

## Platform

- Windows 11 with Git Bash
- Use pathlib.Path for all file operations
- Forward slashes in Python code

## Discovered Patterns

(Grows as iterations complete stories)
