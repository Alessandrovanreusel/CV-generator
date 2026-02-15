"""Wrapper to call Claude via the claude CLI instead of the Anthropic API."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _find_claude_cmd() -> str:
    """Find the claude CLI executable path."""
    claude = shutil.which("claude")
    if claude:
        return claude
    # Windows: try .cmd extension explicitly
    if sys.platform == "win32":
        claude_cmd = shutil.which("claude.cmd")
        if claude_cmd:
            return claude_cmd
    raise FileNotFoundError(
        "claude CLI not found in PATH. Install it with: npm install -g @anthropic-ai/claude-code"
    )


def call_claude(prompt: str, system_prompt: str | None = None, max_turns: int = 1) -> str:
    """Call Claude via the claude CLI and return the response text.

    Uses `claude -p` (print mode) which outputs the response and exits.
    This uses the user's existing Claude Code subscription — no API key needed.
    """
    claude_bin = _find_claude_cmd()
    cmd = [claude_bin, "-p", "--output-format", "text"]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    if max_turns:
        cmd.extend(["--max-turns", str(max_turns)])

    # Clear CLAUDECODE env var to avoid nested-session detection
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        shell=(sys.platform == "win32"),
        env=env,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"Claude CLI failed (exit {result.returncode}): {stderr}")

    return result.stdout.strip()
