from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os
import sys

# Add backend dir to path
sys.path.insert(0, os.path.dirname(__file__))

from src.agent import run_agent
from src.config import GROQ_API_KEY, MONDAY_API_TOKEN, DEALS_BOARD_ID, WORK_ORDERS_BOARD_ID

app = FastAPI(title="Monday.com BI Agent", version="1.0.0")

# CORS — allow all for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    trace: list


@app.get("/")
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "Monday.com BI Agent API running. Frontend not found."}


@app.get("/health")
async def health():
    """Check configuration status."""
    issues = []
    if not GROQ_API_KEY:
        issues.append("GROQ_API_KEY not set")
    if not MONDAY_API_TOKEN:
        issues.append("MONDAY_API_TOKEN not set")
    if not DEALS_BOARD_ID:
        issues.append("DEALS_BOARD_ID not set")
    if not WORK_ORDERS_BOARD_ID:
        issues.append("WORK_ORDERS_BOARD_ID not set")

    return {
        "status": "ok" if not issues else "misconfigured",
        "issues": issues,
        "config": {
            "groq_key_set": bool(GROQ_API_KEY),
            "monday_token_set": bool(MONDAY_API_TOKEN),
            "deals_board_id": DEALS_BOARD_ID or "NOT SET",
            "work_orders_board_id": WORK_ORDERS_BOARD_ID or "NOT SET",
        },
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint — runs the agent and returns answer + trace."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if not GROQ_API_KEY or not MONDAY_API_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Server not configured. Check /health for details.",
        )

    try:
        result = run_agent(request.message)
        return ChatResponse(answer=result["answer"], trace=result["trace"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sample-questions")
async def sample_questions():
    """Return sample questions to show in the UI."""
    return {
        "questions": [
            "What is our total ARR across all deals?",
            "Which deals are in the energy sector?",
            "Show me all work orders with high priority",
            "What's our pipeline breakdown by stage?",
            "Which accounts have both open deals and work orders?",
            "How many deals closed this quarter?",
            "What are the top 5 deals by value?",
            "Show work orders that are overdue or at risk",
        ]
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)