from dotenv import load_dotenv
load_dotenv()
from langchain_classic.memory import ConversationBufferMemory
from langchain_mistralai import ChatMistralAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os


def get_llm():
    return ChatMistralAI(api_key=os.getenv("MISTRAL_API_KEY"), model_name="mistral-small-2603")


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

    memory.save_context(
        {"input": query},
        {"output": response.content}
    )

    return response.content