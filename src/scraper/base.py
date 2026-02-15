from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base class for all job ad scrapers."""

    @abstractmethod
    def scrape(self) -> str:
        """Scrape and return raw text content of a job ad."""
        ...
