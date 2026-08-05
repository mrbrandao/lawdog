---
name: pdf-split
description: >-
  Splits document PDFs into parts not exceeding LAWDOG_PDF_SIZE bytes (default 4MB JEC limit).
  Uses PEP 723 inline deps via uv run — pypdf resolved automatically, no install needed.
  NOT for image PDFs — use img2pdf quality reduction for those.
  Activate on: /lawdog:pdf-split, PDF too large, PDF above 4MB, split PDF,
  PDF maior que 4MB, dividir PDF.
compatibility: >-
  Requires uv in PATH. pypdf resolved automatically via PEP 723 on first uv run.
  Reads LAWDOG_PDF_SIZE from environment (setup.sh exports it).
  Check: command -v uv
allowed-tools: Bash
metadata:
  author: mrbrandao
  version: "1.0"
---

## Trigger

Invoked by `/lawdog:doc2pdf` or `/lawdog:juntada` when a document PDF exceeds
`LAWDOG_PDF_SIZE`. Direct use: `/lawdog:pdf-split -i <input.pdf> -o <prefix>`

## Fluxo

1. Run:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/pdf_split.py" \
    -i "<input.pdf>" -o "<output-prefix>"
```

2. Script creates `<prefix>-1.pdf`, `<prefix>-2.pdf`, etc.
3. If output is "no split needed": file already within limit.
4. Return list of created parts with paths and sizes.

## Gotchas

- **Never use for image PDFs** (produced by img2pdf). Splitting a photo creates
  two meaningless half-images. For image PDFs >4MB, use img2pdf quality reduction.
- **uv is required** — pypdf is fetched automatically via PEP 723. Install uv:
  `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **LAWDOG_PDF_SIZE** must be exported. If unset, defaults to 4194304.
  Verify: `echo $LAWDOG_PDF_SIZE`
