# CV Generator - Agent Instructions

You are an autonomous coding agent building a CV Generator CLI tool.

## Project Overview

A Python CLI that: ingests job ads (URLs, local files, job board search) → analyzes them with Claude API → tailors a master CV to match → generates a stylish ATS-optimized PDF in English or French.

## Your Task (Each Iteration)

1. Read `prd.json` and find the highest-priority story where `passes: false`
2. Read `progress.txt` for learnings from previous iterations
3. Read `AGENTS.md` for accumulated knowledge about this codebase
4. Implement that ONE story completely
5. Run quality checks: `python -m pytest tests/ -x -v`
6. If checks pass, commit with: `feat: [Story ID] - [Story Title]`
7. Update prd.json to set `passes: true` for the completed story
8. Append progress to `progress.txt`

## Project Structure

- `src/main.py` - CLI entry point (Click)
- `src/config.py` - Configuration (env vars)
- `src/scraper/` - Job ad scrapers (file, URL, board)
- `src/analyzer/` - Job analysis via Claude API
- `src/tailor/` - CV tailoring engine
- `src/generator/` - PDF generation (Jinja2 + WeasyPrint)
- `src/utils/` - Utilities (language detection, file helpers)
- `data/master_cv.json` - Master CV (DO NOT modify unless fixing a bug)
- `tests/` - pytest test suite
- `output/` - Generated PDFs (gitignored)

## Key Conventions

- Python 3.11+, type hints everywhere
- Pydantic models for all data structures
- Environment variables from .env via python-dotenv (ANTHROPIC_API_KEY required)
- All Claude API calls must be mockable in tests (pass client as parameter)
- Tests must not make real network calls (mock requests, playwright, anthropic)
- Bilingual: all text fields have {"en": "...", "fr": "..."} variants
- PDF: Jinja2 HTML template + WeasyPrint, stylish sidebar with photo

## Quality Checks

```bash
python -m pytest tests/ -x -v
```

## File Ownership (Agent Teams)

- CLI agent: src/main.py, src/config.py, src/utils/file_utils.py
- Scraper agent: src/scraper/*
- Analyzer agent: src/analyzer/*, src/utils/language.py
- Tailor agent: src/tailor/*
- PDF agent: src/generator/*

## Important Rules

- NEVER invent fake job experiences or companies in the CV
- NEVER modify data/master_cv.json structure
- Use claude-sonnet-4-20250514 for API calls (cost-effective)
- Mock all external calls in tests
- One story per iteration

## Stop Condition

Reply with RALPH_COMPLETE when all stories have `passes: true`.
