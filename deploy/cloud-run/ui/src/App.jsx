import { useEffect, useRef, useState } from "react";
import {
  checkHealth,
  clearSessionId,
  createSession,
  getStoredSessionId,
  sendMessage,
} from "./api.js";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! Ask me anything about the knowledge base. I use Pinecone + agentloop when configured.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(getStoredSessionId());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function ensureSession() {
    if (sessionId) return sessionId;
    const id = await createSession();
    setSessionId(id);
    return id;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    try {
      const sid = await ensureSession();
      const data = await sendMessage(text, sid);
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          meta: data.rag_enabled ? "Pinecone RAG" : "Mock KB",
        },
      ]);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function handleNewChat() {
    clearSessionId();
    setSessionId(null);
    setError("");
    setMessages([
      {
        role: "assistant",
        text: "New conversation started. What would you like to know?",
      },
    ]);
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>agentloop Chat</h1>
          <p className="subtitle">React UI → Cloud Run API → agentloop + Pinecone</p>
        </div>
        <div className="header-actions">
          {health && (
            <span className={`badge ${health.rag_live ? "live" : "mock"}`}>
              {health.rag_live ? "Pinecone live" : "Mock KB"}
            </span>
          )}
          <button type="button" className="secondary" onClick={handleNewChat}>
            New chat
          </button>
        </div>
      </header>

      <main className="chat">
        {messages.map((msg, index) => (
          <div key={index} className={`bubble ${msg.role}`}>
            <div className="bubble-text">{msg.text}</div>
            {msg.meta && <div className="bubble-meta">{msg.meta}</div>}
          </div>
        ))}
        {loading && (
          <div className="bubble assistant">
            <div className="bubble-text typing">Thinking…</div>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      {error && <div className="error">{error}</div>}

      <form className="composer" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ask about docs, deployment, Pinecone…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
