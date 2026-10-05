from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from ..config import settings
from .base import SYSTEM_PROMPT, AIAnalysis, LLMProvider, ProviderError, parse_ai_json, user_prompt

log = logging.getLogger("veritas")


def configured_models() -> list[str]:
    """OPENAI_COMPAT_MODEL may be a comma-separated fallback list: tried in order."""
    return [m.strip() for m in settings.openai_model.split(",") if m.strip()]


class OpenAICompatProvider(LLMProvider):
    """Any OpenAI-compatible chat-completions endpoint (OpenRouter, Featherless, vLLM, Ollama...). Text only."""

    name = "openai_compat"

    @property
    def available(self) -> bool:
        return bool(settings.openai_api_key and configured_models())

    async def _call(self, model: str, text: str, extraction_summary: str) -> AIAnalysis:
        body = {
            "model": model,
            "temperature": 0,
            "max_tokens": 2500,
            # ask OpenRouter to skip "thinking" mode (it burns the output budget); ignored by models without it
            "reasoning": {"enabled": False},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(text, extraction_summary)},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as c:
                url = settings.openai_base_url.rstrip("/") + "/chat/completions"
                headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
                r = await c.post(url, headers=headers, json=body)
                if r.status_code == 400 and "reasoning" in body:  # model/provider rejects the optional field
                    body.pop("reasoning")
                    r = await c.post(url, headers=headers, json=body)
                # 502/503 = transient upstream hiccup: one quick retry. 429 = rate/quota limit: do NOT retry the same
                # model (retries burn the free quota); the caller falls through to the next configured model instead.
                if r.status_code in (502, 503):
                    await asyncio.sleep(2.0)
                    r = await c.post(url, headers=headers, json=body)
            if r.status_code != 200:
                detail = ""
                try:  # provider error text (e.g. "rate limit", "model not found"); contains no user content
                    detail = str(r.json().get("error", {}).get("message", ""))[:140]
                except Exception:
                    pass
                raise ProviderError(f"{model}: HTTP {r.status_code}" + (f" - {detail}" if detail else ""))
            raw = r.json()["choices"][0]["message"]["content"] or ""
            if not raw.strip():
                raise ProviderError(f"{model}: empty response (reasoning models sometimes do this)")
        except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as e:
            raise ProviderError(f"{model}: request failed ({type(e).__name__})") from e
        try:
            return parse_ai_json(raw, text)
        except ProviderError as e:
            raise ProviderError(f"{model}: {e}") from e

    async def analyze(self, text: str, extraction_summary: str) -> Optional[AIAnalysis]:
        errors: list[str] = []
        for model in configured_models():
            try:
                return await self._call(model, text, extraction_summary)
            except ProviderError as e:
                errors.append(str(e))
                log.warning("ai model failed, trying next: %s", e)
        raise ProviderError("all configured models failed: " + " | ".join(errors))
