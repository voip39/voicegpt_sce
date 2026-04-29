def normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def is_empty(text: str) -> bool:
    return not bool(normalize(text))


def is_greeting(text: str) -> bool:
    t = normalize(text)
    return t in {
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "hello there",
        "hi there",
        "hey there",
    }


def is_memory_write(text: str) -> bool:
    t = normalize(text)

    if t.startswith("my "):
        return True

    if t.startswith("call me "):
        return True

    if t.startswith("remember that "):
        return True

    return False


def is_profile_query(text: str) -> bool:
    t = normalize(text)

    exact = {
        "what do you know about me",
        "tell me about me",
        "what do you remember about me",
        "who am i",
        "what do you know abt me",
        "what do u know about me",
        "what do u remember about me",
    }

    if t in exact:
        return True

    if "know about me" in t:
        return True

    if "remember about me" in t:
        return True

    if "tell me about me" in t:
        return True

    return False


def is_name_query(text: str) -> bool:
    t = normalize(text)

    exact = {
        "what is my name",
        "what's my name",
        "whats my name",
        "do you know my name",
        "do u know my name",
        "my name?",
        "name?",
    }

    if t in exact:
        return True

    if "my name" in t and any(word in t for word in {"what", "what's", "whats", "know"}):
        return True

    if t.endswith("my name"):
        return True

    return False


def is_favorite_color_query(text: str) -> bool:
    t = normalize(text)

    exact = {
        "what is my favorite color",
        "what's my favorite color",
        "whats my favorite color",
        "do you know my favorite color",
        "favorite color?",
        "my favorite color?",
        "what is my favourite colour",
        "what's my favourite colour",
        "do you know my favourite colour",
        "favourite colour?",
    }

    if t in exact:
        return True

    if "favorite color" in t:
        return True

    if "favourite colour" in t:
        return True

    return False


def is_favorite_food_query(text: str) -> bool:
    t = normalize(text)

    exact = {
        "what is my favorite food",
        "what's my favorite food",
        "whats my favorite food",
        "do you know my favorite food",
        "favorite food?",
        "my favorite food?",
    }

    if t in exact:
        return True

    if "favorite food" in t:
        return True

    return False


def is_previous_message_query(text: str) -> bool:
    t = normalize(text)

    exact = {
        "what did i say before",
        "what did i say previously",
        "what was my previous message",
        "what was my last message",
        "what did i just say",
        "my last message?",
        "previous message?",
    }

    if t in exact:
        return True

    if "previous message" in t:
        return True

    if "last message" in t:
        return True

    if "did i say before" in t:
        return True

    return False


def is_history_query(text: str) -> bool:
    t = normalize(text)

    exact = {
        "what did we talk about",
        "summarize conversation",
        "summarise conversation",
        "what have we discussed",
        "give me summary",
        "conversation summary",
        "history summary",
    }

    if t in exact:
        return True

    if "summarize conversation" in t:
        return True

    if "summarise conversation" in t:
        return True

    if "conversation summary" in t:
        return True

    if "what did we talk about" in t:
        return True

    if "what have we discussed" in t:
        return True

    return False