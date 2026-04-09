"""Minimal Ollama client with deterministic fallback behavior."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OllamaResponse:
    text: str
    model_used: str
    used_fallback: bool


def ask_ollama(
    base_url: str,
    model: str,
    prompt: str,
    timeout_seconds: float,
) -> OllamaResponse:
    endpoint = f"{base_url.rstrip('/')}/api/generate"
    body = {"model": model, "prompt": prompt, "stream": False}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
            text = str(payload.get("response", "")).strip()
            return OllamaResponse(
                text=text or "No model response.",
                model_used=model,
                used_fallback=False,
            )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return OllamaResponse(
            text=(
                "LLM unavailable; deterministic path used. "
                "Escalate only if deterministic risk or policy requires."
            ),
            model_used="deterministic-fallback",
            used_fallback=True,
        )
