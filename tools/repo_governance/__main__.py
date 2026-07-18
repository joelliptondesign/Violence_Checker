"""Command line entrypoint for local repository governance tooling."""

from .governance import main

if __name__ == "__main__":
    raise SystemExit(main())
