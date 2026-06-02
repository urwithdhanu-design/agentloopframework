"""
Voice chatbot powered by agentloop — speak, listen, get spoken replies.

Text mode (no microphone, works everywhere):
    python examples/voice_agent.py --text

Mock mode (offline, no API key):
    python examples/voice_agent.py --text --mock

Voice mode (microphone + speaker):
    pip install -e ".[voice,openai]"
    python examples/voice_agent.py

On Windows, if PyAudio fails to install, use --text or see examples/README.md.

Say "stop" or "quit" to exit (or Ctrl+C).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import create_chat_agent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="agentloop voice agent example")
    parser.add_argument(
        "--text",
        action="store_true",
        help="Type instead of using the microphone (recommended for first run)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force offline mock provider",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Force live OpenAI-compatible provider",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Seconds to wait for speech (voice mode only)",
    )
    return parser.parse_args()


def resolve_mode(args: argparse.Namespace) -> str:
    if args.mock and args.live:
        print("Choose only one of --mock or --live.")
        sys.exit(1)
    if args.mock:
        return "mock"
    if args.live:
        return "live"
    return "auto"


class VoiceIO:
    """Speech-to-text and text-to-speech wrappers."""

    def __init__(self, *, listen_timeout: float = 5.0) -> None:
        self.listen_timeout = listen_timeout
        self._recognizer = None
        self._microphone = None
        self._tts = None

    def _ensure_voice_deps(self) -> None:
        try:
            import speech_recognition as sr
            import pyttsx3
        except ImportError as exc:
            raise SystemExit(
                "Voice mode requires optional dependencies.\n"
                "Install with: pip install -e \".[voice]\"\n"
                "Or run with --text to type instead of speak."
            ) from exc

        self._recognizer = sr.Recognizer()
        self._microphone = sr.Microphone()
        self._tts = pyttsx3.init()
        self._tts.setProperty("rate", 175)

    def listen(self) -> str | None:
        import speech_recognition as sr

        self._ensure_voice_deps()
        assert self._recognizer is not None
        assert self._microphone is not None

        with self._microphone as source:
            print("Listening... (speak now)")
            self._recognizer.adjust_for_ambient_noise(source, duration=0.4)
            try:
                audio = self._recognizer.listen(
                    source,
                    timeout=self.listen_timeout,
                    phrase_time_limit=12,
                )
            except sr.WaitTimeoutError:
                print("(No speech detected.)")
                return None

        try:
            return self._recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("(Could not understand audio.)")
            return None
        except sr.RequestError as exc:
            print(f"(Speech recognition error: {exc})")
            return None

    def speak(self, text: str) -> None:
        self._ensure_voice_deps()
        assert self._tts is not None
        self._tts.say(text)
        self._tts.runAndWait()


async def run_session(
    *,
    mode: str,
    text_mode: bool,
    listen_timeout: float,
) -> None:
    agent = create_chat_agent(mode=mode)
    voice = VoiceIO(listen_timeout=listen_timeout)
    using_mock = mode == "mock" or (
        mode == "auto" and not __import__("os").environ.get("OPENAI_API_KEY")
    )

    print("=" * 50)
    print("  agentloop voice agent")
    print(f"  Input: {'text' if text_mode else 'microphone'}")
    print(f"  Output: {'text' if text_mode else 'speaker + text'}")
    print(f"  LLM: {'mock (offline)' if using_mock else 'live'}")
    print('  Say or type "quit" to exit')
    print("=" * 50)

    while True:
        try:
            if text_mode:
                user_input = input("\nYou: ").strip()
            else:
                user_input = voice.listen()
                if not user_input:
                    continue
                print(f"You: {user_input}")
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if user_input.lower() in ("quit", "exit", "stop", "/quit"):
            if not text_mode:
                voice.speak("Goodbye!")
            print("Bye!")
            break

        result = await agent.run(user_input)
        print(f"\nAssistant: {result.answer}")

        if not text_mode:
            voice.speak(result.answer)


def main() -> None:
    args = parse_args()
    mode = resolve_mode(args)
    asyncio.run(
        run_session(
            mode=mode,
            text_mode=args.text,
            listen_timeout=args.timeout,
        )
    )


if __name__ == "__main__":
    main()
