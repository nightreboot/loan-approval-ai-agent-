from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.loan_agent import run_agent

app = FastAPI(
    title="Loan Approval AI Assistant API",
    description="Chat with a LangGraph agent that routes between loan-approval "
                 "prediction and general conversation.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's message")


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
def health_check():
    """Simple liveness check."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Send one message to the agent and get its reply.

    The agent internally decides whether this is a loan-approval request
    or general chat and routes it accordingly (see agent.py).
    """
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="message must not be empty")

    try:
        reply = run_agent(user_message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return ChatResponse(response=reply)