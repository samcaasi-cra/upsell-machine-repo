from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services import agent

router = APIRouter(tags=["agent"])


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.get("/agent/status")
def agent_status() -> dict:
    return {"enabled": agent.is_configured(), "provider": agent.active_provider()}


@router.post("/agent/chat")
def agent_chat(payload: ChatRequest) -> dict:
    if not agent.is_configured():
        raise HTTPException(
            status_code=503,
            detail="No model configured — set ANTHROPIC_API_KEY or OPENAI_API_KEY in backend/.env.",
        )
    if not payload.messages:
        raise HTTPException(status_code=400, detail="No messages provided.")
    try:
        return agent.run([m.model_dump() for m in payload.messages])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent failed: {exc}") from exc
