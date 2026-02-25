"""Shared text processing utilities."""
from __future__ import annotations


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences if present.

    Handles patterns like:
        ```json
        {...}
        ```
    Returns text unchanged if no fences found.
    """
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.rstrip().endswith("```"):
            text = text.rstrip().rsplit("```", 1)[0]
    return text


def extract_html_text(html: str) -> str:
    """Extract clean text from HTML, stripping non-content tags.

    Removes script, style, nav, footer, header, and aside elements.
    Returns text with newline separators, whitespace stripped.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)
