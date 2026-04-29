from __future__ import annotations

from typing import Any, Dict, List, Tuple


_SYSTEM_PROMPT = """You are a decision producer for a canonical AI runtime.

Your task:
Return ONLY valid JSON with a minimal semantic decision draft.

Allowed top-level fields:
- decision_type
- capability
- selected_path
- inputs_used
- response_plan
- confidence
- notes

Do NOT return any other top-level fields.
Do NOT include markdown fences.
Do NOT explain your answer.
Do NOT return prose outside JSON.

Allowed decision_type values:
- greeting
- profile_summary
- memory_write_ack
- memory_recall
- continuity_recall
- conversation_summary
- answer

Allowed capability values:
- greeting
- profile_summary
- memory_write
- name_recall
- favorite_color_recall
- favorite_food_recall
- previous_message
- conversation_summary
- answer

Rules:
1. Prefer the routing signal unless there is a strong reason to narrow or correct the semantic choice.
2. inputs_used must reflect which context sources are likely needed:
   - profile
   - memory
   - history
3. response_plan must contain:
   - response_style: use "direct" for all cases in this version
   - template_family
4. confidence must be a number between 0.0 and 1.0
5. If uncertain, lower confidence below 0.8
6. notes must be a list of objects with:
   - source
   - kind
   - text
   Use "builder" as source in this version.
7. selected_path should be a short string describing the semantic path chosen.
8. Never invent unavailable context.
9. Do NOT mix decision_type and capability from different semantic families.

Continuity guidance:
- If the user asks what they said before, what their last message was, or asks for the previous message,
  use:
  - decision_type = "continuity_recall"
  - capability = "previous_message"
  - response_plan.template_family = "continuity_recall"

- If the user asks for a conversation summary, chat summary, or history summary,
  use:
  - decision_type = "conversation_summary"
  - capability = "conversation_summary"
  - response_plan.template_family = "conversation_summary"

Memory recall guidance:
- If the user asks for favorite food, favorite color, or name recall,
  use:
  - decision_type = "memory_recall"
  - capability matching the specific recall target
  - response_plan.template_family = "memory_recall"

Profile guidance:
- If the user asks "tell me about me" or asks for a profile-style summary of known facts,
  use:
  - decision_type = "profile_summary"
  - capability = "profile_summary"
  - response_plan.template_family = "profile_summary"

Path guidance:
- Prefer selected_path values that align with the capability name when possible.
- For previous message recall, prefer "previous_message".
- For conversation summary, prefer "conversation_summary".
- For profile summary, prefer "profile_summary".
"""


def build_decision_prompts(
    runtime_ctx: Dict[str, Any],
    routing: Dict[str, Any],
) -> Tuple[str, str]:
    system_prompt = _SYSTEM_PROMPT
    user_prompt = _build_user_prompt(runtime_ctx, routing)
    return system_prompt, user_prompt


def _build_user_prompt(runtime_ctx: Dict[str, Any], routing: Dict[str, Any]) -> str:
    text = ((runtime_ctx.get("current_turn") or {}).get("text") or "").strip()

    profile = runtime_ctx.get("profile") or {}
    memory_items = (runtime_ctx.get("memory") or {}).get("items") or []
    history = (runtime_ctx.get("continuity") or {}).get("history") or []

    route = routing.get("route", "default_answer")
    route_family = routing.get("family", "fallback")
    capability = routing.get("capability", "answer")

    profile_summary = _summarize_profile(profile)
    memory_summary = _summarize_memory(memory_items)
    history_summary = _summarize_history(history)

    return f"""User message:
{text!r}

Routing signal from deterministic router:
  route: {route}
  route_family: {route_family}
  capability: {capability}

Available context:
  profile_available: {bool(profile)}
  memory_available: {bool(memory_items)}
  history_available: {bool(history)}
  profile_fields: {profile_summary}
  memory_keys: {memory_summary}
  recent_history: {history_summary}

Return JSON only with the allowed fields.
Do not include any fields outside the allowed schema.
""".strip()


def _summarize_profile(profile: Dict[str, Any]) -> str:
    fields: List[str] = []

    identity = profile.get("identity") or {}
    preferences = profile.get("preferences") or {}

    if identity.get("name"):
        fields.append("name")
    if preferences.get("favorite_color"):
        fields.append("favorite_color")
    if preferences.get("favorite_food"):
        fields.append("favorite_food")

    return ", ".join(fields) if fields else "none"


def _summarize_memory(memory_items: List[Dict[str, Any]]) -> str:
    keys: List[str] = []
    seen = set()

    for item in memory_items:
        if not isinstance(item, dict):
            continue
        content = item.get("content") or {}
        if not isinstance(content, dict):
            continue
        for key, value in content.items():
            if key in seen:
                continue
            if value in (None, "", [], {}):
                continue
            seen.add(key)
            keys.append(str(key))

    return ", ".join(keys) if keys else "none"


def _summarize_history(history: List[Dict[str, Any]]) -> str:
    recent_user_turns: List[str] = []

    for item in history[-6:]:
        if not isinstance(item, dict):
            continue
        if item.get("role") == "user" and item.get("text"):
            recent_user_turns.append(str(item.get("text")).strip())

    recent_user_turns = [x for x in recent_user_turns if x]

    if not recent_user_turns:
        return "none"

    return " | ".join(recent_user_turns[-2:])
