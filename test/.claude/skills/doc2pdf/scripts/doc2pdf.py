#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Convert text documents (.md, .txt, .doc, .docx) to PDF.

.md/.txt: pandoc + pdflatex + base-legal.latex template.
.doc/.docx: LibreOffice headless.

Usage:
    uv run doc2pdf.py -i <input> -o <output.pdf> [-t <template.latex>]
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def default_template() -> Path:
    return SCRIPT_DIR / ".." / ".." / "templates" / "base-legal.latex"


def convert_md_txt(src: Path, dest: Path, template: Path | None) -> None:
    tmpl = template or default_template()
    cmd = ["pandoc", str(src), "--pdf-engine=pdflatex", "-o", str(dest)]
    if tmpl.exists():
        cmd += [f"--template={tmpl}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"pandoc failed (exit {result.returncode})")


def convert_doc_docx(src: Path, dest: Path) -> None:
    if not shutil.which("libreoffice"):
        raise RuntimeError("libreoffice not found in PATH")
    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf",
         str(src), "--outdir", str(dest.parent)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"libreoffice failed: {result.stderr}")
    lo_out = dest.parent / (src.stem + ".pdf")
    if lo_out != dest and lo_out.exists():
        lo_out.rename(dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-t", "--template", default=None)
    args = parser.parse_args()

    src = Path(args.input)
    dest = Path(args.output)
    tmpl = Path(args.template) if args.template else None

    if not src.exists():
        print(f"ERROR: Input not found: {src}", file=sys.stderr)
        sys.exit(1)

    ext = src.suffix.lower().lstrip(".")
    print(f"Converting: {src} → {dest}", file=sys.stderr)

    try:
        if ext in ("md", "txt"):
            convert_md_txt(src, dest, tmpl)
        elif ext in ("doc", "docx"):
            convert_doc_docx(src, dest)
        else:
            print(f"ERROR: Unsupported format: .{ext}", file=sys.stderr)
            sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not dest.exists():
        print("ERROR: Conversion failed — no output created", file=sys.stderr)
        sys.exit(1)

    size = dest.stat().st_size
    print(f"Done: {dest} ({size} bytes)")


if __name__ == "__main__":
    main()
