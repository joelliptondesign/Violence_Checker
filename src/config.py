from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OPENAI_MODEL = "gpt-5-mini"


class AppConfig(BaseModel):
    openai_api_key: Optional[str] = None
    openai_model: str = DEFAULT_OPENAI_MODEL


def load_config() -> AppConfig:
    load_dotenv(ROOT_DIR / ".env")
    from os import getenv

    return AppConfig(
        openai_api_key=getenv("OPENAI_API_KEY") or None,
        openai_model=getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL,
    )
