"""
Interactive multi-turn chatbot powered by agentloop.

Mock mode (no API key):
    python examples/chatbot.py --mock

Live mode (OpenAI-compatible API):
    set OPENAI_API_KEY=sk-...
    python examples/chatbot.py

Commands during chat:
    /quit or /exit  — leave
    /reset          — clear conversation memory
    /history        — show message count
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow running as: python examples/chatbot.py
sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import create_chat_agent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="agentloop chatbot example")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force offline mock provider (no API key)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Force live OpenAI-compatible provider (requires OPENAI_API_KEY)",
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


async def chat_loop(mode: str) -> None:
    agent = create_chat_agent(mode=mode)
    using_mock = mode == "mock" or (
        mode == "auto" and not __import__("os").environ.get("OPENAI_API_KEY")
    )

    print("=" * 50)
    print("  agentloop chatbot")
    print(f"  Mode: {'mock (offline)' if using_mock else 'live (OpenAI-compatible)'}")
    print("  Commands: /quit  /reset  /history")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        lowered = user_input.lower()
        if lowered in ("/quit", "/exit", "quit", "exit"):
            print("Bye!")
            break
        if lowered == "/reset":
            agent.reset()
            print("Conversation cleared.")
            continue
        if lowered == "/history":
            count = len(agent.loop.memory.messages)
            print(f"{count} message(s) in memory.")
            continue

        result = await agent.run(user_input)
        print(f"\nAssistant: {result.answer}")

        if result.stopped_reason == "max_iterations":
            print("(Stopped: hit max tool iterations.)")


def main() -> None:
    args = parse_args()
    mode = resolve_mode(args)
    asyncio.run(chat_loop(mode))


if __name__ == "__main__":
    main()
