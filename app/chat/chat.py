from dotenv import load_dotenv
load_dotenv()
from langchain_classic.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.utils.llm_response import extract_text
import os


def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing in .env file")

    return ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=api_key,
    )


# Module level so it persists across calls, same reasoning as core/memory.py.
memory = ConversationBufferMemory(
    return_messages=True
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
