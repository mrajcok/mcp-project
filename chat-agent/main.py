# ABOUT-ME: Top-level entrypoint to run the chat-agent from the repository root task.
# ABOUT-ME: Delegates to the package CLI in src.main.

from src.main import main


if __name__ == "__main__":
    raise SystemExit(main())
