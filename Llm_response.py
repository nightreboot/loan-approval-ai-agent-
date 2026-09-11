def extract_text(content) -> str:
    """
    Safely turn an LLM message's `.content` into a plain string.

    ChatMistralAI always returned a plain string, but Gemini (via
    langchain_google_genai) can return `.content` as a list of parts,
    e.g. [{"type": "text", "text": "..."}], instead of a plain string.
    Calling `.strip()` / string ops directly on that list blows up with
    "'list' object has no attribute 'strip'". This normalizes either
    shape into one string.
    """
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        return "".join(parts)

    return str(content)
