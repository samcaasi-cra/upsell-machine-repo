import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import auth, config
from .routers import agent, customers, decision_makers, news, opportunities, scores, upsell, usage
from .services import scheduler, web_research


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(scheduler.daily_loop())
    yield
    task.cancel()


app = FastAPI(title="Upsell Machine — Project 5", lifespan=lifespan)

# Extra origins (the deployed frontend) come from the environment; localhost is always
# allowed so local development needs no configuration.
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registered after CORS so preflight requests are answered before the gate runs.
app.middleware("http")(auth.auth_middleware)

app.include_router(customers.router)
app.include_router(scores.router)
app.include_router(usage.router)
app.include_router(decision_makers.router)
app.include_router(news.router)
app.include_router(upsell.router)
app.include_router(opportunities.router)
app.include_router(agent.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "auth_required": auth.is_enabled(), "csm_name": config.CSM_NAME}


class LoginRequest(BaseModel):
    password: str


@app.post("/login")
def login(payload: LoginRequest) -> dict:
    if not auth.is_enabled():
        return {"token": "", "auth_required": False}
    if not auth.check_password(payload.password):
        return JSONResponse(status_code=401, content={"detail": "Incorrect password"})
    return {"token": auth.issue_token(), "auth_required": True}


@app.get("/capabilities")
def capabilities() -> dict:
    """Lets the UI show or disable features that depend on optional configuration."""
    return {"auto_research": web_research.is_configured()}


@app.get("/research-status")
def research_status() -> dict:
    return scheduler.status()


@app.post("/research-run-now")
async def research_run_now() -> dict:
    """Manual trigger for the same batch the daily loop runs."""
    if not web_research.is_configured():
        return {"status": "disabled", "detail": "Needs an OPENAI_API_KEY in backend/.env."}
    # Fire and forget: the batch takes minutes, far longer than a sensible HTTP wait.
    asyncio.create_task(scheduler.run_batch(reason="manual"))
    return {"status": "started"}
