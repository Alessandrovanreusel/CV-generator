"""Tests for the language detection utility."""

import pytest

from src.utils.language import detect_language


class TestDetectEnglish:
    """Test detection of English text."""

    def test_english_text(self):
        text = (
            "We are looking for a Senior Software Engineer with experience "
            "in Python, AWS, and Docker. The ideal candidate will have 5+ "
            "years of experience building scalable web applications."
        )
        assert detect_language(text) == "en"


class TestDetectFrench:
    """Test detection of French text."""

    def test_french_text(self):
        text = (
            "Nous recherchons un ingénieur logiciel senior avec une expérience "
            "en Python, AWS et Docker. Le candidat idéal aura plus de 5 ans "
            "d'expérience dans le développement d'applications web évolutives."
        )
        assert detect_language(text) == "fr"


class TestDetectEmpty:
    """Test handling of empty or short text."""

    def test_empty_string(self):
        assert detect_language("") == "en"

    def test_short_string(self):
        assert detect_language("hello") == "en"

    def test_whitespace_only(self):
        assert detect_language("   ") == "en"


class TestDetectFallback:
    """Test fallback behavior for unsupported languages."""

    def test_unsupported_language_falls_back_to_en(self):
        # German text should fall back to 'en'
        text = (
            "Wir suchen einen erfahrenen Softwareentwickler mit Kenntnissen "
            "in Python und Cloud-Technologien. Der ideale Kandidat hat "
            "mindestens fünf Jahre Berufserfahrung."
        )
        result = detect_language(text)
        assert result == "en"  # Not 'de'
