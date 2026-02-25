from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    master_cv_path: Path = Path("data/master_cv.json")
    photo_path: Path = Path("data/photo.jpg")
    board_country: str = os.getenv("BOARD_COUNTRY", "Netherlands")

    def validate_settings(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Backward compatibility alias
Config = Settings

# Configure logging at import time
import logging

_log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, _log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
