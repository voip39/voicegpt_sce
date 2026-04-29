from __future__ import annotations

from typing import Iterable

from agent.recommendation import (
    build_recommendation_from_memory,
    build_book_recommendation_from_memory,
    build_movie_recommendation_from_memory,
)


def route_recommendation(intent: str, items: Iterable) -> str:
    intent = (intent or "").strip()

    if intent == "memory_recommendation_books":
        return build_book_recommendation_from_memory(items)

    if intent == "memory_recommendation_movies":
        return build_movie_recommendation_from_memory(items)

    return build_recommendation_from_memory(items)
