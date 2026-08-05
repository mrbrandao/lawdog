"""Regression tests for img2pdf.py.

Tests verify real behavioral contracts:
- Images actually convert to valid PDFs
- Output respects LAWDOG_PDF_SIZE
- Missing input fails cleanly

The test fixture creates a PNG using raw bytes (no Pillow import in test process)
so these tests run in the standard pytest environment without extra deps.
"""
import os
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "image_to_pdf.py"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", str(SCRIPT)] + args,
        capture_output=True, text=True,
    )


def is_pdf(path: Path) -> bool:
    return path.read_bytes()[:4] == b"%PDF"


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Build a PNG chunk with CRC."""
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def make_blue_png(path: Path) -> None:
    """Write a minimal 10x10 blue PNG using stdlib only."""
    width, height = 10, 10
    raw_rows = b""
    for _ in range(height):
        # Filter byte 0 (None) + RGB pixels
        raw_rows += b"\x00" + b"\x00\x00\xff" * width  # blue
    compressed = zlib.compress(raw_rows)

    png = (
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


@pytest.fixture
def blue_png(tmp_path):
    """Create a tiny solid-blue PNG using stdlib only."""
    p = tmp_path / "blue.png"
    make_blue_png(p)
    return p


def test_png_converts_to_valid_pdf(blue_png, tmp_path):
    out = tmp_path / "out.pdf"
    r = run(["-i", str(blue_png), "-o", str(out)])
    assert out.exists(), f"No output created. stderr: {r.stderr}"
    assert is_pdf(out), "Output is not a valid PDF"


def test_output_respects_lawdog_pdf_size(blue_png, tmp_path):
    out = tmp_path / "out.pdf"
    run(["-i", str(blue_png), "-o", str(out)])
    limit = int(os.environ.get("LAWDOG_PDF_SIZE", 4 * 1024 * 1024))
    assert out.stat().st_size < limit


def test_missing_input_exits_nonzero(tmp_path):
    r = run(["-i", str(tmp_path / "nope.png"), "-o", str(tmp_path / "out.pdf")])
    assert r.returncode != 0
    assert "error" in r.stderr.lower() or "not found" in r.stderr.lower()
