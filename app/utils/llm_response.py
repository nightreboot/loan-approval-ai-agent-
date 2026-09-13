import os
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda


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


# Tried in order. OpenRouter's free-tier models share a pool and get
# rate-limited (HTTP 429) or occasionally error out upstream — if the first
# one is busy, we fall through to the next instead of failing the request.
#
# Ling 3.0 Flash Fin is a finance-tuned model (trained on financial data,
# built for investment/financial reasoning workflows) — a strong match for
# a loan-approval assistant, so it goes first. Nemotron 3 Ultra is a very
# large, strong general-reasoning backup; the rest are solid general models.
FALLBACK_MODELS = (
    "inclusionai/ling-3.0-flash-fin:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-31b-it:free",
    "nex-agi/nex-n2.5-pro:free",
)

_OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://loan-approval-ai-agent-1.onrender.com",
    "X-Title": "Loan Approval AI Assistant",
}


def get_openrouter_llm(temperature: float = 0):
    """
    Returns a Runnable that behaves like a chat model for both direct
    `.invoke()` calls and LCEL chains (`prompt | get_openrouter_llm()`),
    but tries several free OpenRouter models in order and automatically
    falls back to the next one if the current one is rate-limited or
    returns an error.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing in .env file")

    def _invoke(input_value):
        last_exc = None
        for model_name in FALLBACK_MODELS:
            try:
                client = ChatOpenAI(
                    model=model_name,
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=temperature,
                    default_headers=_OPENROUTER_HEADERS,
                )
                return client.invoke(input_value)
            except Exception as exc:
                last_exc = exc
                continue
        # every model in the chain failed — surface the last error
        raise last_exc

    return RunnableLambda(_invoke)
