import pandas as pd
import joblib
from pathlib import Path
from math import isfinite
from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "Loan_Aprroval.pkl"
model = joblib.load(MODEL_PATH)


class ContentValidation(BaseModel):

    no_of_dependents: int = Field(
        ...,
        ge=0,
        description="Number of people dependent on the applicant's income"
    )

    education: str = Field(
        ...,
        description="Graduate or Not Graduate"
    )

    self_employed: str = Field(
        ...,
        description="Yes or No"
    )

    annual_income: float = Field(
        ...,
        gt=0,
        description="Annual income"
    )

    loan_amount: float = Field(
        ...,
        gt=0,
        description="Requested loan amount"
    )

    loan_term: int = Field(
        ...,
        gt=0,
        description="Loan term"
    )

    cibil_score: int = Field(
        ...,
        ge=300,
        le=900,
        description="CIBIL score between 300 and 900"
    )

    residential_assets_value: float = Field(
        ...,
        ge=0,
        description="Residential assets value"
    )

    commercial_assets_value: float = Field(
        ...,
        ge=0,
        description="Commercial assets value"
    )

    luxury_assets_value: float = Field(
        ...,
        ge=0,
        description="Luxury assets value"
    )

    bank_asset_value: float = Field(
        ...,
        ge=0,
        description="Bank asset value"
    )


    @field_validator("education")
    @classmethod
    def validate_education(cls, value):

        value = value.strip().title()

        if value not in ["Graduate", "Not Graduate"]:
            raise ValueError(
                "Education must be either 'Graduate' or 'Not Graduate'"
            )

        return value

    @field_validator("self_employed")
    @classmethod
    def validate_self_employed(cls, value):

        value = value.strip().title()

        if value not in ["Yes", "No"]:
            raise ValueError(
                "self_employed must be either 'Yes' or 'No'"
            )

        return value


    @field_validator(
        "annual_income",
        "loan_amount",
        "residential_assets_value",
        "commercial_assets_value",
        "luxury_assets_value",
        "bank_asset_value"
    )
    @classmethod
    def validate_finite_values(cls, value):

        if not isfinite(value):
            raise ValueError(
                "Value must be a valid finite number"
            )

        return value


@tool(args_schema=ContentValidation)
def predict_loan_approval(
    no_of_dependents: int,
    education: str,
    self_employed: str,
    annual_income: float,
    loan_amount: float,
    loan_term: int,
    cibil_score: int,
    residential_assets_value: float,
    commercial_assets_value: float,
    luxury_assets_value: float,
    bank_asset_value: float
):
    """
    Predict whether a loan application will be approved or rejected.
    """

    input_data = pd.DataFrame([{

        "no_of_dependents": no_of_dependents,

        "education": education,

        "self_employed": self_employed,

        "income_annum": annual_income,

        "loan_amount": loan_amount,

        "loan_term": loan_term,

        "cibil_score": cibil_score,

        "residential_assets_value": residential_assets_value,

        "commercial_assets_value": commercial_assets_value,

        "luxury_assets_value": luxury_assets_value,

        "bank_asset_value": bank_asset_value
    }])

    prediction = model.predict(input_data)[0]

    probabilities = model.predict_proba(input_data)[0][0]

    return {
        "status" : prediction,
        "Approved_probabilities" : probabilities
    }

