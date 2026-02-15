from __future__ import annotations

import json

from .models import JobRequirements
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.utils.claude_cli import call_claude


class JobAnalyzer:
    """Analyze a job ad using Claude CLI to extract structured requirements."""

    def __init__(self, model: str | None = None, client=None):
        # model and client kept for backward compatibility but not used
        pass

    def analyze(self, job_text: str) -> JobRequirements:
        """Analyze raw job ad text and return structured requirements."""
        if not job_text or len(job_text.strip()) < 50:
            raise ValueError("Job ad text is too short to analyze.")

        prompt = USER_PROMPT_TEMPLATE.format(job_text=job_text)
        raw_json = call_claude(prompt, system_prompt=SYSTEM_PROMPT)
        # Strip markdown fences if present
        if raw_json.startswith("```"):
            raw_json = raw_json.split("\n", 1)[1]
            if raw_json.endswith("```"):
                raw_json = raw_json.rsplit("```", 1)[0]

        data = json.loads(raw_json)
        return JobRequirements(**data)
