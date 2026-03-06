# Personal AI (CLI)

A simple personal AI chat program you can run in your terminal.

## Setup

1. Install dependencies:

   ```bash
   pip install openai
   ```

2. Set your API key:

   ```bash
   export OPENAI_API_KEY="your_key_here"
   ```

3. Run:

   ```bash
   python personal_ai.py
   ```

## Useful options

- `--model gpt-4.1-mini` (default)
- `--system-prompt "..."` to customize behavior
- `--history-file /path/to/history.json` to change memory location
- `--no-memory` to disable saving chat history
