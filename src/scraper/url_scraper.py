import requests

from .base import BaseScraper

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class UrlScraper(BaseScraper):
    """Scrape job ad text from a URL. Falls back to Playwright for JS-rendered pages."""

    def __init__(self, url: str):
        self.url = url
        self.headers = {"User-Agent": USER_AGENT}

    def scrape(self) -> str:
        text = self._try_static()
        if len(text.strip()) < 200:
            text = self._try_playwright()
        return text

    def _try_static(self) -> str:
        resp = requests.get(self.url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return self._extract_text(resp.text)

    def _try_playwright(self) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "Page requires JavaScript rendering but Playwright is not installed. "
                "Install with: pip install playwright && playwright install chromium"
            )
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="networkidle", timeout=30000)
            content = page.content()
            browser.close()
        return self._extract_text(content)

    @staticmethod
    def _extract_text(html: str) -> str:
        from src.utils.text_utils import extract_html_text

        return extract_html_text(html)
