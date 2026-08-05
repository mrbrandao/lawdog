#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pypdf>=4.3.0",
# ]
# ///
"""Split a document PDF into parts not exceeding a size limit.

Reads LAWDOG_PDF_SIZE env var for the byte limit (default: 4194304 = 4MB).

Usage:
    uv run pdf_split.py -i <input.pdf> -o <output-prefix> [-m <max-bytes>]

Outputs:
    <prefix>-1.pdf, <prefix>-2.pdf, ...
    If file is already within limit: prints "no split needed" and exits 0.
"""
import argparse
import os
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

MAX_DEFAULT = int(os.environ.get("LAWDOG_PDF_SIZE", 4 * 1024 * 1024))


def split_pdf(src: Path, prefix: str, max_bytes: int) -> list[Path]:
    """Split src PDF into parts of at most max_bytes each. Returns list of output paths."""
    reader = PdfReader(str(src))
    total_pages = len(reader.pages)

    parts: list[Path] = []
    part_num = 1
    start = 0

    while start < total_pages:
        # Binary search for largest chunk that fits in max_bytes
        lo, hi = 1, total_pages - start
        best = 1
        while lo <= hi:
            mid = (lo + hi) // 2
            writer = PdfWriter()
            for i in range(start, min(start + mid, total_pages)):
                writer.add_page(reader.pages[i])
            # Check size in memory
            import io
            buf = io.BytesIO()
            writer.write(buf)
            size = len(buf.getvalue())
            if size <= max_bytes:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1

        # Write the best chunk
        writer = PdfWriter()
        for i in range(start, start + best):
            writer.add_page(reader.pages[i])
        out_path = Path(f"{prefix}-{part_num}.pdf")
        with open(out_path, "wb") as f:
            writer.write(f)
        parts.append(out_path)
        print(f"  Part {part_num}: {out_path} ({out_path.stat().st_size} bytes, "
              f"pages {start + 1}-{start + best})", file=sys.stderr)
        part_num += 1
        start += best

    return parts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", required=True, help="Input PDF path")
    parser.add_argument("-o", "--output", required=True, help="Output prefix (e.g. doc-part)")
    parser.add_argument("-m", "--max-bytes", type=int, default=MAX_DEFAULT,
                        help=f"Max bytes per part (default: {MAX_DEFAULT})")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"ERROR: Input not found: {src}", file=sys.stderr)
        sys.exit(1)

    size = src.stat().st_size
    if size <= args.max_bytes:
        print(f"no split needed ({size} bytes <= {args.max_bytes} limit)")
        sys.exit(0)

    print(f"Splitting: {src} ({size} bytes) with limit {args.max_bytes}", file=sys.stderr)
    parts = split_pdf(src, args.output, args.max_bytes)
    for p in parts:
        print(f"Done: {p} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
