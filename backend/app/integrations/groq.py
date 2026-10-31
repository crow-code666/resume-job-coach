"""Minimal Groq chat-completions client with server-only credentials."""

import json

from app.core.config import Settings
from app.integrations.http import ProviderError, post_json


def complete_json(settings: Settings, system: str, user: str, max_tokens: int = 900) -> dict | None:
    if not settings.groq_api_key:
        return None

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.25,
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    try:
        response = post_json("https://api.groq.com/openai/v1/chat/completions", headers, payload, "Groq")
    except ProviderError as error:
        if error.status != 400:
            return None
        # Some available models may not support JSON mode; the prompt still asks
        # for strict JSON, which is parsed and validated by the caller.
        payload.pop("response_format", None)
        try:
            response = post_json("https://api.groq.com/openai/v1/chat/completions", headers, payload, "Groq")
        except ProviderError:
            return None

    try:
        content = response["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            return None
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None
