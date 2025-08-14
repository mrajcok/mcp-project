# ABOUT-ME: Minimal entrypoint for the chat agent CLI.
# ABOUT-ME: Parses simple commands for running or testing connectivity.

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return 0
    cmd = argv[0]
    if cmd == "run":
        # Placeholder: start app here later
        return 0
    if cmd == "test-model":
        # Placeholder: later we'll ping the model provider
        print("ok")
        return 0
    if cmd == "--version":
        from . import __version__
        print(__version__)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
