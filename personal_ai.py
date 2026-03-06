#!/usr/bin/env python3
"""A small personal AI assistant CLI.

Usage:
    export OPENAI_API_KEY=...
    python personal_ai.py
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: openai. Install with `pip install openai`."
    ) from exc

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_SYSTEM_PROMPT = (
    "You are my personal AI assistant. Be concise, practical, and friendly. "
    "Ask follow-up questions when user intent is ambiguous."
)


def load_history(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_history(path: Path, history: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")


def build_messages(system_prompt: str, history: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{"role": "system", "content": system_prompt}, *history]


def chat_once(
    client: OpenAI,
    model: str,
    system_prompt: str,
    history: list[dict[str, str]],
    user_text: str,
) -> str:
    local_history = [*history, {"role": "user", "content": user_text}]
    response = client.chat.completions.create(
        model=model,
        messages=build_messages(system_prompt, local_history),
        temperature=0.7,
    )
    content = response.choices[0].message.content or ""
    return content.strip()


def run_repl(args: argparse.Namespace) -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY before running.")
        return 1

    client = OpenAI(api_key=api_key)
    history_path = Path(args.history_file)
    history = [] if args.no_memory else load_history(history_path)

    print("Personal AI ready. Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        try:
            answer = chat_once(
                client=client,
                model=args.model,
                system_prompt=args.system_prompt,
                history=history,
                user_text=user_text,
            )
        except Exception as exc:  # pragma: no cover
            print(f"ai> Request failed: {exc}")
            continue

        print(f"ai> {answer}")

        if not args.no_memory:
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": answer})
            save_history(history_path, history)

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personal AI CLI")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name to use")
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="System prompt that defines assistant behavior",
    )
    parser.add_argument(
        "--history-file",
        default=str(Path.home() / ".personal_ai" / "history.json"),
        help="Where to persist conversation history",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable conversation memory",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_repl(args)


if __name__ == "__main__":
    raise SystemExit(main())
