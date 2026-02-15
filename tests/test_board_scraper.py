"""Tests for the board scraper module."""

from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

from src.scraper.board_scraper import BoardScraper


class TestBoardScraperSuccess:
    """Test successful job board search."""

    @patch("jobspy.scrape_jobs")
    def test_search_returns_results(self, mock_scrape):
        mock_scrape.return_value = pd.DataFrame([
            {
                "title": "Software Engineer",
                "company": "TechCorp",
                "location": "Amsterdam",
                "job_url": "https://example.com/job/1",
                "description": "Python developer needed.",
            },
            {
                "title": "Data Engineer",
                "company": "DataCo",
                "location": "Berlin",
                "job_url": "https://example.com/job/2",
                "description": "SQL and Python role.",
            },
        ])

        scraper = BoardScraper()
        results = scraper.search("Python developer", location="Amsterdam")

        assert len(results) == 2
        assert results[0]["title"] == "Software Engineer"
        assert results[0]["company"] == "TechCorp"
        assert results[1]["title"] == "Data Engineer"
        mock_scrape.assert_called_once()


class TestBoardScraperEmptyResults:
    """Test search with no results."""

    @patch("jobspy.scrape_jobs")
    def test_empty_results(self, mock_scrape):
        mock_scrape.return_value = pd.DataFrame(
            columns=["title", "company", "location", "job_url", "description"]
        )

        scraper = BoardScraper()
        results = scraper.search("nonexistent role xyz")

        assert results == []


class TestBoardScraperCustomSites:
    """Test passing custom site names."""

    @patch("jobspy.scrape_jobs")
    def test_custom_sites(self, mock_scrape):
        mock_scrape.return_value = pd.DataFrame(
            columns=["title", "company", "location", "job_url", "description"]
        )

        scraper = BoardScraper()
        scraper.search("Dev", sites=["linkedin"])

        call_kwargs = mock_scrape.call_args[1]
        assert call_kwargs["site_name"] == ["linkedin"]
