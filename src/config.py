from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    master_cv_path: Path = Path("data/master_cv.json")
    photo_path: Path = Path("data/photo.jpg")
    claude_model: str = "claude-sonnet-4-20250514"

    def validate_settings(self) -> None:
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set. Add it to .env or set as environment variable.")
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Backward compatibility alias
Config = Settings
