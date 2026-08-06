---
name: img2pdf
description: >-
  Converts image files (.jpg, .jpeg, .png, .heic) to PDF for JEC submission.
  Automatically reduces quality if output exceeds LAWDOG_PDF_SIZE (default 4MB).
  HEIC files are handled natively via pillow-heif (no ImageMagick needed).
  Activate on: /lawdog:img2pdf, convert image to PDF, image for juntada,
  foto para PDF, imagem para juntada.
compatibility: >-
  Requires uv in PATH (setup.sh installs Python deps).
  All Python dependencies (img2pdf, pillow-heif, Pillow) are resolved
  automatically via PEP 723 inline deps on first `uv run`.
  Check: command -v uv
allowed-tools: Bash
metadata:
  author: mrbrandao
  version: "1.0"
---

## Trigger

Invoked by `/lawdog:juntada` for images in `anexos/`.
Direct use: `/lawdog:img2pdf -i <input.jpg> -o <output.pdf>`

## Fluxo

1. Run the script:

```bash
LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/img2pdf}"
uv run "${LAWDOG_SKILL}/scripts/image_to_pdf.py" -i "<input>" -o "<output>"
```

2. If script prints `WARNING: Cannot reduce below`:
   inform user but continue — the file may still be accepted by the court.
3. Return the PDF path and size in bytes.

## Gotchas

- **Never use pdf-split on image PDFs.** An image cannot be logically split —
  split creates two half-images, neither useful as evidence. Use quality
  reduction (this script) for image PDFs that exceed LAWDOG_PDF_SIZE.
- **HEIC files** are handled natively via pillow-heif — no ImageMagick needed.
  The pillow_heif package is declared as an inline PEP 723 dependency and
  resolved automatically by `uv run`.
