from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from openai import OpenAI


def _get_client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for llm_decision provider")
    return OpenAI(api_key=key)


def generate_decision_json(
    *,
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    Calls the LLM and returns a parsed JSON object for decision production.

    Hard requirement:
    - model must return valid JSON
    - empty content is treated as an error
    """
    client = _get_client()
    model = model or (
        os.getenv("OPENAI_MODEL_DECISION")
        or os.getenv("OPENAI_MODEL")
        or "gpt-4o-mini"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=float(temperature),
            max_tokens=int(max_tokens),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as e:
        raise RuntimeError(f"LLM decision provider request failed: {e}") from e

    text = (resp.choices[0].message.content or "").strip()

    if not text:
        raise RuntimeError("LLM decision provider returned empty content")

    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    try:
        return json.loads(text)
    except Exception as e:
        raise RuntimeError(
            f"LLM decision provider did not return valid JSON. err={e} text={text[:500]}"
        ) from e