"""Tests for the file scraper module."""

import pytest

from src.scraper.base import BaseScraper
from src.scraper.file_scraper import FileScraper


class TestFileScraperTxt:
    """Test scraping plain text files."""

    def test_file_scraper_txt(self, tmp_path):
        """Create a temp .txt file, scrape it, and verify content returned."""
        content = (
            "Senior Software Engineer - TechCorp\n"
            "Location: Amsterdam, Netherlands\n\n"
            "Requirements:\n"
            "- 5+ years of Python experience\n"
            "- AWS cloud services knowledge\n"
        )
        txt_file = tmp_path / "job_ad.txt"
        txt_file.write_text(content, encoding="utf-8")

        scraper = FileScraper(str(txt_file))
        result = scraper.scrape()

        assert result == content
        assert "Senior Software Engineer" in result
        assert "Python" in result


class TestFileScraperHtml:
    """Test scraping HTML files with nav/footer filtering."""

    def test_file_scraper_html(self, tmp_path):
        """Scrape an HTML file and verify nav/footer content is stripped."""
        html_content = """<!DOCTYPE html>
<html>
<head><title>Job Ad</title></head>
<body>
    <nav><a href="/">Home</a><a href="/jobs">Jobs</a></nav>
    <header><h1>TechCorp Careers</h1></header>
    <main>
        <h2>Senior Software Engineer</h2>
        <p>We are looking for a talented Python developer with AWS experience.</p>
        <ul>
            <li>5+ years of experience</li>
            <li>Strong Python skills</li>
        </ul>
    </main>
    <footer><p>Copyright 2024 TechCorp</p></footer>
</body>
</html>"""
        html_file = tmp_path / "job_ad.html"
        html_file.write_text(html_content, encoding="utf-8")

        scraper = FileScraper(str(html_file))
        result = scraper.scrape()

        # Main content should be present
        assert "Senior Software Engineer" in result
        assert "Python developer" in result
        assert "5+ years of experience" in result

        # Nav and footer content should be stripped
        assert "Home" not in result
        assert "Jobs" not in result  # nav link text
        assert "Copyright 2024 TechCorp" not in result
        # Header is also stripped by the decompose logic
        assert "TechCorp Careers" not in result


class TestFileScraperUnsupported:
    """Test handling of unsupported file formats."""

    def test_file_scraper_unsupported(self, tmp_path):
        """Trying to open a .docx file should raise ValueError."""
        docx_file = tmp_path / "resume.docx"
        docx_file.write_bytes(b"fake docx content")

        with pytest.raises(ValueError, match="Unsupported file format"):
            FileScraper(str(docx_file))


class TestFileScraperNotFound:
    """Test handling of nonexistent files."""

    def test_file_scraper_not_found(self):
        """Trying to open a nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            FileScraper("/nonexistent/path/job_ad.txt")


class TestBaseScraperAbstract:
    """Test that BaseScraper cannot be instantiated directly."""

    def test_base_scraper_is_abstract(self):
        """BaseScraper is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseScraper()
