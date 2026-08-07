from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import customers, decision_makers, scores, upsell, usage

app = FastAPI(title="Upsell Machine — Project 5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(scores.router)
app.include_router(usage.router)
app.include_router(decision_makers.router)
app.include_router(upsell.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
