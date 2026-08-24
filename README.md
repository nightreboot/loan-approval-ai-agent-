# Loan Approval AI Assistant

An AI-powered assistant that predicts loan approval using a trained ML model, and explains the result in natural language through an LLM. General questions are handled as normal conversation. Built with **FastAPI**, **LangGraph**, **LangChain**, and **Mistral AI**, containerized with **Docker**.

---

## ✨ Features

- 🤖 **Smart routing** — a LangGraph agent classifies each message and routes it to either the loan-approval flow or general chat
- 📊 **ML-based loan prediction** — a trained scikit-learn model predicts loan approval/rejection from applicant details
- 💬 **Natural language explanations** — an LLM (Mistral) explains the ML model's prediction in plain language, without overriding it
- 🧠 **Conversation memory** — remembers context within a session for both the loan flow and general chat
- 🌐 **REST API** — FastAPI backend with interactive Swagger docs
- 🎨 **Simple frontend** — HTML/CSS/JS chat interface
- 🐳 **Dockerized** — runs identically on any machine
- 🚀 **CI/CD ready** — deployable via GitHub + Render (or AWS)

---

## 🏗️ Architecture

```
User message
     │
     ▼
FastAPI (/chat endpoint)
     │
     ▼
LangGraph Agent (agent.py)
     │
     ├── classify_intent_node  ──► decides: "loan" or "chat"
     │
     ├── loan_node  ──► core/details.py → utils/ml_response.py
     │                  (collects applicant info, runs ML model,
     │                   explains prediction via core/prompts.py)
     │
     └── chat_node  ──► normal_chat.py
                        (general purpose conversation)
```

**State, Nodes, Edges (LangGraph):**
- **State** — `AgentState` carries `user_input`, `route`, and `response` between nodes
- **Nodes** — `classify_intent_node`, `loan_node`, `chat_node`
- **Edges** — a conditional edge out of `classify_intent` routes to either `loan_node` or `chat_node`

---

## 📁 Project Structure

```
loan-approval-ai-agent/
├── api.py                 # FastAPI app (HTTP entry point)
├── agent.py                # LangGraph agent — state, nodes, edges, routing
├── main.py                 # CLI entry point (terminal chat, no HTTP)
├── normal_chat.py           # General purpose chat (non-loan messages)
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── Loan_Aprroval.pkl        # Trained ML model (not committed to git)
├── core/
│   ├── details.py           # Collects applicant info, calls the ML tool
│   ├── memory.py            # Loan-flow conversation memory + explanation chain
│   └── prompts.py           # System prompt for explaining predictions
├── utils/
│   └── ml_response.py       # ML model loading + predict_loan_approval tool
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| Agent orchestration | LangGraph |
| LLM framework | LangChain |
| LLM provider | Mistral AI (`mistral-small-2603`) |
| ML model | scikit-learn (loaded via joblib) |
| Data validation | Pydantic |
| Containerization | Docker |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Render (Docker-based), GitHub Actions for CI/CD |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Docker Desktop (for containerized run)
- A [Mistral AI](https://console.mistral.ai/) API key

### 1. Clone the repository
```bash
git clone https://github.com/nightreboot/loan-approval-ai-agent-.git
cd loan-approval-ai-agent-
```

### 2. Set up environment variables
Create a `.env` file in the project root:
```
MISTRAL_API_KEY=your-actual-api-key-here
```
> No spaces around `=`, no quotes around the value.

### 3a. Run locally (without Docker)
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py                # CLI chat
# or
uvicorn api:app --reload      # HTTP API
```

### 3b. Run with Docker
```bash
docker build -t loan-approval-backend .
docker run -p 8000:8000 --env-file .env loan-approval-backend
```

### 4. Try it out
Open **http://localhost:8000/docs** for the interactive Swagger UI, or send a request directly:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

---

## 📡 API Reference

### `GET /health`
Liveness check.
```json
{ "status": "ok" }
```

### `POST /chat`
Send one message to the agent.

**Request:**
```json
{ "message": "I want to check my loan approval" }
```

**Response:**
```json
{ "response": "..." }
```

---

## ⚠️ Disclaimer

This assistant provides an **ML-based prediction only** and does not guarantee the final decision of any bank or financial institution. It is intended for educational/demonstration purposes.

---

## 📄 License

This project is for educational purposes. Add a license of your choice (MIT, Apache 2.0, etc.) if you plan to distribute it publicly.