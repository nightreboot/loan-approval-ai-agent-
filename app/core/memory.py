from langchain_classic.memory import ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from app.schemas.loan_schema import llm, extract_loan_details
from app.core.prompts import Prompts

load_dotenv()

memory = ConversationBufferMemory(return_messages=True)


def Memories(user_input):
    details, missing = extract_loan_details(user_input)

    chain = Prompts() | llm() | StrOutputParser()
    history = memory.load_memory_variables({})['history']

    if details is None:
        prompt_text = f"""
        The user is applying for a loan. Their message was:

        {user_input}

        The following required fields are still missing or invalid:
        {", ".join(missing)}

        Ask the user only for those missing fields. Do not ask again for
        fields that were already provided.
        """
    else:
        prompt_text = f"""
        The user submitted the following loan application:

        Number of Dependents: {details['no_of_dependents']}
        Education: {details['education']}
        Self Employed: {details['self_employed']}
        Annual Income: {details['annual_income']}
        Loan Amount: {details['loan_amount']}
        Loan Term: {details['loan_term']}
        CIBIL Score: {details['cibil_score']}
        Residential Assets Value: {details['residential_assets_value']}
        Commercial Assets Value: {details['commercial_assets_value']}
        Luxury Assets Value: {details['luxury_assets_value']}
        Bank Asset Value: {details['bank_asset_value']}

        The ML model returned this prediction:

        {details['prediction']}

        Explain the ML prediction to the user.
        Do not change the prediction.
        """

    final_response = chain.invoke({
        "history": history,
        "user_input": prompt_text,
    })

    memory.save_context(
        {"input": user_input},
        {"model_output": final_response}
    )

    print("\nResponsing......")
    return final_response