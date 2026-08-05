"""Regression tests for importar_caso.py."""
import json
import subprocess
from pathlib import Path
import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "importar_caso.py"

def run(args):
    return subprocess.run(["uv", "run", str(SCRIPT)] + args, capture_output=True, text=True)

def write_manifest(path, slug, movements):
    path.write_text(json.dumps({"slug": slug, "movements": movements}))

@pytest.fixture
def cases_dir(tmp_path):
    d = tmp_path / "cases"
    d.mkdir()
    return d

@pytest.fixture
def manifest_path(tmp_path):
    return tmp_path / "manifest.json"

def test_decision_gets_docs_only(cases_dir, manifest_path, tmp_path):
    """Judge decisions: docs/ only, no juntada/."""
    pdf = tmp_path / "d.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    write_manifest(manifest_path, "case", [{"seq": "02", "type": "decisao-juiz", "files": [str(pdf)]}])
    run(["--slug", "case", "--cases-dir", str(cases_dir), "--manifest", str(manifest_path)])
    mov = cases_dir / "case" / "02-decisao-juiz"
    assert (mov / "docs").is_dir()
    assert not (mov / "juntada").exists()

def test_peticao_gets_all_dirs(cases_dir, manifest_path, tmp_path):
    """Petitions: docs/ + anexos/ + juntada/."""
    pdf = tmp_path / "p.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    write_manifest(manifest_path, "case", [{"seq": "01", "type": "peticao-inicial", "files": [str(pdf)]}])
    run(["--slug", "case", "--cases-dir", str(cases_dir), "--manifest", str(manifest_path)])
    mov = cases_dir / "case" / "01-peticao-inicial"
    assert (mov / "docs").is_dir()
    assert (mov / "anexos").is_dir()
    assert (mov / "juntada").is_dir()

def test_external_file_copied(cases_dir, manifest_path, tmp_path):
    """External files copied, original preserved."""
    pdf = tmp_path / "ext.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    write_manifest(manifest_path, "case", [{"seq": "01", "type": "peticao-inicial", "files": [str(pdf)]}])
    run(["--slug", "case", "--cases-dir", str(cases_dir), "--manifest", str(manifest_path)])
    assert pdf.exists()
    assert (cases_dir / "case" / "01-peticao-inicial" / "docs" / "ext.pdf").exists()

def test_internal_file_moved(cases_dir, manifest_path):
    """Internal files moved, no duplicates."""
    src = cases_dir / "src.pdf"
    src.write_bytes(b"%PDF-1.4")
    write_manifest(manifest_path, "case", [{"seq": "01", "type": "peticao-inicial", "files": [str(src)]}])
    run(["--slug", "case", "--cases-dir", str(cases_dir), "--manifest", str(manifest_path)])
    assert not src.exists()
    assert (cases_dir / "case" / "01-peticao-inicial" / "docs" / "src.pdf").exists()

def test_caso_md_generated(cases_dir, manifest_path, tmp_path):
    pdf = tmp_path / "p.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    write_manifest(manifest_path, "case", [{"seq": "01", "type": "peticao-inicial", "files": [str(pdf)]}])
    run(["--slug", "case", "--cases-dir", str(cases_dir), "--manifest", str(manifest_path)])
    content = (cases_dir / "case" / "caso.md").read_text()
    assert "# Caso: case" in content
    assert "Estado atual" in content
    assert "Movimentações" in content

def test_caso_md_not_overwritten(cases_dir, manifest_path, tmp_path):
    pdf = tmp_path / "p.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    write_manifest(manifest_path, "case", [{"seq": "01", "type": "peticao-inicial", "files": [str(pdf)]}])
    run(["--slug", "case", "--cases-dir", str(cases_dir), "--manifest", str(manifest_path)])
    md = cases_dir / "case" / "caso.md"
    md.write_text("preserved")
    pdf2 = tmp_path / "d.pdf"
    pdf2.write_bytes(b"%PDF-1.4")
    write_manifest(manifest_path, "case", [{"seq": "02", "type": "decisao-juiz", "files": [str(pdf2)]}])
    run(["--slug", "case", "--cases-dir", str(cases_dir), "--manifest", str(manifest_path)])
    assert md.read_text() == "preserved"

def test_conflict_resolved_kebab(cases_dir, manifest_path, tmp_path):
    """Duplicate names -> file-1.pdf, no spaces."""
    a = tmp_path / "doc.pdf"; a.write_bytes(b"a")
    sub = tmp_path / "s"; sub.mkdir()
    b = sub / "doc.pdf"; b.write_bytes(b"b")
    write_manifest(manifest_path, "case", [{"seq": "01", "type": "peticao-inicial", "files": [str(a), str(b)]}])
    run(["--slug", "case", "--cases-dir", str(cases_dir), "--manifest", str(manifest_path)])
    docs = cases_dir / "case" / "01-peticao-inicial" / "docs"
    assert (docs / "doc.pdf").exists()
    assert (docs / "doc-1.pdf").exists()
    assert not (docs / "doc (1).pdf").exists()

def test_missing_manifest_exits_nonzero(cases_dir):
    r = run(["--slug", "x", "--cases-dir", str(cases_dir), "--manifest", "/tmp/nope_lawdog.json"])
    assert r.returncode != 0
