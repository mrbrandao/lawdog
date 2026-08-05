"""Regression tests for juntada.py file operations.

Tests verify behavioral contracts that would cause real regressions:
- list_pending correctly filters .converted files
- tag renames file and removes original
- resolve_conflict never overwrites existing files
- mkdirs creates all three required directories
"""
import contextlib
import importlib.util
import io
from pathlib import Path

import pytest

# Import functions directly for unit testing — no subprocess overhead
_spec = importlib.util.spec_from_file_location(
    "juntada",
    Path(__file__).parent.parent / "scripts" / "juntada.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

list_pending_fn = _mod.list_pending
tag_fn = _mod.tag
resolve_conflict_fn = _mod.resolve_conflict
mkdirs_fn = _mod.mkdirs


def capture_stdout(fn, *args):
    """Capture printed output from a function."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args)
    return buf.getvalue().strip()


def test_list_pending_excludes_converted(tmp_path):
    (tmp_path / "foto.jpg").touch()
    (tmp_path / "doc.pdf").touch()
    (tmp_path / "done.pdf.converted").touch()
    out = capture_stdout(list_pending_fn, str(tmp_path))
    assert "foto.jpg" in out
    assert "doc.pdf" in out
    assert "done.pdf.converted" not in out


def test_list_pending_empty_dir(tmp_path):
    out = capture_stdout(list_pending_fn, str(tmp_path))
    assert out == ""


def test_tag_renames_to_converted(tmp_path):
    f = tmp_path / "evidence.pdf"
    f.touch()
    tag_fn(str(f))
    assert not f.exists(), "Original should be removed after tag"
    assert (tmp_path / "evidence.pdf.converted").exists()


def test_resolve_conflict_returns_original_when_free(tmp_path):
    dest = tmp_path / "file.pdf"
    result = capture_stdout(resolve_conflict_fn, str(dest))
    assert Path(result) == dest


def test_resolve_conflict_increments_suffix(tmp_path):
    (tmp_path / "file.pdf").touch()
    result = capture_stdout(resolve_conflict_fn, str(tmp_path / "file.pdf"))
    assert result.endswith("-1.pdf")


def test_resolve_conflict_increments_past_existing(tmp_path):
    (tmp_path / "file.pdf").touch()
    (tmp_path / "file-1.pdf").touch()
    result = capture_stdout(resolve_conflict_fn, str(tmp_path / "file.pdf"))
    assert result.endswith("-2.pdf")


def test_mkdirs_creates_required_dirs(tmp_path):
    petition = tmp_path / "peticao-inicial"
    mkdirs_fn(str(petition))
    assert (petition / "docs").is_dir()
    assert (petition / "anexos").is_dir()
    assert (petition / "juntada").is_dir()


def test_mkdirs_is_idempotent(tmp_path):
    petition = tmp_path / "peticao-inicial"
    mkdirs_fn(str(petition))
    mkdirs_fn(str(petition))  # Second call must not fail
    assert (petition / "docs").is_dir()
