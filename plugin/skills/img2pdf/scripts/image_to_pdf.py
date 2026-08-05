#!/usr/bin/env python3
# /// script
# dependencies = [
#   "img2pdf>=0.6.0",
#   "pillow-heif>=0.18.0",
#   "Pillow>=10.0.0",
# ]
# ///
"""Convert image files (.jpg, .jpeg, .png, .heic) to PDF for JEC submission.

Reads LAWDOG_PDF_SIZE env var for size limit (default: 4194304 = 4MB).
HEIC files are handled natively via pillow-heif (no ImageMagick needed).

Usage:
    uv run img2pdf.py -i <input> -o <output>
"""
import argparse
import io
import os
import sys
from pathlib import Path

import img2pdf as _img2pdf
import pillow_heif
from PIL import Image

pillow_heif.register_heif_opener()

MAX = int(os.environ.get("LAWDOG_PDF_SIZE", 4 * 1024 * 1024))


def to_pdf(src: Path, dest: Path) -> None:
    """Convert image at src to PDF at dest. Handles all formats via Pillow."""
    ext = src.suffix.lower()
    if ext in (".jpg", ".jpeg", ".png"):
        # Lossless path: img2pdf preserves original quality
        with open(dest, "wb") as f:
            f.write(_img2pdf.convert(str(src)))
    else:
        # HEIC and other formats: open with Pillow (pillow_heif registered),
        # save as high-quality JPEG in memory, then pass to img2pdf
        img = Image.open(src)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=95)
        buf.seek(0)
        with open(dest, "wb") as f:
            f.write(_img2pdf.convert(buf.read()))


def reduce_quality(src: Path, dest: Path, max_bytes: int) -> int:
    """Reduce image quality until output PDF fits within max_bytes."""
    img = Image.open(src)
    quality = 70
    pdf_bytes = b""
    while quality >= 20:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=quality)
        buf.seek(0)
        pdf_bytes = _img2pdf.convert(buf.read())
        if len(pdf_bytes) <= max_bytes:
            dest.write_bytes(pdf_bytes)
            return len(pdf_bytes)
        quality -= 10
    # Floor reached — write whatever we have
    dest.write_bytes(pdf_bytes)
    return len(pdf_bytes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", required=True, help="Input image path")
    parser.add_argument("-o", "--output", required=True, help="Output PDF path")
    args = parser.parse_args()

    src = Path(args.input)
    dest = Path(args.output)

    if not src.exists():
        print(f"ERROR: Input not found: {src}", file=sys.stderr)
        sys.exit(1)

    print(f"Converting: {src} → {dest}", file=sys.stderr)
    to_pdf(src, dest)

    size = dest.stat().st_size
    if size > MAX:
        print(f"  {size} bytes > {MAX} limit. Reducing quality...", file=sys.stderr)
        size = reduce_quality(src, dest, MAX)
        if size > MAX:
            print(f"WARNING: Cannot reduce below {MAX} bytes. Size: {size}", file=sys.stderr)

    print(f"Done: {dest} ({size} bytes)")


if __name__ == "__main__":
    main()
