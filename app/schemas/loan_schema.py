import re
from pydantic import ValidationError
from langchain_mistralai import ChatMistralAI
from app.utils.ml_response import predict_loan_approval, ContentValidation


def llm():
    return ChatMistralAI(model="mistral-small-2603", temperature=0)


# One regex per field. Matches the "Label: value" lines the frontend sends,
# and is loose enough to also catch reasonably-formatted typed chat.
FIELD_PATTERNS = {
    "no_of_dependents": r"depend(?:ent)?s?\s*:\s*([0-9]+)",
    "education": r"education\s*:\s*([A-Za-z ]+)",
    "self_employed": r"self[\s\-]?employed\s*:\s*([A-Za-z]+)",
    "annual_income": r"annual income\s*:\s*([0-9]+(?:\.[0-9]+)?)",
    "loan_amount": r"loan amount\s*:\s*([0-9]+(?:\.[0-9]+)?)",
    "loan_term": r"loan term[^:]*:\s*([0-9]+)",
    "cibil_score": r"cibil score\s*:\s*([0-9]+)",
    "residential_assets_value": r"residential assets?[^:]*:\s*([0-9]+(?:\.[0-9]+)?)",
    "commercial_assets_value": r"commercial assets?[^:]*:\s*([0-9]+(?:\.[0-9]+)?)",
    "luxury_assets_value": r"luxury assets?[^:]*:\s*([0-9]+(?:\.[0-9]+)?)",
    "bank_asset_value": r"bank assets?[^:]*:\s*([0-9]+(?:\.[0-9]+)?)",
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


def extract_loan_details(user_input: str):
    """
    Parse loan fields out of free-form text (no input() calls, so this
    works fine inside an HTTP request handler).

    Returns:
        (details_dict_with_prediction, [])   -> everything was present and valid
        (None, [missing_field_labels...])     -> one or more fields are missing/invalid
    """
    found = {}
    missing_keys = []

    for key, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if not match:
            missing_keys.append(key)
            continue
        raw_value = match.group(1).strip()
        try:
            found[key] = FIELD_CASTS[key](raw_value)
        except ValueError:
            missing_keys.append(key)

    if missing_keys:
        return None, [FIELD_LABELS[k] for k in missing_keys]

    try:
        validated = ContentValidation(**found)
    except ValidationError as exc:
        # Surface the pydantic errors as "missing" so the assistant asks
        # the user to correct/resupply those fields rather than crashing.
        bad_fields = sorted({err["loc"][0] for err in exc.errors()})
        return None, [FIELD_LABELS.get(f, f) for f in bad_fields]

    details = validated.model_dump()
    prediction = predict_loan_approval.invoke(details)

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