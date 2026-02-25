from pathlib import Path

from .base import BaseScraper


class FileScraper(BaseScraper):
    """Scrape job ad text from a local file (PDF, HTML, or TXT)."""

    SUPPORTED_EXTENSIONS = {".pdf", ".html", ".htm", ".txt"}

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        if self.file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {self.file_path.suffix}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

    def scrape(self) -> str:
        suffix = self.file_path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf()
        elif suffix in (".html", ".htm"):
            return self._extract_html()
        else:
            return self._extract_text()

    def _extract_pdf(self) -> str:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise RuntimeError(
                "PyMuPDF is required for PDF parsing. Install with: pip install PyMuPDF"
            )
        doc = fitz.open(str(self.file_path))
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n".join(pages)

    def _extract_html(self) -> str:
        from src.utils.text_utils import extract_html_text

        html = self.file_path.read_text(encoding="utf-8")
        return extract_html_text(html)

    def _extract_text(self) -> str:
        return self.file_path.read_text(encoding="utf-8")
