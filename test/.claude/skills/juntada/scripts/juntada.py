#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""File operations helper for /lawdog:juntada.

Atomic ops: list pending evidence, tag processed files, resolve name
conflicts, create petition directory structure.

Usage:
    uv run juntada.py list-pending <dir>
    uv run juntada.py tag <file>
    uv run juntada.py resolve-conflict <path>
    uv run juntada.py mkdirs <petition-dir>
"""
import sys
from pathlib import Path


def list_pending(dir_path: str) -> None:
    d = Path(dir_path)
    if not d.is_dir():
        print(f"ERROR: Not a directory: {dir_path}", file=sys.stderr)
        sys.exit(1)
    for f in sorted(d.iterdir()):
        if f.is_file() and not f.name.endswith(".converted"):
            print(f)


def tag(file_path: str) -> None:
    f = Path(file_path)
    if not f.is_file():
        print(f"ERROR: Not a file: {file_path}", file=sys.stderr)
        sys.exit(1)
    dest = Path(str(f) + ".converted")
    f.rename(dest)
    print(f"Tagged: {dest}")


def resolve_conflict(dest_path: str) -> None:
    dest = Path(dest_path)
    if not dest.exists():
        print(dest)
        return
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    n = 1
    while True:
        candidate = parent / f"{stem}-{n}{suffix}"
        if not candidate.exists():
            print(candidate)
            return
        n += 1


def mkdirs(petition_dir: str) -> None:
    base = Path(petition_dir)
    for sub in ("docs", "anexos", "juntada"):
        (base / sub).mkdir(parents=True, exist_ok=True)
    print(f"Created: docs/ anexos/ juntada/ in {base}")


COMMANDS = {
    "list-pending": (list_pending, "<dir>"),
    "tag": (tag, "<file>"),
    "resolve-conflict": (resolve_conflict, "<path>"),
    "mkdirs": (mkdirs, "<petition-dir>"),
}


def usage() -> None:
    print("Usage: juntada.py <subcommand> [arg]")
    for cmd, (_, arg) in COMMANDS.items():
        print(f"  {cmd} {arg}")
    sys.exit(0 if "--help" in sys.argv or "-h" in sys.argv else 1)


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        usage()
    cmd = args[0]
    if cmd not in COMMANDS:
        print(f"ERROR: Unknown subcommand: {cmd}", file=sys.stderr)
        usage()
    if len(args) < 2:
        print(f"ERROR: {cmd} requires {COMMANDS[cmd][1]}", file=sys.stderr)
        sys.exit(1)
    COMMANDS[cmd][0](args[1])


if __name__ == "__main__":
    main()
