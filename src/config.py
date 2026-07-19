from pathlib import Path
from typing import Mapping, Optional

from dotenv import load_dotenv
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OPENAI_MODEL = "gpt-5-mini"
STREAMLIT_SECRET_KEYS = ("OPENAI_API_KEY", "OPENAI_MODEL")


class AppConfig(BaseModel):
    openai_api_key: Optional[str] = None
    openai_model: str = DEFAULT_OPENAI_MODEL


def _load_streamlit_secrets() -> Mapping[str, object]:
    """Read only supported Streamlit secrets without requiring Streamlit at import time."""
    try:
        import streamlit as st

        return {
            key: st.secrets[key]
            for key in STREAMLIT_SECRET_KEYS
            if key in st.secrets
        }
    except Exception:
        return {}


def _non_empty_text(value: object) -> Optional[str]:
    return value if isinstance(value, str) and value.strip() else None


def load_config(*, streamlit_secrets: Optional[Mapping[str, object]] = None) -> AppConfig:
    """Load local defaults, then environment, then deployment-native secrets."""
    load_dotenv(ROOT_DIR / ".env")
    from os import getenv

    secrets = _load_streamlit_secrets() if streamlit_secrets is None else streamlit_secrets
    environment_key = _non_empty_text(getenv("OPENAI_API_KEY"))
    environment_model = _non_empty_text(getenv("OPENAI_MODEL"))
    return AppConfig(
        openai_api_key=_non_empty_text(secrets.get("OPENAI_API_KEY")) or environment_key,
        openai_model=(
            _non_empty_text(secrets.get("OPENAI_MODEL"))
            or environment_model
            or DEFAULT_OPENAI_MODEL
        ),
    )
