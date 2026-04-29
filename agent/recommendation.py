from __future__ import annotations

from typing import Iterable


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_items(items: Iterable) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []

    for item in items or []:
        if isinstance(item, dict):
            key = _safe_text(item.get("key"))
            value = _safe_text(item.get("value"))
            if key and value:
                result.append((key, value))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            key = _safe_text(item[0])
            value = _safe_text(item[1])
            if key and value:
                result.append((key, value))

    return result


def build_recommendation_from_memory(items: Iterable) -> str:
    pairs = _normalize_items(items)

    if not pairs:
        return "I do not have enough information yet to make a recommendation."

    memory = {key: value for key, value in pairs}

    favorite_book = memory.get("favorite_book", "")
    favorite_movie = memory.get("favorite_movie", "")
    favorite_music = memory.get("favorite_music", "")
    favorite_food = memory.get("favorite_food", "")
    favorite_drink = memory.get("favorite_drink", "")
    favorite_color = memory.get("favorite_color", "")
    favorite_city = memory.get("favorite_city", "")

    if favorite_book or favorite_movie or favorite_music:
        themes = []

        if favorite_book:
            themes.append(f"books like {favorite_book}")
        if favorite_movie:
            themes.append(f"movies like {favorite_movie}")
        if favorite_music:
            themes.append(f"music like {favorite_music}")

        joined = ", ".join(themes[:-1]) + (f", and {themes[-1]}" if len(themes) > 1 else themes[0])

        return (
            f"Based on what you like, I would recommend something thoughtful and immersive. "
            f"Since you enjoy {joined}, you seem to prefer experiences with a strong mood, style, or atmosphere."
        )

    if favorite_food or favorite_drink:
        parts = []
        if favorite_food:
            parts.append(favorite_food)
        if favorite_drink:
            parts.append(favorite_drink)

        if len(parts) == 2:
            joined = f"{parts[0]} and {parts[1]}"
        else:
            joined = parts[0]

        return (
            f"Based on what you like, I would recommend something cozy and enjoyable. "
            f"Since you like {joined}, you may enjoy experiences that feel comforting and easy to settle into."
        )

    if favorite_color or favorite_city:
        parts = []
        if favorite_color:
            parts.append(f"the color {favorite_color}")
        if favorite_city:
            parts.append(f"places like {favorite_city}")

        if len(parts) == 2:
            joined = f"{parts[0]} and {parts[1]}"
        else:
            joined = parts[0]

        return (
            f"Based on what you like, I would recommend something with a strong sense of mood or setting. "
            f"Since you seem drawn to {joined}, atmosphere may matter a lot to you."
        )

    values = [value for _key, value in pairs[:4]]
    if len(values) == 1:
        joined = values[0]
    elif len(values) == 2:
        joined = f"{values[0]} and {values[1]}"
    else:
        joined = ", ".join(values[:-1]) + f", and {values[-1]}"

    return (
        f"Based on what you like, I would recommend something that fits your overall taste. "
        f"So far I know that you like {joined}, which suggests you enjoy things with a distinct personal flavor."
    )

def build_book_recommendation_from_memory(items):
    pairs = _normalize_items(items)

    if not pairs:
        return "I do not have enough information yet to recommend a book."

    memory = {key: value for key, value in pairs}

    favorite_book = memory.get("favorite_book", "")
    favorite_movie = memory.get("favorite_movie", "")
    favorite_music = memory.get("favorite_music", "")

    if favorite_book:
        return (
            f"Since you liked {favorite_book}, I would recommend something in a similar style—"
            f"thoughtful, immersive, and possibly science fiction or concept-driven storytelling. "
            f"You may enjoy books with strong world-building or philosophical themes."
        )

    if favorite_movie:
        return (
            f"Based on your interest in movies like {favorite_movie}, you might enjoy books that explore "
            f"complex ideas or layered storytelling. Look for novels with strong conceptual depth."
        )

    if favorite_music:
        return (
            f"Since you enjoy music like {favorite_music}, you may enjoy books with a strong atmosphere "
            f"and tone—something immersive and emotionally textured."
        )

    return (
        "Based on what I know about your taste, I would recommend exploring books that focus on strong atmosphere, "
        "immersive storytelling, or thoughtful themes."
    )

def build_movie_recommendation_from_memory(items):
    pairs = _normalize_items(items)

    if not pairs:
        return "I do not have enough information yet to recommend a movie."

    memory = {key: value for key, value in pairs}

    favorite_movie = memory.get("favorite_movie", "")
    favorite_book = memory.get("favorite_book", "")
    favorite_music = memory.get("favorite_music", "")

    if favorite_movie:
        return (
            f"Since you liked {favorite_movie}, I would recommend movies with a similar depth—"
            f"concept-driven, atmospheric, or mind-bending stories. "
            f"You may enjoy films that explore complex ideas or layered realities."
        )

    if favorite_book:
        return (
            f"Since you enjoy books like {favorite_book}, you might like movies with strong world-building "
            f"and immersive storytelling, especially in science fiction or epic narratives."
        )

    if favorite_music:
        return (
            f"Since you enjoy music like {favorite_music}, you may prefer movies with a strong mood and tone—"
            f"something atmospheric and stylistically distinctive."
        )

    return (
        "Based on your taste, I would recommend movies with a strong sense of atmosphere, storytelling depth, "
        "or unique style."
    )
