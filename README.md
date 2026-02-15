# CV Generator

A Python CLI tool that ingests job ads, analyzes them with Claude AI, tailors a master CV to match, and generates a stylish ATS-optimized PDF in English or French.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Testing](#testing)
- [Project Structure](#project-structure)

## Features

- **Multi-source input**: Job ads from local files (PDF, HTML, TXT), URLs, or job board search (LinkedIn, Indeed, Glassdoor)
- **AI-powered analysis**: Extracts structured requirements using Claude API
- **Smart tailoring**: Rewrites summaries, enhances bullet points, reorders skills to match job requirements
- **Bilingual**: Generates CVs in English or French with automatic language detection
- **Stylish PDF**: Two-column layout with sidebar, circular photo, skill bars, and ATS-optimized semantic HTML
- **Never fabricates**: Only uses real experience from your master CV

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com)
- WeasyPrint system dependencies (GTK3 on Windows/macOS — see [WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html))
- (Optional) Playwright for JS-rendered pages: `pip install playwright && playwright install chromium`

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd cv-generator

# Install dependencies
pip install -e ".[dev]"

# (Optional) Install Playwright for JavaScript-rendered job pages
pip install playwright && playwright install chromium
```

## Configuration

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
OUTPUT_DIR=output
LOG_LEVEL=INFO
```

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) | — |
| `OUTPUT_DIR` | Directory for generated PDFs | `output` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Usage

### Generate from a local file

```bash
python -m src.main --job-file path/to/job_ad.txt
python -m src.main --job-file path/to/job_ad.pdf
python -m src.main --job-file path/to/job_ad.html
```

### Generate from a URL

```bash
python -m src.main --job-url "https://example.com/job-posting"
```

### Search job boards

```bash
python -m src.main --search "Python developer" --location "Amsterdam"
```

### Additional options

```bash
# Force output language (default: auto-detect)
python -m src.main --job-file job.txt --language fr

# Specify output path
python -m src.main --job-file job.txt --output my_cv.pdf

# Exclude photo from PDF
python -m src.main --job-file job.txt --no-photo
```

## Architecture

```
Job Ad Input ──► Scraper ──► Raw Text ──► Analyzer (Claude API) ──► JobRequirements
                                                                          │
Master CV (JSON) ──────────────────► Tailor (Claude API + Rules) ◄────────┘
                                            │
                                      TailoredCV
                                            │
                                  PDF Generator (Jinja2 + WeasyPrint)
                                            │
                                      Stylish ATS PDF
```

### Modules

| Module | Description |
|--------|-------------|
| `src/scraper/` | Extracts text from files, URLs, or job boards |
| `src/analyzer/` | Sends text to Claude API, returns structured `JobRequirements` |
| `src/tailor/` | Rewrites summary, enhances bullets, reorders skills using Claude + rules |
| `src/generator/` | Renders HTML template with Jinja2, converts to PDF with WeasyPrint |
| `src/utils/` | Language detection, file helpers |
| `src/config.py` | Settings loaded from `.env` |
| `src/main.py` | Click CLI entry point |

### Data Models

- **`JobRequirements`** (Pydantic): Structured output from job analysis — title, company, skills, responsibilities
- **`TailoredCV`** (Pydantic): Final CV data ready for PDF rendering — personal info, summary, experiences, skills, education

## Testing

```bash
# Run all tests
python -m pytest tests/ -x -v

# Run specific test modules
python -m pytest tests/test_analyzer.py -v
python -m pytest tests/test_integration.py -v
```

All external calls (Claude API, network requests, Playwright, WeasyPrint) are mocked in tests. No real API calls are made.

## Project Structure

```
cv-generator/
├── src/
│   ├── main.py              # CLI entry point (Click)
│   ├── config.py             # Settings (Pydantic + dotenv)
│   ├── analyzer/
│   │   ├── models.py         # JobRequirements model
│   │   ├── job_analyzer.py   # Claude API job analysis
│   │   └── prompts.py        # System/user prompts
│   ├── scraper/
│   │   ├── file_scraper.py   # PDF/HTML/TXT extraction
│   │   ├── url_scraper.py    # Web page scraping
│   │   └── board_scraper.py  # Job board search (JobSpy)
│   ├── tailor/
│   │   ├── models.py         # TailoredCV model
│   │   ├── cv_tailor.py      # CV tailoring engine
│   │   └── strategies.py     # Experience selection/ranking
│   ├── generator/
│   │   ├── pdf_generator.py  # PDF generation
│   │   └── templates/        # Jinja2 HTML/CSS templates
│   └── utils/
│       ├── language.py       # Language detection
│       └── file_utils.py     # JSON helpers
├── data/
│   ├── master_cv.json        # Master CV (bilingual, read-only)
│   └── photo.jpg             # Profile photo
├── tests/                    # pytest test suite
├── output/                   # Generated PDFs (gitignored)
├── pyproject.toml            # Dependencies and config
└── .env                      # API key (gitignored)
```
