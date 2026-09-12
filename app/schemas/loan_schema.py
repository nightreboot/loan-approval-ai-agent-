import os
import re
from pydantic import ValidationError
from langchain_openai import ChatOpenAI
from app.utils.ml_response import predict_loan_approval, ContentValidation

OPENROUTER_MODEL = "google/gemma-4-31b-it:free"


def llm():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing in .env file")

    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        # OpenRouter recommends these so requests are attributed to your app
        # (helps with their rate limiting on free models) — optional but safe.
        default_headers={
            "HTTP-Referer": "https://loan-approval-ai-agent-1.onrender.com",
            "X-Title": "Loan Approval AI Assistant",
        },
    )


# One regex per field. Loose enough to catch reasonably-formatted typed
# chat, e.g. "annual income: 800000" or "cibil score is 720".
FIELD_PATTERNS = {
    "no_of_dependents": r"depend(?:ent)?s?\s*:?\s*(?:is|are)?\s*([0-9]+)",
    "education": r"education\s*:?\s*(?:is)?\s*([A-Za-z ]+)",
    "self_employed": r"self[\s\-]?employed\s*:?\s*(?:is)?\s*([A-Za-z]+)",
    "annual_income": r"annual income\s*:?\s*(?:is)?\s*([0-9]+(?:\.[0-9]+)?)",
    "loan_amount": r"loan amount\s*:?\s*(?:is)?\s*([0-9]+(?:\.[0-9]+)?)",
    "loan_term": r"loan term[^:0-9]*:?\s*([0-9]+)",
    "cibil_score": r"cibil score\s*:?\s*(?:is)?\s*([0-9]+)",
    "residential_assets_value": r"residential assets?[^:0-9]*:?\s*([0-9]+(?:\.[0-9]+)?)",
    "commercial_assets_value": r"commercial assets?[^:0-9]*:?\s*([0-9]+(?:\.[0-9]+)?)",
    "luxury_assets_value": r"luxury assets?[^:0-9]*:?\s*([0-9]+(?:\.[0-9]+)?)",
    "bank_asset_value": r"bank assets?[^:0-9]*:?\s*([0-9]+(?:\.[0-9]+)?)",
}

FIELD_CASTS = {
    "no_of_dependents": int,
    "education": str,
    "self_employed": str,
    "annual_income": float,
    "loan_amount": float,
    "loan_term": int,
    "cibil_score": int,
    "residential_assets_value": float,
    "commercial_assets_value": float,
    "luxury_assets_value": float,
    "bank_asset_value": float,
}

# Friendly names used when telling the user what's still missing.
FIELD_LABELS = {
    "no_of_dependents": "Number of Dependents",
    "education": "Education",
    "self_employed": "Self Employed",
    "annual_income": "Annual Income",
    "loan_amount": "Loan Amount",
    "loan_term": "Loan Term",
    "cibil_score": "CIBIL Score",
    "residential_assets_value": "Residential Assets Value",
    "commercial_assets_value": "Commercial Assets Value",
    "luxury_assets_value": "Luxury Assets Value",
    "bank_asset_value": "Bank Asset Value",
}

# Fields collected so far for the loan application currently "in progress".
# Persists across turns (module-level, same pattern as the memory buffers)
# so the user never has to repeat a field they already gave in an earlier
# message — this is what lets the assistant collect the 11 fields one at a
# time over the conversation instead of needing them all in one message.
_collected: dict = {}


def extract_loan_details(user_input: str):
    """
    Parse loan fields out of free-form chat text and merge them into
    whatever has already been collected for this in-progress application.

    Returns:
        (details_dict_with_prediction, [])
            -> everything was present and valid; application is complete
               and _collected is reset for the next one.
        (None, [missing_field_labels...])
            -> one or more fields are still missing/invalid; the assistant
               should ask the user for just those, conversationally.
    """
    global _collected

    for key, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if not match:
            continue
        raw_value = match.group(1).strip()
        try:
            _collected[key] = FIELD_CASTS[key](raw_value)
        except ValueError:
            # Leave whatever was previously collected (if anything) alone;
            # this value just didn't parse, so it'll show up as missing.
            pass

    missing_keys = [k for k in FIELD_PATTERNS if k not in _collected]

    if missing_keys:
        return None, [FIELD_LABELS[k] for k in missing_keys]

    try:
        validated = ContentValidation(**_collected)
    except ValidationError as exc:
        # Surface the pydantic errors as "missing" so the assistant asks
        # the user to correct/resupply those fields rather than crashing.
        bad_fields = sorted({err["loc"][0] for err in exc.errors()})
        for f in bad_fields:
            _collected.pop(f, None)
        return None, [FIELD_LABELS.get(f, f) for f in bad_fields]

    details = validated.model_dump()
    prediction = predict_loan_approval.invoke(details)

    _collected = {}  # application complete — start clean for the next one

    return {**details, "prediction": prediction}, []


def All_Details():
    """Interactive CLI version — only safe to call from a real terminal
    (e.g. `python loan_agent.py` standalone testing), never from the API."""
    print("==========================================")
    print("       LOAN APPROVAL AI ASSISTANT         ")
    print("==========================================")

    print("\nAssistant:")
    print("\nPlease enter your loan information:\n")

    no_of_dependents = int(input("Number of Dependents: "))
    education = input("Education (Graduate/Not Graduate): ")
    self_employed = input("Self Employed (Yes/No): ")
    annual_income = float(input("Annual Income: "))
    loan_amount = float(input("Loan Amount: "))
    loan_term = int(input("Loan Term: "))
    cibil_score = int(input("CIBIL Score: "))
    residential_assets_value = float(input("Residential Assets Value: "))
    commercial_assets_value = float(input("Commercial Assets Value: "))
    luxury_assets_value = float(input("Luxury Assets Value: "))
    bank_asset_value = float(input("Bank Asset Value: "))

    input_details = {
        "no_of_dependents": no_of_dependents,
        "education": education,
        "self_employed": self_employed,
        "annual_income": annual_income,
        "loan_amount": loan_amount,
        "loan_term": loan_term,
        "cibil_score": cibil_score,
        "residential_assets_value": residential_assets_value,
        "commercial_assets_value": commercial_assets_value,
        "luxury_assets_value": luxury_assets_value,
        "bank_asset_value": bank_asset_value,
    }

    prediction = predict_loan_approval.invoke(input_details)

    return {**input_details, "prediction": prediction}
