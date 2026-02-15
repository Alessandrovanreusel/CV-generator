"""Tests for the file scraper module."""

import pytest

from src.scraper.file_scraper import FileScraper


class TestFileScraperTxt:
    """Test scraping plain text files."""

    def test_scrape_txt(self, tmp_path):
        content = "Senior Software Engineer\nRequirements:\n- Python\n- AWS\n"
        f = tmp_path / "job.txt"
        f.write_text(content, encoding="utf-8")

        result = FileScraper(str(f)).scrape()
        assert result == content
        assert "Python" in result


class TestFileScraperHtml:
    """Test scraping HTML files with tag filtering."""

    def test_scrape_html_strips_nav_footer(self, tmp_path):
        html = """<!DOCTYPE html><html><body>
        <nav><a href="/">Home</a></nav>
        <main><h2>Software Engineer</h2><p>Python developer needed.</p></main>
        <footer><p>Copyright 2024</p></footer>
        </body></html>"""
        f = tmp_path / "job.html"
        f.write_text(html, encoding="utf-8")

        result = FileScraper(str(f)).scrape()
        assert "Software Engineer" in result
        assert "Python developer" in result
        assert "Home" not in result
        assert "Copyright 2024" not in result


class TestFileScraperPdf:
    """Test PDF extraction using PyMuPDF."""

    def test_scrape_pdf(self, tmp_path):
        import fitz
        pdf_path = tmp_path / "job.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Data Engineer - CloudCorp\nRequires Python and SQL.")
        doc.save(str(pdf_path))
        doc.close()

        result = FileScraper(str(pdf_path)).scrape()
        assert "Data Engineer" in result
        assert "Python" in result


class TestFileScraperUnsupported:
    """Test handling of unsupported file formats."""

    def test_unsupported_raises_value_error(self, tmp_path):
        f = tmp_path / "resume.docx"
        f.write_bytes(b"fake")
        with pytest.raises(ValueError, match="Unsupported file format"):
            FileScraper(str(f))


class TestFileScraperNotFound:
    """Test handling of nonexistent files."""

    def test_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            FileScraper("/nonexistent/job.txt")
