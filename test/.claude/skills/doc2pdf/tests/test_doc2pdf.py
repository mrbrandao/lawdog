"""Regression tests for doc2pdf.py — verifies real PDF output, not text patterns."""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "doc2pdf.py"
TEMPLATE = Path(__file__).parent.parent.parent.parent / "templates" / "base-legal.latex"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", str(SCRIPT)] + args, capture_output=True, text=True)


def is_pdf(path: Path) -> bool:
    return path.exists() and path.read_bytes()[:4] == b"%PDF"


@pytest.fixture
def simple_md(tmp_path) -> Path:
    p = tmp_path / "test.md"
    p.write_text(
        "---\ntitle: Teste\n---\n\n## Dos Fatos\n\nFato.\n\n## Dos Pedidos\n\n1. Pedido.\n"
    )
    return p


def test_markdown_produces_valid_pdf(simple_md, tmp_path):
    out = tmp_path / "out.pdf"
    r = run(["-i", str(simple_md), "-o", str(out), "-t", str(TEMPLATE)])
    assert is_pdf(out), f"No valid PDF produced. stderr: {r.stderr}"


def test_unsupported_format_exits_nonzero(tmp_path):
    src = tmp_path / "test.heic"
    src.touch()
    r = run(["-i", str(src), "-o", str(tmp_path / "out.pdf")])
    assert r.returncode != 0


def test_missing_input_exits_nonzero(tmp_path):
    r = run(["-i", str(tmp_path / "nope.md"), "-o", str(tmp_path / "out.pdf")])
    assert r.returncode != 0
    assert "error" in r.stderr.lower()
