from __future__ import annotations

from typing import Iterable, Mapping, Sequence


def _humanize_key(key: str) -> str:
    return (key or "").replace("_", " ").strip()


def _normalize_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _join_natural(parts: Sequence[str]) -> str:
    parts = [p.strip() for p in parts if p and p.strip()]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _dedupe_pairs(items: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []

    for key, value in items:
        k = (key or "").strip()
        v = _normalize_value(value)
        if not k or not v:
            continue
        pair = (k, v)
        if pair in seen:
            continue
        seen.add(pair)
        result.append(pair)

    return result


def synthesize_single_fact(key: str, value: str) -> str:
    """
    User-facing answer for a single exact fact.
    Example:
      Your favorite movie is Inception.
    """
    human_key = _humanize_key(key)
    value = _normalize_value(value)

    if not human_key or not value:
        return "I could not find a clear answer in memory."

    return f"Your {human_key} is {value}."


def synthesize_preference_fact(key: str, value: str) -> str:
    """
    User-facing answer for a single preference-like memory.
    Example:
      You like jazz.
      You prefer tea.
    """
    human_key = _humanize_key(key).lower()
    value = _normalize_value(value)

    if not human_key or not value:
        return "I could not find a clear preference in memory."

    # Lightweight phrasing rules for better natural tone
    if human_key.startswith("favorite "):
        thing = human_key[len("favorite ") :].strip()
        if thing:
            return f"Your favorite {thing} is {value}."

    if "prefer" in human_key or "preference" in human_key:
        return f"You prefer {value}."

    if human_key in {"likes", "interests", "favorite things"}:
        return f"You like {value}."

    return f"Your {human_key} is {value}."


def synthesize_broad_memory(
    items: list[tuple[str, str]],
    limit: int = 4,
) -> str:
    """
    Broad shortlist answer.
    Input is expected to be already relevance-ranked upstream.
    Example:
      You like blue, tea, jazz, and dune.
    """
    deduped = _dedupe_pairs(items)

    if not deduped:
        return "I could not find anything relevant in memory."

    values: list[str] = []
    seen_values: set[str] = set()

    for _key, value in deduped:
        v = _normalize_value(value)
        lv = v.lower()
        if lv in seen_values:
            continue
        seen_values.add(lv)
        values.append(v)
        if len(values) >= limit:
            break

    if not values:
        return "I could not find anything relevant in memory."

    if len(values) == 1:
        return f"You like {values[0]}."

    return f"You like {_join_natural(values)}."


def synthesize_profile_summary(
    facts: Mapping[str, str] | None,
    preferences: Mapping[str, str] | None,
    recent: Mapping[str, str] | None = None,
) -> str:
    """
    Section-based profile summary.
    Example:
      Here is what I know about you.
      Facts: your city is Boston; your job is engineer.
      Preferences: you like jazz; your favorite movie is Inception.
      Recent notes: your current project is VoiceGPT.
    """
    facts = facts or {}
    preferences = preferences or {}
    recent = recent or {}

    fact_parts: list[str] = []
    pref_parts: list[str] = []
    recent_parts: list[str] = []

    for key, value in facts.items():
        human_key = _humanize_key(key)
        norm_value = _normalize_value(value)
        if human_key and norm_value:
            fact_parts.append(f"your {human_key} is {norm_value}")

    for key, value in preferences.items():
        human_key = _humanize_key(key).lower()
        norm_value = _normalize_value(value)
        if not human_key or not norm_value:
            continue

        if human_key.startswith("favorite "):
            thing = human_key[len("favorite ") :].strip()
            if thing:
                pref_parts.append(f"your favorite {thing} is {norm_value}")
            else:
                pref_parts.append(f"you like {norm_value}")
        elif "prefer" in human_key or "preference" in human_key:
            pref_parts.append(f"you prefer {norm_value}")
        else:
            pref_parts.append(f"your {human_key} is {norm_value}")

    for key, value in recent.items():
        human_key = _humanize_key(key)
        norm_value = _normalize_value(value)
        if human_key and norm_value:
            recent_parts.append(f"your {human_key} is {norm_value}")

    sections: list[str] = []

    if fact_parts:
        sections.append("Facts: " + "; ".join(fact_parts) + ".")

    if pref_parts:
        sections.append("Preferences: " + "; ".join(pref_parts) + ".")

    if recent_parts:
        sections.append("Recent notes: " + "; ".join(recent_parts) + ".")

    if not sections:
        return "I do not know anything about you yet."

    return "Here is what I know about you. " + " ".join(sections)


def synthesize_memory_answer(
    query_mode: str,
    *,
    key: str | None = None,
    value: str | None = None,
    items: list[tuple[str, str]] | None = None,
    facts: Mapping[str, str] | None = None,
    preferences: Mapping[str, str] | None = None,
    recent: Mapping[str, str] | None = None,
) -> str:
    """
    Main dispatcher for Phase 7A v2.

    Supported query_mode values:
      - exact_fact
      - preference_fact
      - semantic_fact
      - broad_summary
      - profile_summary
    """
    query_mode = (query_mode or "").strip().lower()

    if query_mode == "exact_fact":
        return synthesize_single_fact(key or "", value or "")

    if query_mode == "preference_fact":
        return synthesize_preference_fact(key or "", value or "")

    if query_mode == "semantic_fact":
        # Transitional choice:
        # semantic fact still returns a direct user-facing answer
        return synthesize_single_fact(key or "", value or "")

    if query_mode == "broad_summary":
        return synthesize_broad_memory(items or [])

    if query_mode == "profile_summary":
        return synthesize_profile_summary(
            facts=facts,
            preferences=preferences,
            recent=recent,
        )

    return "I could not synthesize a clear answer from memory."