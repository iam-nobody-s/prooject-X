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
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from openai import OpenAI

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_SYSTEM_PROMPT = (
    "You are my personal AI assistant. Be concise, practical, and friendly. "
    "Ask follow-up questions when user intent is ambiguous."
)
DEFAULT_HISTORY_PATH = Path.home() / ".personal_ai" / "history.json"


def load_history(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    cleaned: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str):
            cleaned.append({"role": role, "content": content})
    return cleaned


def save_history(path: Path, history: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def build_messages(system_prompt: str, history: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{"role": "system", "content": system_prompt}, *history]


def make_client(api_key: str) -> "OpenAI":
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Missing dependency: openai. Install with `pip install openai`."
        ) from exc
    return OpenAI(api_key=api_key)


def chat_once(
    client: "OpenAI",
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


def print_startup(args: argparse.Namespace) -> None:
    print("Personal AI ready. Type 'exit' or 'quit' to stop.")
    if not args.no_memory:
        print(f"Memory file: {Path(args.history_file).expanduser()}")


def run_once(args: argparse.Namespace, client: "OpenAI", history: list[dict[str, str]]) -> int:
    user_text = args.once.strip()
    if not user_text:
        print("The --once message cannot be empty.")
        return 1

    answer = chat_once(
        client=client,
        model=args.model,
        system_prompt=args.system_prompt,
        history=history,
        user_text=user_text,
    )
    print(answer)

    if not args.no_memory:
        history.extend(
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": answer},
            ]
        )
        save_history(Path(args.history_file), history)
    return 0


def run_repl(args: argparse.Namespace) -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY before running.")
        return 1

    client = make_client(api_key=api_key)
    history_path = Path(args.history_file).expanduser()
    history = [] if args.no_memory else load_history(history_path)

    if args.once is not None:
        try:
            return run_once(args, client, history)
        except Exception as exc:  # pragma: no cover
            print(f"Request failed: {exc}")
            return 1

    print_startup(args)

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
        if user_text.lower() == "/clear":
            history.clear()
            if not args.no_memory:
                save_history(history_path, history)
            print("ai> Memory cleared.")
            continue

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
            history.extend(
                [
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": answer},
                ]
            )
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
        default=str(DEFAULT_HISTORY_PATH),
        help="Where to persist conversation history",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable conversation memory",
    )
    parser.add_argument(
        "--once",
        help="Send one prompt and exit (non-interactive mode)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_repl(args)


if __name__ == "__main__":
    raise SystemExit(main())
