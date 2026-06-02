# Examples

Runnable demos built on **agentloop**. Run from the repo root.

## Quick reference

| Example | What it shows | Command |
|---------|---------------|---------|
| `basic_mock.py` | Single-shot agent + tools, no API key | `python examples/basic_mock.py` |
| `openai_agent.py` | Live LLM + tools | `python examples/openai_agent.py` |
| `custom_provider.py` | Custom LLM provider | `python examples/custom_provider.py` |
| **`chatbot.py`** | **Multi-turn interactive chat** | `python examples/chatbot.py --mock` |
| **`voice_agent.py`** | **Voice in / voice out agent** | `python examples/voice_agent.py --text --mock` |

## Chatbot

Interactive REPL that keeps conversation memory across turns.

```powershell
# Offline (no API key)
python examples/chatbot.py --mock

# Live (set OPENAI_API_KEY first)
python examples/chatbot.py --live
```

Try asking:
- "What time is it?"
- "What is 128 divided by 8?"
- "Hello!"

Commands: `/quit`, `/reset`, `/history`

## Voice agent

Same agent loop with speech input and spoken replies.

```powershell
# Easiest start — type instead of speak, no API key
python examples/voice_agent.py --text --mock

# Real voice (install extras first)
pip install -e ".[voice,openai]"
python examples/voice_agent.py --mock
```

### Voice dependencies

```powershell
pip install -e ".[voice]"
```

- **SpeechRecognition** — captures microphone audio and transcribes (uses Google's free web API by default).
- **pyttsx3** — speaks responses locally (works offline on Windows).
- **PyAudio** — required for the microphone. On Windows, if `pip install pyaudio` fails:

  ```powershell
  pip install pipwin
  pipwin install pyaudio
  ```

  Or use `--text` to skip the microphone entirely.

### Environment variables (live mode)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | API key for live LLM |
| `OPENAI_BASE_URL` | Optional custom endpoint (Ollama, Azure, etc.) |
| `OPENAI_MODEL` | Model name (default `gpt-4o-mini`) |
