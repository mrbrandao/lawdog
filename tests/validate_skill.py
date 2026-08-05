#!/usr/bin/env python3
"""Validate SKILL.md files against agentskills.io required structure.

Usage:
    python3 tests/validate_skill.py [path/to/SKILL.md ...]
    python3 tests/validate_skill.py --all          # validates all SKILL.md in plugin/
"""
import sys
import re
from pathlib import Path

REQUIRED_FRONTMATTER_FIELDS = ['name', 'description', 'allowed-tools', 'metadata']
REQUIRED_METADATA_FIELDS = ['author', 'version']
REQUIRED_SECTIONS = ['## Trigger', '## Fluxo']

PASS = 0
FAIL = 1


def extract_frontmatter(content: str) -> str | None:
    """Return the raw YAML frontmatter block, or None if absent."""
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    return match.group(1) if match else None


def check_frontmatter_fields(frontmatter: str) -> list[str]:
    """Return list of error messages for missing frontmatter fields."""
    errors = []
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if not re.search(rf'^{re.escape(field)}:', frontmatter, re.MULTILINE):
            errors.append(f"Missing frontmatter field: '{field}'")
    for field in REQUIRED_METADATA_FIELDS:
        if not re.search(rf'^\s+{re.escape(field)}:', frontmatter, re.MULTILINE):
            errors.append(f"Missing metadata sub-field: '{field}'")
    return errors


def check_required_sections(content: str) -> list[str]:
    """Return list of error messages for missing required markdown sections."""
    errors = []
    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing section: '{section}'")
    return errors


def validate_file(filepath: str) -> int:
    """Validate a single SKILL.md. Returns PASS (0) or FAIL (1)."""
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  FAIL [{filepath}]: file not found")
        return FAIL

    errors = []

    frontmatter = extract_frontmatter(content)
    if frontmatter is None:
        errors.append("No YAML frontmatter (--- ... ---) found")
    else:
        errors.extend(check_frontmatter_fields(frontmatter))

    errors.extend(check_required_sections(content))

    if errors:
        for err in errors:
            print(f"  FAIL [{filepath}]: {err}")
        return FAIL

    print(f"  PASS [{filepath}]")
    return PASS


def find_all_skill_files() -> list[str]:
    """Recursively find all SKILL.md files under plugin/skills."""
    root = Path(__file__).parent.parent / 'plugin' / 'skills'
    return [str(p) for p in root.rglob('SKILL.md')]


def run(paths: list[str]) -> int:
    """Validate all given paths. Returns exit code (0 = all pass)."""
    total = len(paths)
    failures = sum(validate_file(p) for p in paths)
    passed = total - failures
    print(f"\nResults: {passed}/{total} passed")
    return 0 if failures == 0 else 1


def main() -> None:
    args = sys.argv[1:]

    if '--all' in args:
        paths = find_all_skill_files()
        if not paths:
            print("No SKILL.md files found under plugin/skills/")
            sys.exit(1)
    elif args:
        paths = args
    else:
        print("Usage: validate_skill.py [path ...] | --all")
        sys.exit(1)

    print(f"Validating {len(paths)} SKILL.md file(s)...")
    sys.exit(run(paths))


if __name__ == '__main__':
    main()
