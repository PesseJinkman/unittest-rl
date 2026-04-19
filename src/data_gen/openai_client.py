"""Thin wrapper around the OpenAI client with JSON-mode + retries."""
from __future__ import annotations

import json
import os
import time
from typing import Any

from openai import OpenAI
from openai import APIError, APITimeoutError, RateLimitError


def make_client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)


def chat_json(
    client: OpenAI,
    model: str,
    system: str,
    user: str,
    *,
    temperature: float = 1.0,
    max_retries: int = 3,
    request_timeout_s: float = 120.0,
) -> dict[str, Any]:
    """Request a JSON object from the model. Retries on rate limit / timeouts."""
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                timeout=request_timeout_s,
            )
            content = resp.choices[0].message.content or "{}"
            return json.loads(content)
        except (RateLimitError, APITimeoutError, APIError) as e:
            last_err = e
            time.sleep(2 ** attempt)
        except json.JSONDecodeError as e:
            last_err = e
            time.sleep(1)
    raise RuntimeError(f"chat_json failed after {max_retries} retries: {last_err}")
