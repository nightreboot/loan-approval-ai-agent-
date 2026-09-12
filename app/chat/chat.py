from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.utils.llm_response import extract_text
from app.core.memory import memory  # shared instance — keeps chat/loan context in sync
import os

OPENROUTER_MODEL = "google/gemma-4-31b-it:free"


def get_llm():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing in .env file")

    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://loan-approval-ai-agent-1.onrender.com",
            "X-Title": "Loan Approval AI Assistant",
        },
    )


def model_response(query: str) -> str:
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Give all answers of the user."
        ),
        MessagesPlaceholder(variable_name="history"),
        (
            "human",
            "{question}"
        )
    ])

    load_history = RunnableLambda(lambda x: {
        "history": memory.load_memory_variables({})
        .get("history", []),
        "question": x['question']
    })

    chain = (RunnablePassthrough() | load_history | prompt | llm)

    response = chain.invoke({"question": query})
    reply_text = extract_text(response.content)

    memory.save_context(
        {"input": query},
        {"output": reply_text}
    )

    return reply_text
