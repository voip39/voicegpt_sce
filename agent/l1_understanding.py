import re


def _extract_text(last_event: dict) -> str:
    if not isinstance(last_event, dict):
        return ""

    content = last_event.get("content", {}) or {}
    text = content.get("text")

    if isinstance(text, str):
        return text.strip()

    return ""


def _normalize_memory_key(raw_key: str) -> str:
    raw_key = (raw_key or "").strip().lower()
    raw_key = raw_key.replace(" ", "_")
    return raw_key


def understand(context: dict) -> dict:
    state = context.get("state", {}) or {}

    last_event = context.get("last_event")
    if not last_event:
        last_event = state.get("last_event", {}) or {}

    text = _extract_text(last_event)
    text_lower = text.lower()

    understanding = {
        "intent": "message_received",
        "last_event": last_event,
    }

    if not text:
        return understanding

    if text_lower.startswith("search:"):
        understanding["intent"] = "kb_search"
        understanding["query"] = text[len("search:"):].strip()
        return understanding

    if text_lower.startswith("sms:"):
        understanding["intent"] = "send_sms"
        understanding["sms_text"] = text[len("sms:"):].strip()
        return understanding

    if text_lower.startswith("handoff:"):
        understanding["intent"] = "handoff_request"
        understanding["handoff_reason"] = text[len("handoff:"):].strip()
        return understanding

    if text_lower.startswith("remember:"):
        payload = text[len("remember:"):].strip()
        understanding["intent"] = "memory_store"
        understanding["memory_payload"] = payload
        return understanding

    if "what do you know about me" in text_lower or "tell me about me" in text_lower:
        understanding["intent"] = "memory_summary"
        understanding["memory_query"] = {}
        return understanding

    if "tell me about my preferences" in text_lower or "tell me about my tastes" in text_lower:
        understanding["intent"] = "memory_summary"
        understanding["memory_query"] = {"topic": "preferences"}
        return understanding

    if text_lower in {
        "what movie should i watch based on what i like",
        "recommend a movie for me",
        "what should i watch",
    }:
        understanding["intent"] = "memory_recommendation_movies"
        understanding["memory_query"] = {
            "query_text": text,
            "topic": "movies",
        }
        return understanding

    if text_lower in {
        "what should i read based on what i like",
        "recommend a book for me",
        "what book should i read",
    }:
        understanding["intent"] = "memory_recommendation_books"
        understanding["memory_query"] = {
            "query_text": text,
            "topic": "books",
        }
        return understanding

    if text_lower in {
        "based on what i like, recommend something",
        "recommend something for me",
        "what would you recommend for me",
    }:
        understanding["intent"] = "memory_recommendation"
        understanding["memory_query"] = {
            "query_text": text,
            "topic": "likes",
        }
        return understanding

    if text_lower in {"what do i like", "what things do i like"}:
        understanding["intent"] = "memory_semantic_recall"
        understanding["memory_query"] = {
            "query_text": text,
            "topic": "likes",
        }
        return understanding

    match = re.match(r"^what is my (.+?)\??$", text_lower)
    if match:
        raw_key = match.group(1).strip()
        understanding["intent"] = "memory_recall"
        understanding["memory_query"] = {
            "key": _normalize_memory_key(raw_key)
        }
        return understanding

    match = re.match(r"^what (.+?) do i like\??$", text_lower)
    if match:
        raw_topic = match.group(1).strip()
        understanding["intent"] = "memory_semantic_recall"
        understanding["memory_query"] = {
            "query_text": text,
            "topic": raw_topic,
        }
        return understanding

    return understanding
