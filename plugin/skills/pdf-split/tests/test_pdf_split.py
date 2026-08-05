"""Regression tests for pdf_split.py — verifies actual split behavior."""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "pdf_split.py"
TEMPLATE = Path(__file__).parent.parent.parent.parent / "templates" / "base-legal.latex"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", str(SCRIPT)] + args, capture_output=True, text=True)


def is_pdf(path: Path) -> bool:
    return path.exists() and path.read_bytes()[:4] == b"%PDF"


@pytest.fixture
def two_page_pdf(tmp_path) -> Path:
    """Create a real 2-page PDF via pandoc + base-legal.latex template."""
    md = tmp_path / "src.md"
    md.write_text(
        "---\ntitle: Teste\n---\n\n# Página 1\n\nConteúdo.\n\n"
        "\\newpage\n\n# Página 2\n\nConteúdo.\n"
    )
    out = tmp_path / "src.pdf"
    subprocess.run(
        [
            "pandoc", str(md),
            "--pdf-engine=pdflatex",
            f"--template={TEMPLATE.resolve()}",
            "-o", str(out),
        ],
        check=True, capture_output=True,
    )
    return out


def test_no_split_when_under_limit(two_page_pdf, tmp_path):
    r = run(["-i", str(two_page_pdf), "-o", str(tmp_path / "part"), "-m", "10000000"])
    assert "no split needed" in r.stdout, f"Expected 'no split needed', got: {r.stdout}"
    assert not list(tmp_path.glob("part-*.pdf")), "Unnecessary split occurred"


def test_split_produces_valid_pdfs(two_page_pdf, tmp_path):
    # Force split with tiny limit (1 byte forces per-page split)
    run(["-i", str(two_page_pdf), "-o", str(tmp_path / "split"), "-m", "100"])
    parts = sorted(tmp_path.glob("split-*.pdf"))
    assert len(parts) >= 1, "No parts created"
    for part in parts:
        assert is_pdf(part), f"{part} is not a valid PDF"


def test_missing_input_exits_nonzero(tmp_path):
    r = run(["-i", str(tmp_path / "nope.pdf"), "-o", str(tmp_path / "out")])
    assert r.returncode != 0
