from __future__ import annotations


class BoardScraper:
    """Search job boards (LinkedIn, Indeed, Glassdoor, etc.) via JobSpy."""

    DEFAULT_SITES = ["linkedin", "indeed", "glassdoor"]

    def __init__(self, country: str = "Netherlands"):
        self.country = country

    def search(
        self,
        search_term: str,
        location: str = "Amsterdam",
        sites: list[str] | None = None,
        results_wanted: int = 10,
    ) -> list[dict]:
        """Search job boards and return a list of job ad dicts.

        Each dict contains: title, company, location, job_url, description.
        """
        try:
            from jobspy import scrape_jobs
        except ImportError:
            raise RuntimeError(
                "python-jobspy is required for board scraping. "
                "Install with: pip install python-jobspy"
            )

        sites = sites or self.DEFAULT_SITES
        df = scrape_jobs(
            site_name=sites,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            country_indeed=self.country,
        )

        results = []
        for _, row in df.iterrows():
            results.append({
                "title": str(row.get("title", "")),
                "company": str(row.get("company", "")),
                "location": str(row.get("location", "")),
                "job_url": str(row.get("job_url", "")),
                "description": str(row.get("description", "")),
            })
        return results
