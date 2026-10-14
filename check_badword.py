#!/usr/bin/env python3
"""Compatibility entry point for the offline canonical-policy CLI."""
from pathlib import Path
import subprocess
import sys


def main(argv: list[str]) -> int:
    try:
        return subprocess.run(
            ["node", str(Path(__file__).with_suffix(".cjs")), *argv], check=False
        ).returncode
    except OSError as exc:
        print(f"Cannot start Node.js policy checker: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
