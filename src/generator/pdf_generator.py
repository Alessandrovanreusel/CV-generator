from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

# Add MSYS2 mingw64 bin to DLL search path for WeasyPrint on Windows
if sys.platform == "win32":
    _msys2_bin = Path("C:/msys64/mingw64/bin")
    if _msys2_bin.exists():
        os.environ["PATH"] = str(_msys2_bin) + os.pathsep + os.environ.get("PATH", "")
        os.add_dll_directory(str(_msys2_bin))

from jinja2 import Environment, FileSystemLoader

from src.tailor.models import TailoredCV

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Section labels by language
LABELS = {
    "en": {
        "contact": "Contact",
        "skills": "Skills",
        "languages": "Languages",
        "certifications": "Certifications",
        "volunteering": "Volunteering",
        "summary": "Professional Summary",
        "experience": "Experience",
        "education": "Education",
        "projects": "Projects",
        "present": "Present",
    },
    "fr": {
        "contact": "Contact",
        "skills": "Compétences",
        "languages": "Langues",
        "certifications": "Certifications",
        "volunteering": "Bénévolat",
        "summary": "Résumé Professionnel",
        "experience": "Expérience",
        "education": "Formation",
        "projects": "Projets",
        "present": "Présent",
    },
}

# Language proficiency → number of filled dots (out of 5)
LANG_DOTS = {
    "Native": 5,
    "Bilingual": 5,
    "Fluent": 4,
    "Intermediate": 3,
    "Basic": 2,
    "Beginner": 1,
    # French equivalents
    "Natif": 5,
    "Langue maternelle": 5,
    "Bilingue": 5,
    "Courant": 4,
    "Intermédiaire": 3,
    "Basique": 2,
    "Débutant": 1,
}


class PdfGenerator:
    """Generate a stylish, ATS-friendly PDF CV using Jinja2 + WeasyPrint."""

    def __init__(self, include_photo: bool = True):
        self.include_photo = include_photo
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,
        )

    def generate(
        self,
        tailored_cv: TailoredCV,
        output_path: str | Path,
        photo_path: str | Path | None = None,
    ) -> Path:
        """Render the tailored CV to PDF.

        Args:
            tailored_cv: The tailored CV data.
            output_path: Where to save the PDF.
            photo_path: Path to the photo file. Defaults to data/photo.jpg.

        Returns:
            Path to the generated PDF.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load photo as base64
        photo_base64 = None
        if self.include_photo:
            photo_base64 = self._load_photo_base64(photo_path)

        # Get labels for target language
        labels = LABELS.get(tailored_cv.target_language, LABELS["en"])

        # Flatten skills for sidebar display (take top skills across categories)
        flat_skills = self._flatten_skills(tailored_cv.skills, max_total=12)

        # Build skill levels dict
        skill_levels = self._load_skill_levels()

        # Render HTML
        template = self.env.get_template("cv_template.html")
        html = template.render(
            cv=tailored_cv,
            photo_base64=photo_base64,
            labels=labels,
            lang_dots=LANG_DOTS,
            skill_levels=skill_levels,
            flat_skills=flat_skills,
        )

        # Generate PDF with WeasyPrint
        try:
            from weasyprint import HTML
        except ImportError:
            raise RuntimeError(
                "WeasyPrint is required for PDF generation. "
                "Install with: pip install weasyprint"
            )

        HTML(
            string=html,
            base_url=str(TEMPLATES_DIR),
        ).write_pdf(str(output_path))

        return output_path

    def _load_photo_base64(
        self, photo_path: str | Path | None
    ) -> str | None:
        """Load a photo file and return as base64 string."""
        if photo_path is None:
            photo_path = Path("data/photo.jpg")
        photo_path = Path(photo_path)

        if not photo_path.exists():
            return None

        with open(photo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _load_skill_levels(self) -> dict[str, int]:
        """Load skill levels from JSON file."""
        skill_levels_path = Path(__file__).parent.parent.parent / "data" / "skill_levels.json"
        try:
            with open(skill_levels_path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            import logging
            logging.getLogger(__name__).warning("Could not load skill_levels.json: %s", e)
            return {}

    def _flatten_skills(
        self, skills: dict[str, list[str]], max_total: int = 12
    ) -> list[str]:
        """Flatten categorized skills into a single list, limited to max_total."""
        flat = []
        for category_skills in skills.values():
            for skill in category_skills:
                if skill not in flat:
                    flat.append(skill)
                if len(flat) >= max_total:
                    return flat
        return flat
