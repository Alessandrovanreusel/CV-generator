"""Tests for the URL scraper module."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.scraper.url_scraper import UrlScraper


class TestUrlScraperStaticSuccess:
    """Test successful static HTML fetching."""

    @patch("src.scraper.url_scraper.requests")
    def test_scrape_static_html(self, mock_requests):
        html = """<html><body>
        <nav><a>Nav</a></nav>
        <main><h1>Senior Developer</h1><p>We need a Python expert with 5 years experience.
        This is a long description to pass the 200 char threshold. Lorem ipsum dolor sit amet,
        consectetur adipiscing elit. More text here to make it long enough for the test.</p></main>
        <footer>Footer</footer>
        </body></html>"""
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        scraper = UrlScraper("https://example.com/job")
        result = scraper.scrape()

        assert "Senior Developer" in result
        assert "Python expert" in result
        assert "Nav" not in result
        assert "Footer" not in result
        mock_requests.get.assert_called_once()


class TestUrlScraperPlaywrightFallback:
    """Test Playwright fallback when static content is too short."""

    @patch("src.scraper.url_scraper.requests")
    def test_falls_back_to_playwright(self, mock_requests):
        # Static returns short content (< 200 chars stripped)
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>Loading...</body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        scraper = UrlScraper("https://example.com/js-job")

        full_html = """<html><body><main><h1>React Developer</h1>
        <p>We need a React and TypeScript expert. This is a sufficiently long description
        that passes the minimum character threshold for content extraction purposes.</p></main></body></html>"""

        # Create mock playwright module and sync_playwright context manager
        mock_page = MagicMock()
        mock_page.content.return_value = full_html
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_pw_ctx = MagicMock()
        mock_pw_ctx.chromium.launch.return_value = mock_browser

        mock_sync_pw_fn = MagicMock()
        mock_sync_pw_fn.return_value.__enter__ = MagicMock(return_value=mock_pw_ctx)
        mock_sync_pw_fn.return_value.__exit__ = MagicMock(return_value=False)

        mock_pw_module = MagicMock()
        mock_pw_module.sync_playwright = mock_sync_pw_fn

        with patch.dict(sys.modules, {"playwright": MagicMock(), "playwright.sync_api": mock_pw_module}):
            result = scraper.scrape()

        assert "React Developer" in result


class TestUrlScraperNetworkError:
    """Test handling of network errors."""

    @patch("src.scraper.url_scraper.requests")
    def test_raises_on_network_error(self, mock_requests):
        mock_requests.get.side_effect = Exception("Connection refused")

        scraper = UrlScraper("https://unreachable.example.com/job")
        with pytest.raises(Exception, match="Connection refused"):
            scraper.scrape()
