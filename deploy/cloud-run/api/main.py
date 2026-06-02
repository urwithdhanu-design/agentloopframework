"""FastAPI service for Cloud Run — agentloop + Pinecone RAG chatbot."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api.agent_factory import create_rag_agent
from api.rag import KnowledgeBase
from api.sessions import SessionStore

app = FastAPI(title="agentloop RAG Chatbot", version="1.0.0")

cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kb = KnowledgeBase()
sessions = SessionStore(ttl_seconds=int(os.environ.get("SESSION_TTL_SECONDS", "3600")))

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    rag_enabled: bool
    iterations: int


class SessionResponse(BaseModel):
    session_id: str


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "rag_live": kb.is_live,
        "openai_configured": bool(os.environ.get("OPENAI_API_KEY")),
        "pinecone_configured": bool(os.environ.get("PINECONE_API_KEY")),
    }


@app.post("/api/session", response_model=SessionResponse)
async def create_session() -> SessionResponse:
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the server.",
        )
    agent = create_rag_agent(kb)
    session_id = sessions.create(agent)
    return SessionResponse(session_id=session_id)


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    removed = sessions.delete(session_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    agent = sessions.get(body.session_id) if body.session_id else None
    if agent is None:
        agent = create_rag_agent(kb)
        session_id = sessions.create(agent)
    else:
        session_id = body.session_id  # type: ignore[assignment]

    result = await agent.run(body.message.strip())

    return ChatResponse(
        session_id=session_id,
        answer=result.answer,
        rag_enabled=kb.is_live,
        iterations=result.iterations,
    )


# Serve React UI (built into /static by Docker)
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404)
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
