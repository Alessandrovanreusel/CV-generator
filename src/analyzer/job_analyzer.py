from __future__ import annotations

import json
import time

import anthropic

from .models import JobRequirements
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


class JobAnalyzer:
    """Analyze a job ad using Claude API to extract structured requirements."""

    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.client = client or anthropic.Anthropic()
        self.model = model

    def analyze(self, job_text: str) -> JobRequirements:
        """Analyze raw job ad text and return structured requirements."""
        if not job_text or len(job_text.strip()) < 50:
            raise ValueError("Job ad text is too short to analyze.")

        response = self._call_api(job_text)
        raw_json = response.content[0].text.strip()

        # Strip markdown fences if present
        if raw_json.startswith("```"):
            raw_json = raw_json.split("\n", 1)[1]
            if raw_json.endswith("```"):
                raw_json = raw_json.rsplit("```", 1)[0]

        data = json.loads(raw_json)
        return JobRequirements(**data)

    def _call_api(
        self, job_text: str, max_retries: int = 3
    ) -> anthropic.types.Message:
        prompt = USER_PROMPT_TEMPLATE.format(job_text=job_text)
        last_error = None

        for attempt in range(max_retries):
            try:
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
            except anthropic.RateLimitError:
                last_error = "Rate limited"
                time.sleep(2 ** attempt)
            except anthropic.APIConnectionError as e:
                last_error = str(e)
                time.sleep(2 ** attempt)
            except anthropic.AuthenticationError:
                raise ValueError(
                    "Invalid ANTHROPIC_API_KEY. Check your .env file."
                )

        raise RuntimeError(
            f"Failed to analyze job ad after {max_retries} attempts: {last_error}"
        )
