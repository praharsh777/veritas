"""Server-side configuration. Secrets are read from the environment and never sent to the client."""
from __future__ import annotations

import os
from pathlib import Path

try:  # optional
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5").strip()
    openai_base_url: str = os.getenv("OPENAI_COMPAT_BASE_URL", "https://api.featherless.ai/v1").strip()
    openai_api_key: str = os.getenv("OPENAI_COMPAT_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_COMPAT_MODEL", "").strip()
    live_url_checks: bool = _bool("ENABLE_LIVE_URL_CHECKS", False)
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if o.strip()
    ]
    database_path: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "veritas.db"))

    # limits
    rate_limit: int = int(os.getenv("RATE_LIMIT_PER_WINDOW", "30"))
    rate_window_s: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "600"))
    max_text_chars: int = 20_000
    max_image_bytes: int = 6 * 1024 * 1024
    max_doc_bytes: int = 200 * 1024
    llm_timeout_s: float = 25.0
    url_timeout_s: float = 4.0


settings = Settings()
