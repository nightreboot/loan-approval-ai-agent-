from dotenv import load_dotenv
load_dotenv()
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.utils.llm_response import extract_text, get_openrouter_llm
from app.core.memory import memory  # shared instance — keeps chat/loan context in sync


def get_llm():
    return get_openrouter_llm()


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
