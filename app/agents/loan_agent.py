from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from app.schemas.loan_schema import llm
from app.core.memory import Memories
from app.chat.chat import model_response
from app.utils.llm_response import extract_text

class AgentState(TypedDict):
    user_input: str
    route: Literal["loan", "chat", ""]
    response: str
    open_form: bool


def classify_intent_node(state: AgentState) -> AgentState:
    """Decide whether this message is a loan-approval request or general chat."""

    user_input = state["user_input"]

    classifier_prompt = f"""
    Classify the user's message into exactly one category:

    - "loan": the user wants to check loan eligibility/approval, apply for a
      loan, ask about loan prediction, or is continuing a loan application.
    - "chat": anything else (general questions, greetings, small talk).

    Respond with only one word: loan or chat.

    User message: {user_input}
    """

    result = llm().invoke(classifier_prompt)
    label = extract_text(result.content).strip().lower()

    if "loan" in label:
        route = "loan"
    else:
        route = "chat"

    return {**state, "route": route}


def loan_node(state: AgentState) -> AgentState:
    """Run the loan-application intake + ML prediction + explanation flow."""
    response, open_form = Memories(state["user_input"])
    return {**state, "response": response, "open_form": open_form}


def chat_node(state: AgentState) -> AgentState:
    """Handle everything that isn't loan-related as normal conversation."""
    response = model_response(state["user_input"])
    return {**state, "response": response, "open_form": False}


def route_decision(state: AgentState) -> str:
    """Read state["route"] (set by classify_intent_node) and pick the next node."""
    return state["route"]


graph = StateGraph(AgentState)

graph.add_node("classify_intent", classify_intent_node)
graph.add_node("loan_node", loan_node)
graph.add_node("chat_node", chat_node)

graph.add_edge(START, "classify_intent")

graph.add_conditional_edges(
    "classify_intent",
    route_decision,
    {
        "loan": "loan_node",
        "chat": "chat_node",
    },
)

graph.add_edge("loan_node", END)
graph.add_edge("chat_node", END)

app = graph.compile()


def run_agent(user_input: str) -> tuple[str, bool]:
    """Convenience wrapper: run one turn through the graph and return
    (reply_text, open_form) — open_form tells the caller whether the
    structured loan slip should be shown to the user."""
    result = app.invoke({
        "user_input": user_input,
        "route": "",
        "response": "",
        "open_form": False,
    })
    return result["response"], result["open_form"]


if __name__ == "__main__":
    print("==========================================")
    print("   LOAN APPROVAL AGENT (standalone test)   ")
    print("==========================================")
    print("\nType 'exit' at any prompt to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("exit", "quit"):
            print("\nAssistant: Goodbye!")
            break

        response, open_form = run_agent(user_input)
        print(f"\nAssistant:\n{response}\n")
        if open_form:
            print("[frontend would open the loan slip here]\n")
