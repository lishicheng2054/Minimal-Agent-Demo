from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

try:
    from openai import OpenAI as _OpenAIClient
except Exception:  # noqa: BLE001
    _OpenAIClient = None

OpenAI = _OpenAIClient


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    session_dir: Path
    docs_root: Path
    base_url: str = ""


def load_settings() -> Settings:
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    return Settings(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        session_dir=Path(os.getenv("SESSION_DIR", "data/sessions")),
        docs_root=Path(os.getenv("DOCS_ROOT", ".")),
        base_url=os.getenv("OPENAI_BASE_URL", "").strip(),
    )


def make_client(settings: Settings):
    client_kwargs = {"api_key": settings.api_key}
    if settings.base_url:
        client_kwargs["base_url"] = settings.base_url
    if OpenAI is None:
        raise RuntimeError("openai package is not installed")
    return OpenAI(**client_kwargs)
