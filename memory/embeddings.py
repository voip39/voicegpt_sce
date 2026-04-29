import os
from typing import List

from openai import OpenAI


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def embed_text(text: str, model: str = "text-embedding-3-small") -> List[float]:
    if not text or not text.strip():
        raise ValueError("text for embedding must be non-empty")

    client = _get_client()
    response = client.embeddings.create(
        model=model,
        input=text.strip(),
    )
    return response.data[0].embedding
