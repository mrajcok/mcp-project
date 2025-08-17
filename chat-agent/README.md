# ABOUT-ME: Developer guide for the chat-agent workspace.
# ABOUT-ME: Explains environment setup and how to run tests locally.

# Chat Agent - Developer Guide

## Setup a local virtual environment

Create and use the local venv inside `chat-agent/`:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running tests

From the `chat-agent/` directory:

```bash
# Using the active venv
pytest -q

# Or invoke pytest via the venv python explicitly
./venv/bin/python -m pytest -q
```

### Integration tests (real LLM)

These tests call the real Pydantic AI + OpenAI model and are opt-in.

Requirements:
- Environment: `OPENAI_API_KEY` set. Optional: `OPENAI_MODEL` and `SYSTEM_PROMPT`.
- Network access; may incur costs on your OpenAI account.

Run only integration tests:
```bash
./venv/bin/python -m pytest -q -m integration
```

Run unit tests only (default for CI/local):
```bash
./venv/bin/python -m pytest -q -m "not integration"
```

Notes:
- The `integration` marker is registered in `pytest.ini`.
- If `OPENAI_API_KEY` is missing, integration tests are skipped.

### VS Code tasks

This repo defines tasks for convenience. They may rely on `python` on PATH. If your PATH does not have Python 3.12, prefer the local venv above. You can update tasks to call `./venv/bin/python` if needed.

## Notes

- Keep changes small and test-driven.
- Use Pydantic models and async patterns per project guidelines.
- Logs should be informative; do not suppress actionable errors.
