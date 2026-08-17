import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import storage
from ..models import QueuedAction
from ..services import agent, briefing

router = APIRouter(tags=["agent"])


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.get("/agent/status")
def agent_status() -> dict:
    return {"enabled": agent.is_configured(), "provider": agent.active_provider()}


def _sdk_missing(exc: ModuleNotFoundError) -> HTTPException:
    """A missing SDK almost always means the server was started with the wrong Python.

    is_configured() only checks that an API key is set, so the guard above passes and
    the import fails later with a bare "No module named 'openai'" -- which says nothing
    about the actual cause. Name the interpreter, because that's the fix.
    """
    return HTTPException(
        status_code=503,
        detail=(
            f"The '{exc.name}' package isn't installed in the Python running this server "
            f"({sys.executable}). This usually means uvicorn was started with the system "
            f"Python instead of the project venv. Restart with: "
            f"backend/.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000"
        ),
    )


@router.get("/today")
def today(refresh: bool = False) -> dict:
    """The agent's daily worklist. Cached per day unless refresh=true."""
    if not agent.is_configured():
        raise HTTPException(
            status_code=503,
            detail="No model configured — set ANTHROPIC_API_KEY or OPENAI_API_KEY in backend/.env.",
        )
    try:
        return briefing.build(force=refresh)
    except ModuleNotFoundError as exc:
        raise _sdk_missing(exc) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Couldn't build today's briefing: {exc}") from exc


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
    except ModuleNotFoundError as exc:
        raise _sdk_missing(exc) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent failed: {exc}") from exc


@router.get("/actions")
def list_actions() -> list[QueuedAction]:
    """Everything the agent has decided to act on, most recent first -- the durable
    record of the "act" step, independent of any one Today briefing or Ask reply."""
    return sorted(storage.load_queued_actions(), key=lambda a: a.created_at, reverse=True)


@router.post("/actions/{action_id}/approve")
def approve_action(action_id: str) -> QueuedAction:
    updated = storage.update_action_status(action_id, "approved")
    if updated is None:
        raise HTTPException(status_code=404, detail=f"No queued action {action_id}")
    return updated


@router.post("/actions/{action_id}/dismiss")
def dismiss_action(action_id: str) -> QueuedAction:
    updated = storage.update_action_status(action_id, "dismissed")
    if updated is None:
        raise HTTPException(status_code=404, detail=f"No queued action {action_id}")
    return updated
