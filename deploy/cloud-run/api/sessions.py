"""In-memory chat sessions (swap for Redis/Firestore in multi-instance production)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from agentloop import Agent


@dataclass
class SessionRecord:
    agent: Agent
    updated_at: float = field(default_factory=time.time)


class SessionStore:
    """
    Stores one Agent per session_id.

    Cloud Run note: in-memory sessions work for demos and min-instances=1.
    For horizontal scaling, use Redis, Firestore, or a stateless API that
    accepts full message history from the client on each request.
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self.ttl_seconds = ttl_seconds

    def create(self, agent: Agent) -> str:
        self._purge_expired()
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = SessionRecord(agent=agent)
        return session_id

    def get(self, session_id: str) -> Agent | None:
        self._purge_expired()
        record = self._sessions.get(session_id)
        if record is None:
            return None
        record.updated_at = time.time()
        return record.agent

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [
            sid
            for sid, record in self._sessions.items()
            if now - record.updated_at > self.ttl_seconds
        ]
        for sid in expired:
            del self._sessions[sid]
