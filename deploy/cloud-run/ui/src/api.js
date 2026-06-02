const SESSION_KEY = "agentloop_session_id";

/** API base URL — empty string uses same origin (Cloud Run single container). */
const API_BASE = import.meta.env.VITE_API_URL || "";

export function getStoredSessionId() {
  return localStorage.getItem(SESSION_KEY);
}

export function storeSessionId(sessionId) {
  localStorage.setItem(SESSION_KEY, sessionId);
}

export function clearSessionId() {
  localStorage.removeItem(SESSION_KEY);
}

export async function createSession() {
  const response = await fetch(`${API_BASE}/api/session`, { method: "POST" });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create session (${response.status})`);
  }
  const data = await response.json();
  storeSessionId(data.session_id);
  return data.session_id;
}

export async function sendMessage(message, sessionId) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Chat failed (${response.status})`);
  }

  const data = await response.json();
  storeSessionId(data.session_id);
  return data;
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error("Health check failed");
  return response.json();
}
