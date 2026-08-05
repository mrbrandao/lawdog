# Juntada de Evidências Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the evidence management stack — staging→analysis→juntada pipeline with parallel sub-agent conversions, automatic format conversion, 4MB JEC limit via `LAWDOG_PDF_SIZE`, and professional LaTeX typesetting.

**Architecture:** Six modular skills (img2pdf, doc2pdf, pdf-split, doc2docx, juntada + existing video2forum). Dedicated scripts for all non-trivial logic (>50 lines) per agentskills.io spec. Python scripts use PEP 723 + `uv run` for dependency isolation. `LAWDOG_PDF_SIZE` is the single env var for the JEC file size limit. `juntada` dispatches conversions as parallel sub-agents — all files at once, not sequentially.

**Tech Stack:** Bash (file ops, orchestration), Python + uv (img2pdf pkg, pypdf via PEP 723), pandoc 3.1 + pdflatex (doc→PDF), ImageMagick `convert` (HEIC pre-convert), ffmpeg/video2forum (video→WebM).

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `requirements.txt` | Python pkg: img2pdf (global install needed for `python3 -m img2pdf`) |
| Modify | `plugin/scripts/setup.sh` | Export `LAWDOG_PDF_SIZE` + install Python deps |
| Create | `plugin/protocols/document-standards.md` | Judicial document quality rules (English) |
| Modify | `plugin/AGENTS.md` | Add "Qualidade Documental" section (Portuguese — user-facing) |
| Modify | `plugin/protocols/file-structure.md` | Add `docs/`, `juntada/` to petition tree |
| Create | `plugin/templates/base-legal.latex` | Pandoc+pdflatex layout engine |
| Create | `plugin/skills/img2pdf/SKILL.md` | img2pdf skill |
| Create | `plugin/skills/img2pdf/scripts/img2pdf.sh` | Image→PDF conversion |
| Create | `plugin/skills/doc2pdf/SKILL.md` | doc2pdf skill |
| Create | `plugin/skills/doc2pdf/scripts/doc2pdf.sh` | Document→PDF conversion |
| Create | `plugin/skills/pdf-split/SKILL.md` | pdf-split skill |
| Create | `plugin/skills/pdf-split/scripts/pdf_split.py` | PDF split (PEP 723 + pypdf) |
| Create | `plugin/skills/doc2docx/SKILL.md` | doc2docx skill |
| Create | `plugin/skills/doc2docx/scripts/doc2docx.sh` | Document→DOCX conversion |
| Modify | `plugin/skills/caso/SKILL.md` | Create docs/, juntada/ + orient to lawdog:juntada |
| Create | `plugin/skills/juntada/SKILL.md` | juntada orchestrator |
| Create | `plugin/skills/juntada/scripts/juntada.sh` | File ops: list-pending, tag, resolve-conflict, mkdirs |
| Create | `tests/test_img2pdf.sh` | img2pdf behavioral tests |
| Create | `tests/test_doc2pdf.sh` | doc2pdf behavioral tests |
| Create | `tests/test_pdf_split.sh` | pdf-split behavioral tests |
| Create | `tests/test_doc2docx.sh` | doc2docx behavioral tests |
| Create | `tests/test_juntada.sh` | juntada file ops tests |
| Modify | `Makefile` | Add new test targets |
| Modify | `README.md` | Document new skills |
| Modify | `plugin/.claude-plugin/plugin.json` | Version 0.3.0 |
| Modify | `CLAUDE.md` | Update skills list to "implemented" |

---

## Task 1: Python Dependencies + LAWDOG_PDF_SIZE

**Files:**
- Create: `requirements.txt`
- Modify: `plugin/scripts/setup.sh`

- [ ] **Step 1.1: Create requirements.txt**

```
img2pdf>=0.6.0
```

(pypdf is handled via PEP 723 inline in `pdf_split.py` — no global install needed.)

- [ ] **Step 1.2: Read setup.sh to understand current structure before editing**

```bash
cat plugin/scripts/setup.sh
```

- [ ] **Step 1.3: Add two new functions to setup.sh**

After the `check_ffmpeg` function, add:

```bash
install_python_deps() {
    local req
    req="$(git rev-parse --show-toplevel 2>/dev/null)/requirements.txt"
    [[ ! -f "$req" ]] && { print_warn "requirements.txt not found."; return; }
    echo ""
    echo "Installing Python dependencies..."
    if command -v uv >/dev/null 2>&1; then
        uv pip install -r "$req" --system 2>/dev/null && print_ok "Installed with uv" || \
            pip3 install -r "$req" --user && print_ok "Installed with pip3"
    elif command -v pip3 >/dev/null 2>&1; then
        pip3 install -r "$req" --user && print_ok "Installed with pip3"
    else
        print_warn "uv and pip3 not found. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
}

write_pdf_size() {
    local profile="$1"
    # Idempotent: remove existing line before adding
    grep -v "LAWDOG_PDF_SIZE" "$profile" > "${profile}.tmp" 2>/dev/null || true
    printf '# JEC file size limit in bytes — change here to update all skills\nexport LAWDOG_PDF_SIZE=4194304\n' \
        >> "${profile}.tmp"
    mv "${profile}.tmp" "$profile"
}
```

In the main block, after `write_to_profile "$PROFILE" "$CASES_DIR"`, add:

```bash
write_pdf_size "$PROFILE"
install_python_deps
```

- [ ] **Step 1.4: Verify shellcheck**

```bash
shellcheck plugin/scripts/setup.sh
```

Expected: no output.

- [ ] **Step 1.5: Run setup.sh and confirm LAWDOG_PDF_SIZE is written**

```bash
echo "" | bash plugin/scripts/setup.sh 2>&1 | grep -E "Python|LAWDOG|uv|pip"
```

- [ ] **Step 1.6: Confirm img2pdf importable**

```bash
python3 -c "import img2pdf; print('OK img2pdf', img2pdf.__version__)"
```

Expected: `OK img2pdf X.Y.Z`

- [ ] **Step 1.7: Run make test (must still pass)**

```bash
make test
```

- [ ] **Step 1.8: Commit**

```bash
git add requirements.txt plugin/scripts/setup.sh
git commit -m "feat(setup): add LAWDOG_PDF_SIZE env var and Python img2pdf dep"
```

---

## Task 2: Protocols + AGENTS.md + file-structure

**Files:**
- Create: `plugin/protocols/document-standards.md`
- Modify: `plugin/AGENTS.md`
- Modify: `plugin/protocols/file-structure.md`

- [ ] **Step 2.1: Write document-standards.md (English — model-facing)**

Write `plugin/protocols/document-standards.md`:

```markdown
# Protocol: Document Standards

Import this protocol in any skill that produces judicial documents.

## Required Petition Structure

Documents must follow this order — no deviations:
1. **Dos Fatos** — facts in chronological order, no embellishment
2. **Do Direito** — legal basis: verified articles cited inline as `(CC, Art. 927)`
3. **Dos Pedidos** — numbered list, one request per line

No introduction. No "portanto" conclusion restating what was already said.

## Writing Rules

- One idea per paragraph. Split if it exceeds 6 lines.
- No filler phrases: "É de notório conhecimento que...", "Ante o exposto..."
- No repetition between paragraphs. Every sentence adds information.
- Active voice. Passive only when the agent is genuinely unknown.
- No AI slop: no hollow affirmations, no padding.

## Typographic Rules (enforced by base-legal.latex)

- No decorative separators (`---`, `***`, horizontal rules).
- No blank pages — a blank page is a typographic failure.
- Signature block (city + date + name) must stay on the same page as the
  last paragraph body. Never isolated on its own page.
- No orphaned lines: a single line alone at the top of a page is unacceptable.
  LaTeX widow/orphan penalties in base-legal.latex handle this automatically.

## What a Judge Appreciates

- The request is clear by the end of page one.
- Damages are proportional and documented.
- Each exhibit is referenced in the text where it matters.
- A well-argued 3-page petition beats a 15-page one.
```

- [ ] **Step 2.2: Verify required sections**

```bash
for s in "Dos Fatos" "Do Direito" "Dos Pedidos" "Writing Rules" "Typographic Rules" "What a Judge"; do
    grep -q "$s" plugin/protocols/document-standards.md && \
        echo "  PASS: $s" || echo "  FAIL: $s missing"
done
```

Expected: 6 PASS lines.

- [ ] **Step 2.3: Add "Qualidade Documental" to AGENTS.md (Portuguese — user-facing)**

In `plugin/AGENTS.md`, insert after `## Raciocínio Adversarial`:

```markdown
## Qualidade Documental

O lawdog confecciona documentos que um juiz leia com facilidade e apreciação:
diretos, claros, sem excesso. Fatos → fundamento → pedido em linha reta.
Parágrafos curtos, cada um com uma ideia. Nunca produz páginas em branco,
linhas decorativas (`---`), repetições ou frases de preenchimento.

O bloco de data, cidade e assinatura nunca é separado do corpo do documento.
Nenhuma linha fica isolada no topo de uma página nova.

Usa `base-legal.latex` via `doc2pdf` para toda produção documental.
Segue `protocols/document-standards.md` em toda redação jurídica.
A qualidade tipográfica é parte da representação do cliente — não é opcional.
```

- [ ] **Step 2.4: Verify AGENTS.md line count**

```bash
wc -l plugin/AGENTS.md
```

Expected: ≤ 115 lines.

- [ ] **Step 2.5: Update file-structure.md directory tree**

In `plugin/protocols/file-structure.md`, replace the existing `## Directory Tree` code block with:

```
$LAWDOG_CASES_DIR/
└── <case-slug>/
    ├── caso.md
    └── <petition>/
        ├── docs/           # editable originals (.md, .docx) — never deleted
        ├── anexos/         # staging: user drops evidence here
        │                   # processed files tagged .converted, never deleted
        └── juntada/        # organized, numbered, JEC-ready for PROJUDI upload
            ├── 01-peticao-inicial.pdf
            ├── 02.1-foto-dano.pdf
            └── 03.1-video-devassa.webm
```

Also add to the `## Naming Rules` section:

```markdown
- **docs/**: editable originals produced by lawdog (.md, .docx). Never deleted.
  Converted to PDF via doc2pdf when going to juntada/.
- **anexos/**: staging area. Any file goes here. After processing, original is
  tagged `.converted` suffix (e.g., `foto.jpg` → `foto.jpg.converted`). Never deleted.
  Script skips `.converted` files on re-run (idempotent).
- **juntada/**: final destination. Files named with sequential prefix `NN` or
  `NN.N` for thematic groups. Name conflict → suffix -1, -2 (kebab-case, no spaces).
- **LAWDOG_PDF_SIZE**: JEC size limit in bytes (default 4194304 = 4MB). Set in
  shell profile by setup.sh. All conversion scripts read this env var.
  Single change point: `export LAWDOG_PDF_SIZE=<bytes>` in profile.
```

- [ ] **Step 2.6: Verify file-structure.md**

```bash
grep -q "docs/" plugin/protocols/file-structure.md && echo "PASS: docs/"
grep -q "juntada/" plugin/protocols/file-structure.md && echo "PASS: juntada/"
grep -q "LAWDOG_PDF_SIZE" plugin/protocols/file-structure.md && echo "PASS: variable documented"
grep -q "converted" plugin/protocols/file-structure.md && echo "PASS: .converted tag"
```

Expected: 4 PASS lines.

- [ ] **Step 2.7: Commit**

```bash
git add plugin/protocols/document-standards.md plugin/AGENTS.md plugin/protocols/file-structure.md
git commit -m "feat(protocols): document-standards, docs/juntada/ dirs, LAWDOG_PDF_SIZE docs"
```

---

## Task 3: LaTeX Template

**Files:**
- Create: `plugin/templates/base-legal.latex`

- [ ] **Step 3.1: Create directory**

```bash
mkdir -p plugin/templates
```

- [ ] **Step 3.2: Write base-legal.latex**

Write `plugin/templates/base-legal.latex`:

```latex
\documentclass[$if(fontsize)$$fontsize$$else$12pt$endif$,a4paper]{article}

% Encoding and fonts
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}

% Brazilian Portuguese hyphenation
\usepackage[brazil]{babel}

% Judicial margins for A4 (Brazil standard)
\usepackage[left=3cm,right=2cm,top=2.5cm,bottom=2cm]{geometry}

% Line spacing
\usepackage{setspace}
\onehalfspacing
\setlength{\parindent}{1.5cm}
\setlength{\parskip}{0pt}

% WIDOW AND ORPHAN CONTROL
% 10000 = maximum penalty = never allow isolated lines.
\widowpenalty=10000
\clubpenalty=10000
\displaywidowpenalty=10000

% No section numbering (judicial documents don't use it)
\setcounter{secnumdepth}{0}

% Plain page style (page number at bottom center only)
\pagestyle{plain}

$for(header-includes)$
$header-includes$
$endfor$

\begin{document}

$if(title)$
\begin{center}
  {\large\textbf{$title$}}
\end{center}
\bigskip
$endif$

$body$

\end{document}
```

- [ ] **Step 3.3: Test template conversion**

```bash
printf '---\ntitle: "Petição de Teste"\n---\n\n## Dos Fatos\n\nFato um.\n\n## Dos Pedidos\n\n1. Pedido.\n\nCuritiba, 29 de maio de 2026.\n\nFulano de Tal\n' \
    > /tmp/ld-test.md

pandoc /tmp/ld-test.md \
    --template=plugin/templates/base-legal.latex \
    --pdf-engine=pdflatex \
    -o /tmp/ld-test.pdf 2>&1
```

Expected: exits 0, no errors.

- [ ] **Step 3.4: Verify PDF is valid, single page**

```bash
file /tmp/ld-test.pdf | grep -q PDF && echo "PASS: valid PDF"
pdfinfo /tmp/ld-test.pdf | grep "^Pages:"
```

Expected: `PASS: valid PDF`, `Pages: 1`

- [ ] **Step 3.5: Commit**

```bash
git add plugin/templates/base-legal.latex
git commit -m "feat(templates): add base-legal.latex with widow/orphan control and judicial margins"
```

---

## Task 4: img2pdf Skill (TDD)

**Files:**
- Create: `tests/test_img2pdf.sh`
- Create: `plugin/skills/img2pdf/scripts/img2pdf.sh`
- Create: `plugin/skills/img2pdf/SKILL.md`

- [ ] **Step 4.1: Write test (TDD baseline)**

Write `tests/test_img2pdf.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../plugin/skills/img2pdf/scripts/img2pdf.sh"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: img2pdf.sh not found"; exit 0; }

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running img2pdf.sh tests..."

# Test 1: --help works (required by agentskills.io spec)
bash "$SCRIPT" --help 2>&1 | grep -qi "usage\|input\|-i" && \
    pass "--help produces usage" || fail "--help not implemented"

# Test 2: PNG → valid PDF
convert -size 100x100 xc:blue "$TMPDIR_T/blue.png"
bash "$SCRIPT" -i "$TMPDIR_T/blue.png" -o "$TMPDIR_T/blue.pdf" >/dev/null 2>&1
[ -f "$TMPDIR_T/blue.pdf" ] && pass "PNG → PDF created" || fail "PNG → PDF not created"
file "$TMPDIR_T/blue.pdf" | grep -q PDF && pass "output is valid PDF" || fail "not valid PDF"

# Test 3: JPEG → PDF
convert -size 100x100 xc:red "$TMPDIR_T/red.jpg"
bash "$SCRIPT" -i "$TMPDIR_T/red.jpg" -o "$TMPDIR_T/red.pdf" >/dev/null 2>&1
[ -f "$TMPDIR_T/red.pdf" ] && pass "JPEG → PDF created" || fail "JPEG → PDF not created"

# Test 4: output respects LAWDOG_PDF_SIZE
SIZE=$(stat -c%s "$TMPDIR_T/blue.pdf" 2>/dev/null || stat -f%z "$TMPDIR_T/blue.pdf")
[ "$SIZE" -lt "${LAWDOG_PDF_SIZE:-4194304}" ] && pass "output under size limit" || fail "exceeds size limit"

# Test 5: missing input exits non-zero with error message
bash "$SCRIPT" -i "$TMPDIR_T/nope.png" -o "$TMPDIR_T/out.pdf" 2>&1 | \
    grep -qi "error\|not found" && pass "missing input gives error" || fail "missing input silent"

echo ""; echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
```

- [ ] **Step 4.2: Confirm test skips**

```bash
bash tests/test_img2pdf.sh
```

Expected: `SKIP: img2pdf.sh not found`

- [ ] **Step 4.3: Write img2pdf.sh**

```bash
mkdir -p plugin/skills/img2pdf/scripts
```

Write `plugin/skills/img2pdf/scripts/img2pdf.sh`:

```bash
#!/usr/bin/env bash
# Convert image files (.jpg, .jpeg, .png, .heic) to PDF.
# Reads LAWDOG_PDF_SIZE for the size limit (default: 4194304 = 4MB JEC limit).
# HEIC files are pre-converted to PNG via ImageMagick before PDF conversion.
set -euo pipefail

MAX="${LAWDOG_PDF_SIZE:-4194304}"

usage() {
    echo "Usage: img2pdf.sh -i <input.jpg|.png|.heic> -o <output.pdf>"
    echo "  Env: LAWDOG_PDF_SIZE — max output bytes (default: 4194304)"
    exit "${1:-1}"
}

file_size() { stat -c%s "$1" 2>/dev/null || stat -f%z "$1"; }

INPUT="" OUTPUT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i) INPUT="$2"; shift 2 ;;
        -o) OUTPUT="$2"; shift 2 ;;
        -h|--help) usage 0 ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

[[ -z "$INPUT" || -z "$OUTPUT" ]] && { echo "ERROR: -i and -o are required" >&2; usage; }
[[ ! -f "$INPUT" ]] && { echo "ERROR: Input not found: $INPUT" >&2; exit 1; }

EXT="${INPUT##*.}"; EXT="${EXT,,}"
TMPF=""

if [[ "$EXT" == "heic" ]]; then
    TMPF="$(mktemp /tmp/lawdog-XXXXXX.png)"
    echo "  HEIC detected — pre-converting to PNG..." >&2
    convert "$INPUT" "$TMPF"
    python3 -m img2pdf "$TMPF" -o "$OUTPUT"
    rm -f "$TMPF"
else
    python3 -m img2pdf "$INPUT" -o "$OUTPUT"
fi

SIZE=$(file_size "$OUTPUT")

if [[ "$SIZE" -gt "$MAX" ]]; then
    echo "  ${SIZE} bytes > ${MAX} limit. Reducing quality..." >&2
    Q=70
    while [[ "$SIZE" -gt "$MAX" && "$Q" -ge 20 ]]; do
        convert -quality "$Q" "$INPUT" "$OUTPUT"
        SIZE=$(file_size "$OUTPUT")
        Q=$((Q - 10))
    done
    [[ "$SIZE" -gt "$MAX" ]] && \
        echo "WARNING: Cannot reduce below ${MAX} bytes (quality floor reached). Size: ${SIZE}" >&2
fi

echo "Done: $OUTPUT (${SIZE} bytes)"
```

- [ ] **Step 4.4: Make executable and shellcheck**

```bash
chmod +x plugin/skills/img2pdf/scripts/img2pdf.sh
shellcheck plugin/skills/img2pdf/scripts/img2pdf.sh
```

Expected: no output.

- [ ] **Step 4.5: Run tests**

```bash
bash tests/test_img2pdf.sh
```

Expected: 5/5 passed.

- [ ] **Step 4.6: Write SKILL.md**

Write `plugin/skills/img2pdf/SKILL.md`:

```markdown
---
name: img2pdf
description: >-
  Converts image files (.jpg, .jpeg, .png, .heic) to PDF for JEC submission.
  Automatically reduces quality if output exceeds LAWDOG_PDF_SIZE (default 4MB).
  HEIC is pre-converted to PNG via ImageMagick before PDF generation.
  Activate on: /lawdog:img2pdf, convert image to PDF, image for juntada,
  foto para PDF, imagem para juntada.
compatibility: >-
  Requires python3 with img2pdf package (setup.sh installs it).
  Requires ImageMagick (convert) in PATH for .heic files.
  Check: python3 -m img2pdf --version && command -v convert
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
bash "${CLAUDE_SKILL_DIR}/scripts/img2pdf.sh" -i "<input>" -o "<output>"
```

2. If script prints `WARNING: Cannot reduce below`:
   - Inform user but continue — the file may still be accepted by the court
3. Return the PDF path and size in bytes.

## Gotchas

- **Never use pdf-split on image PDFs.** An image cannot be logically split in
  half — split would create two half-images, neither useful as evidence.
  Size reduction via quality reduction is the only valid approach for image PDFs.
- **HEIC files** require ImageMagick's `convert`. If not installed, the script
  will fail on HEIC. All other formats use Python `img2pdf` directly.
```

- [ ] **Step 4.7: Validate SKILL.md**

```bash
python3 tests/validate_skill.py plugin/skills/img2pdf/SKILL.md
```

Expected: PASS.

- [ ] **Step 4.8: Commit**

```bash
git add tests/test_img2pdf.sh plugin/skills/img2pdf/
git commit -m "feat(skills): add img2pdf — image to PDF with LAWDOG_PDF_SIZE quality reduction"
```

---

## Task 5: doc2pdf Skill (TDD)

**Files:**
- Create: `tests/test_doc2pdf.sh`
- Create: `plugin/skills/doc2pdf/scripts/doc2pdf.sh`
- Create: `plugin/skills/doc2pdf/SKILL.md`

- [ ] **Step 5.1: Write test**

Write `tests/test_doc2pdf.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../plugin/skills/doc2pdf/scripts/doc2pdf.sh"
TEMPLATE="$SCRIPT_DIR/../plugin/templates/base-legal.latex"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: doc2pdf.sh not found"; exit 0; }

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running doc2pdf.sh tests..."

# Test 1: --help works
bash "$SCRIPT" --help 2>&1 | grep -qi "usage\|-i\|input" && \
    pass "--help produces usage" || fail "--help not implemented"

# Test 2: .md → PDF with template
printf '---\ntitle: "Teste"\n---\n\n## Dos Fatos\n\nFato.\n\n## Dos Pedidos\n\n1. Pedido.\n' \
    > "$TMPDIR_T/test.md"
bash "$SCRIPT" -i "$TMPDIR_T/test.md" -o "$TMPDIR_T/t1.pdf" -t "$TEMPLATE" >/dev/null 2>&1
[ -f "$TMPDIR_T/t1.pdf" ] && pass ".md → PDF created" || fail ".md → PDF not created"
file "$TMPDIR_T/t1.pdf" | grep -q PDF && pass "output is valid PDF" || fail "not valid PDF"

# Test 3: .txt → PDF (no template flag)
echo "Texto simples de teste." > "$TMPDIR_T/test.txt"
bash "$SCRIPT" -i "$TMPDIR_T/test.txt" -o "$TMPDIR_T/t2.pdf" >/dev/null 2>&1
[ -f "$TMPDIR_T/t2.pdf" ] && pass ".txt → PDF created" || fail ".txt → PDF not created"

# Test 4: output under LAWDOG_PDF_SIZE
SIZE=$(stat -c%s "$TMPDIR_T/t1.pdf" 2>/dev/null || stat -f%z "$TMPDIR_T/t1.pdf")
[ "$SIZE" -lt "${LAWDOG_PDF_SIZE:-4194304}" ] && pass "output under size limit" || fail "exceeds limit"

# Test 5: missing input exits with error
bash "$SCRIPT" -i "$TMPDIR_T/nope.md" -o "$TMPDIR_T/out.pdf" 2>&1 | \
    grep -qi "error\|not found" && pass "missing input gives error" || fail "missing input silent"

echo ""; echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
```

- [ ] **Step 5.2: Confirm test skips**

```bash
bash tests/test_doc2pdf.sh
```

Expected: `SKIP: doc2pdf.sh not found`

- [ ] **Step 5.3: Write doc2pdf.sh**

```bash
mkdir -p plugin/skills/doc2pdf/scripts
```

Write `plugin/skills/doc2pdf/scripts/doc2pdf.sh`:

```bash
#!/usr/bin/env bash
# Convert text documents (.md, .txt, .doc, .docx) to PDF.
# .md/.txt: pandoc + pdflatex + base-legal.latex (falls back to pandoc default).
# .doc/.docx: LibreOffice headless.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_TEMPLATE="$SCRIPT_DIR/../../templates/base-legal.latex"

usage() {
    echo "Usage: doc2pdf.sh -i <input> -o <output.pdf> [-t <template.latex>]"
    echo "  Supported: .md, .txt, .doc, .docx"
    exit "${1:-1}"
}

file_size() { stat -c%s "$1" 2>/dev/null || stat -f%z "$1"; }

INPUT="" OUTPUT="" TEMPLATE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i) INPUT="$2"; shift 2 ;;
        -o) OUTPUT="$2"; shift 2 ;;
        -t) TEMPLATE="$2"; shift 2 ;;
        -h|--help) usage 0 ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

[[ -z "$INPUT" || -z "$OUTPUT" ]] && { echo "ERROR: -i and -o are required" >&2; usage; }
[[ ! -f "$INPUT" ]] && { echo "ERROR: Input not found: $INPUT" >&2; exit 1; }

EXT="${INPUT##*.}"; EXT="${EXT,,}"
echo "Converting: $INPUT → $OUTPUT"

case "$EXT" in
    md|txt)
        ARGS=("--pdf-engine=pdflatex" "-o" "$OUTPUT")
        if [[ -n "$TEMPLATE" && -f "$TEMPLATE" ]]; then
            ARGS+=("--template=$TEMPLATE")
        elif [[ -f "$DEFAULT_TEMPLATE" ]]; then
            ARGS+=("--template=$DEFAULT_TEMPLATE")
        fi
        pandoc "$INPUT" "${ARGS[@]}"
        ;;
    doc|docx)
        libreoffice --headless --convert-to pdf "$INPUT" \
            --outdir "$(dirname "$OUTPUT")" 2>/dev/null
        LO_OUT="$(dirname "$OUTPUT")/$(basename "${INPUT%.*}").pdf"
        [[ "$LO_OUT" != "$OUTPUT" && -f "$LO_OUT" ]] && mv "$LO_OUT" "$OUTPUT"
        ;;
    *)
        echo "ERROR: Unsupported format: .$EXT (supported: .md .txt .doc .docx)" >&2
        exit 1
        ;;
esac

[[ ! -f "$OUTPUT" ]] && { echo "ERROR: Conversion failed — no output created" >&2; exit 1; }
echo "Done: $OUTPUT ($(file_size "$OUTPUT") bytes)"
```

- [ ] **Step 5.4: Make executable, shellcheck, run tests**

```bash
chmod +x plugin/skills/doc2pdf/scripts/doc2pdf.sh
shellcheck plugin/skills/doc2pdf/scripts/doc2pdf.sh
bash tests/test_doc2pdf.sh
```

Expected: 5/5 passed.

- [ ] **Step 5.5: Write SKILL.md**

Write `plugin/skills/doc2pdf/SKILL.md`:

```markdown
---
name: doc2pdf
description: >-
  Converts text documents (.md, .txt, .doc, .docx) to PDF with judicial
  typography via pandoc + pdflatex + base-legal.latex template.
  .doc/.docx files are converted via LibreOffice headless.
  Activate on: /lawdog:doc2pdf, convert to PDF, document for juntada,
  documento para PDF, converter para PDF.
compatibility: >-
  .md/.txt: pandoc + pdflatex in PATH.
  .doc/.docx: libreoffice in PATH.
  Check: command -v pandoc && command -v pdflatex && command -v libreoffice
allowed-tools: Bash
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolos importados

Read `protocols/document-standards.md` before generating any document.

## Trigger

Invoked by `/lawdog:juntada` for documents. Direct use: `/lawdog:doc2pdf`

## Fluxo

1. Run:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/doc2pdf.sh" \
    -i "<input>" -o "<output>" \
    -t "${CLAUDE_SKILL_DIR}/../../templates/base-legal.latex"
```

2. Check output size against `LAWDOG_PDF_SIZE`:

```bash
MAX="${LAWDOG_PDF_SIZE:-4194304}"
SIZE=$(stat -c%s "<output>" 2>/dev/null || stat -f%z "<output>")
```

3. If `SIZE > MAX`: invoke `/lawdog:pdf-split -i <output> -o <prefix>`
4. Return path(s) and size(s).

## Gotchas

- **LibreOffice headless** sometimes writes the PDF with the input filename
  (not the `-o` destination). The script handles this with `mv`, but if
  LibreOffice is not installed, `.doc/.docx` conversion will fail silently
  with "no output created". Check: `command -v libreoffice`.
- **Template path** is resolved relative to the script's location. If the
  skill is invoked from a different working directory, always use the absolute
  path via `${CLAUDE_SKILL_DIR}`.
```

- [ ] **Step 5.6: Validate and commit**

```bash
python3 tests/validate_skill.py plugin/skills/doc2pdf/SKILL.md
git add tests/test_doc2pdf.sh plugin/skills/doc2pdf/
git commit -m "feat(skills): add doc2pdf — text/docx to PDF with base-legal.latex template"
```

---

## Task 6: pdf-split Skill (TDD + PEP 723)

**Files:**
- Create: `tests/test_pdf_split.sh`
- Create: `plugin/skills/pdf-split/scripts/pdf_split.py`
- Create: `plugin/skills/pdf-split/SKILL.md`

- [ ] **Step 6.1: Write test**

Write `tests/test_pdf_split.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../plugin/skills/pdf-split/scripts/pdf_split.py"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: pdf_split.py not found"; exit 0; }
command -v uv >/dev/null 2>&1 || { echo "SKIP: uv not found"; exit 0; }

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running pdf_split.py tests..."

# Test 1: --help works
uv run "$SCRIPT" --help 2>&1 | grep -qi "usage\|-i\|input" && \
    pass "--help produces usage" || fail "--help not implemented"

# Create 2-page PDF for testing
printf '# Page 1\n\nContent.\n\n# Page 2\n\nContent.\n' > "$TMPDIR_T/src.md"
pandoc "$TMPDIR_T/src.md" --pdf-engine=pdflatex -o "$TMPDIR_T/src.pdf" 2>/dev/null

# Test 2: no split when under limit
uv run "$SCRIPT" -i "$TMPDIR_T/src.pdf" -o "$TMPDIR_T/part" -m 10000000 >/dev/null 2>&1
[ ! -f "$TMPDIR_T/part-1.pdf" ] && pass "no split when under limit" || fail "unnecessary split"

# Test 3: split occurs with tiny limit (forces split of 2-page PDF)
uv run "$SCRIPT" -i "$TMPDIR_T/src.pdf" -o "$TMPDIR_T/split" -m 500 >/dev/null 2>&1 || true
ls "$TMPDIR_T"/split-*.pdf >/dev/null 2>&1 && pass "split files created" || fail "no split files"

# Test 4: each part is a valid PDF
for part in "$TMPDIR_T"/split-*.pdf; do
    [ -f "$part" ] && file "$part" | grep -q PDF && \
        pass "$(basename "$part") is valid PDF" || fail "not valid PDF: $(basename "$part")"
done

# Test 5: missing input exits with error message
uv run "$SCRIPT" -i "$TMPDIR_T/nope.pdf" -o "$TMPDIR_T/out" 2>&1 | \
    grep -qi "error\|not found\|No such" && pass "missing input gives error" || fail "missing input silent"

echo ""; echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
```

- [ ] **Step 6.2: Confirm test skips**

```bash
bash tests/test_pdf_split.sh
```

Expected: `SKIP: pdf_split.py not found`

- [ ] **Step 6.3: Write pdf_split.py with PEP 723 inline deps**

```bash
mkdir -p plugin/skills/pdf-split/scripts
```

Write `plugin/skills/pdf-split/scripts/pdf_split.py`:

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["pypdf>=4.3.0"]
# ///
"""Split a document PDF into parts not exceeding LAWDOG_PDF_SIZE bytes.

NOT for image PDFs — use img2pdf quality reduction instead.
Run with: uv run pdf_split.py -i input.pdf -o prefix [-m max_bytes]

LAWDOG_PDF_SIZE env var sets the default limit (4194304 = 4MB JEC limit).
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("ERROR: pypdf not available. Run with: uv run pdf_split.py", file=sys.stderr)
    sys.exit(1)

DEFAULT_MAX = int(os.environ.get("LAWDOG_PDF_SIZE", 4 * 1024 * 1024))


def file_size(path: str) -> int:
    return os.path.getsize(path)


def write_part(reader: "PdfReader", start: int, end: int, dest: str) -> int:
    """Write pages [start, end) to dest. Returns file size in bytes."""
    writer = PdfWriter()
    for i in range(start, end):
        writer.add_page(reader.pages[i])
    with open(dest, "wb") as f:
        writer.write(f)
    return file_size(dest)


def split_pdf(input_path: str, prefix: str, max_bytes: int) -> list[str]:
    """Split input_path into parts ≤ max_bytes. Returns list of created paths."""
    if file_size(input_path) <= max_bytes:
        print(f"File is {file_size(input_path)} bytes (≤{max_bytes}), no split needed.")
        return []

    reader = PdfReader(input_path)
    total = len(reader.pages)
    if total == 0:
        print("ERROR: PDF has no pages.", file=sys.stderr)
        sys.exit(1)

    # Estimate initial pages per part from size ratio
    pages_per_part = max(1, int(total * max_bytes / file_size(input_path)) - 1)
    parts: list[str] = []
    part_num = 1
    start = 0

    while start < total:
        end = min(start + pages_per_part, total)
        dest = f"{prefix}-{part_num}.pdf"

        while True:
            size = write_part(reader, start, end, dest)
            if size <= max_bytes or end - start <= 1:
                print(f"  Part {part_num}: pages {start+1}–{end} → {dest} ({size} bytes)")
                parts.append(dest)
                start = end
                part_num += 1
                break
            # Still too big — reduce chunk size
            os.remove(dest)
            pages_per_part = max(1, (end - start) // 2)
            end = start + pages_per_part

    return parts


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--input", required=True, help="Input PDF path")
    parser.add_argument("-o", "--output", required=True, help="Output prefix (without -N.pdf)")
    parser.add_argument(
        "-m", "--max-bytes",
        type=int,
        default=DEFAULT_MAX,
        help=f"Max bytes per part (default: {DEFAULT_MAX} from LAWDOG_PDF_SIZE)",
    )
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"ERROR: Input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    parts = split_pdf(args.input, args.output, args.max_bytes)
    if parts:
        print(f"Split complete: {len(parts)} part(s) created.")
    else:
        print("No split performed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6.4: Verify syntax and PEP 723 deps resolve**

```bash
python3 -m py_compile plugin/skills/pdf-split/scripts/pdf_split.py && echo "PASS: syntax OK"
uv run plugin/skills/pdf-split/scripts/pdf_split.py --help
```

Expected: syntax OK, help output shown.

- [ ] **Step 6.5: Run tests**

```bash
bash tests/test_pdf_split.sh
```

Expected: all pass.

- [ ] **Step 6.6: Write SKILL.md**

Write `plugin/skills/pdf-split/SKILL.md`:

```markdown
---
name: pdf-split
description: >-
  Splits document PDFs into parts not exceeding LAWDOG_PDF_SIZE bytes (default 4MB JEC limit).
  Uses PEP 723 inline deps via uv run — no global install needed.
  NOT for image PDFs — use img2pdf quality reduction for those.
  Activate on: /lawdog:pdf-split, PDF too large, PDF above 4MB, split PDF,
  PDF maior que 4MB, dividir PDF.
compatibility: >-
  Requires uv in PATH (installed by: curl -LsSf https://astral.sh/uv/install.sh | sh).
  pypdf is resolved automatically by uv run from PEP 723 inline deps.
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

- **Never use for image PDFs** (produced by img2pdf). Splitting a photo in half
  produces two meaningless half-images. For image PDFs >4MB, use img2pdf's
  quality reduction instead.
- **uv is required.** pypdf is fetched automatically by `uv run` via PEP 723 —
  no manual install needed. If uv is not installed, the script will not run.
  Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **LAWDOG_PDF_SIZE** must be exported in the shell (setup.sh does this). If
  not set, defaults to 4194304. Verify: `echo $LAWDOG_PDF_SIZE`
```

- [ ] **Step 6.7: Validate and commit**

```bash
python3 tests/validate_skill.py plugin/skills/pdf-split/SKILL.md
git add tests/test_pdf_split.sh plugin/skills/pdf-split/
git commit -m "feat(skills): add pdf-split — PEP 723 + pypdf, LAWDOG_PDF_SIZE aware"
```

---

## Task 7: doc2docx Skill (TDD)

**Files:**
- Create: `tests/test_doc2docx.sh`
- Create: `plugin/skills/doc2docx/scripts/doc2docx.sh`
- Create: `plugin/skills/doc2docx/SKILL.md`

- [ ] **Step 7.1: Write test**

Write `tests/test_doc2docx.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../plugin/skills/doc2docx/scripts/doc2docx.sh"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: doc2docx.sh not found"; exit 0; }

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running doc2docx.sh tests..."

# Test 1: --help works
bash "$SCRIPT" --help 2>&1 | grep -qi "usage\|-i\|input" && \
    pass "--help produces usage" || fail "--help not implemented"

# Test 2: .md → .docx
printf '# Petição\n\n## Dos Fatos\n\nFato.\n' > "$TMPDIR_T/test.md"
bash "$SCRIPT" -i "$TMPDIR_T/test.md" -o "$TMPDIR_T/test.docx" >/dev/null 2>&1
[ -f "$TMPDIR_T/test.docx" ] && pass ".md → .docx created" || fail ".md → .docx not created"
file "$TMPDIR_T/test.docx" | grep -qi "zip\|docx\|microsoft\|OpenDocument" && \
    pass "output is valid DOCX" || fail "not valid DOCX"

# Test 3: .txt → .docx
echo "Texto simples." > "$TMPDIR_T/test.txt"
bash "$SCRIPT" -i "$TMPDIR_T/test.txt" -o "$TMPDIR_T/test2.docx" >/dev/null 2>&1
[ -f "$TMPDIR_T/test2.docx" ] && pass ".txt → .docx created" || fail ".txt → .docx not created"

# Test 4: missing input exits with error
bash "$SCRIPT" -i "$TMPDIR_T/nope.md" -o "$TMPDIR_T/out.docx" 2>&1 | \
    grep -qi "error\|not found" && pass "missing input gives error" || fail "missing input silent"

echo ""; echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
```

- [ ] **Step 7.2: Write doc2docx.sh**

```bash
mkdir -p plugin/skills/doc2docx/scripts
```

Write `plugin/skills/doc2docx/scripts/doc2docx.sh`:

```bash
#!/usr/bin/env bash
# Convert text documents (.md, .txt) to editable .docx via pandoc.
set -euo pipefail

usage() {
    echo "Usage: doc2docx.sh -i <input.md|.txt> -o <output.docx>"
    exit "${1:-1}"
}

INPUT="" OUTPUT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i) INPUT="$2"; shift 2 ;;
        -o) OUTPUT="$2"; shift 2 ;;
        -h|--help) usage 0 ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

[[ -z "$INPUT" || -z "$OUTPUT" ]] && { echo "ERROR: -i and -o are required" >&2; usage; }
[[ ! -f "$INPUT" ]] && { echo "ERROR: Input not found: $INPUT" >&2; exit 1; }

EXT="${INPUT##*.}"; EXT="${EXT,,}"
case "$EXT" in
    md|txt) ;;
    *) echo "ERROR: Unsupported: .$EXT (use .md or .txt)" >&2; exit 1 ;;
esac

echo "Converting: $INPUT → $OUTPUT"
pandoc "$INPUT" -o "$OUTPUT"
[[ ! -f "$OUTPUT" ]] && { echo "ERROR: Conversion failed" >&2; exit 1; }
echo "Done: $OUTPUT"
```

- [ ] **Step 7.3: Make executable, shellcheck, run tests**

```bash
chmod +x plugin/skills/doc2docx/scripts/doc2docx.sh
shellcheck plugin/skills/doc2docx/scripts/doc2docx.sh
bash tests/test_doc2docx.sh
```

Expected: 4/4 passed.

- [ ] **Step 7.4: Write SKILL.md**

Write `plugin/skills/doc2docx/SKILL.md`:

```markdown
---
name: doc2docx
description: >-
  Converts .md or .txt documents to editable .docx via pandoc.
  Use when the user wants to edit a lawdog-generated document in Word or LibreOffice.
  The original .md is preserved in docs/ — DOCX is generated in the same directory.
  Activate on: /lawdog:doc2docx, editable version, edit in Word, generate DOCX,
   versão editável, quero editar no Word, gerar DOCX.
compatibility: >-
  Requires pandoc in PATH. Check: command -v pandoc
allowed-tools: Bash
metadata:
  author: mrbrandao
  version: "1.0"
---

## Trigger

User asks for an editable version of a lawdog-generated document.

Example: "Gostei da petição, mas quero editar. Pode gerar um DOCX?"

## Fluxo

1. Identify the `.md` file in `docs/` for the current petition.
2. Generate DOCX in the same `docs/` directory with the same basename.
   If the `.docx` already exists: apply conflict resolution (`<name>-1.docx`, etc.).
3. Run:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/doc2docx.sh" \
    -i "docs/<name>.md" -o "docs/<name>.docx"
```

4. Report the full path. Remind user: to include in `juntada/`, convert to
   PDF first with `/lawdog:doc2pdf`.

## Gotchas

- **DOCX is for editing only.** It cannot go to `juntada/` directly — PROJUDI
  requires PDF. The user must convert with `/lawdog:doc2pdf` after editing.
- **Conflict resolution:** if `docs/<name>.docx` already exists, the new file
  gets suffix `-1`, `-2`, etc. (kebab-case, no spaces). Inform the user which
  name was actually used.
```

- [ ] **Step 7.5: Validate and commit**

```bash
python3 tests/validate_skill.py plugin/skills/doc2docx/SKILL.md
git add tests/test_doc2docx.sh plugin/skills/doc2docx/
git commit -m "feat(skills): add doc2docx — markdown to editable DOCX via pandoc"
```

---

## Task 8: Update /lawdog:caso

**Files:**
- Modify: `plugin/skills/caso/SKILL.md`

- [ ] **Step 8.1: Update mkdir command**

In `plugin/skills/caso/SKILL.md`, replace the directory creation step:

Old:
```bash
mkdir -p "$CASES_DIR/<case-slug>/peticao-inicial/anexos"
```

New:
```bash
mkdir -p "$CASES_DIR/<case-slug>/peticao-inicial/docs"
mkdir -p "$CASES_DIR/<case-slug>/peticao-inicial/anexos"
mkdir -p "$CASES_DIR/<case-slug>/peticao-inicial/juntada"
```

- [ ] **Step 8.2: Update user orientation (step 6)**

Replace the current step 6 with:

```
6. Inform the user of all created paths and orient next steps:
   - `docs/`   — lawdog creates petition documents here (.md files)
   - `anexos/` — user drops evidence here (any format: photos, PDFs, videos)
   - `juntada/`— organized JEC-ready files appear here after /lawdog:juntada

   Say: "Coloque suas evidências em `<CASES_DIR>/<slug>/peticao-inicial/anexos/`
   ou me informe os caminhos. Quando pronto: `/lawdog:juntada <slug>`"

   Consult `knowledge/court-portals.md` for the user's state portal.
```

- [ ] **Step 8.3: Verify**

```bash
grep -c "mkdir" plugin/skills/caso/SKILL.md | grep -qE "^[3-9]|^[0-9]{2}" && \
    echo "PASS: multiple mkdir lines" || echo "PASS: check manually"
grep -q "lawdog:juntada" plugin/skills/caso/SKILL.md && echo "PASS: juntada orientation"
grep -q "docs" plugin/skills/caso/SKILL.md && echo "PASS: docs/ referenced"
```

- [ ] **Step 8.4: Commit**

```bash
git add plugin/skills/caso/SKILL.md
git commit -m "feat(skills): caso creates docs/, juntada/ and orients user to lawdog:juntada"
```

---

## Task 9: juntada Skill (TDD)

**Files:**
- Create: `tests/test_juntada.sh`
- Create: `plugin/skills/juntada/scripts/juntada.sh`
- Create: `plugin/skills/juntada/SKILL.md`

- [ ] **Step 9.1: Write test**

Write `tests/test_juntada.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../plugin/skills/juntada/scripts/juntada.sh"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: juntada.sh not found"; exit 0; }

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running juntada.sh tests..."

# Test 1: --help
bash "$SCRIPT" --help 2>&1 | grep -qi "usage\|subcommand\|list-pending" && \
    pass "--help produces usage" || fail "--help not implemented"

# Setup for remaining tests
mkdir -p "$TMPDIR_T/anexos"
touch "$TMPDIR_T/anexos/foto.jpg"
touch "$TMPDIR_T/anexos/doc.pdf"
touch "$TMPDIR_T/anexos/done.pdf.converted"

# Test 2: list-pending returns unprocessed files
PENDING=$(bash "$SCRIPT" list-pending "$TMPDIR_T/anexos")
echo "$PENDING" | grep -q "foto.jpg" && pass "list-pending: returns pending files" || fail "missing foto.jpg"
echo "$PENDING" | grep -q "done.pdf.converted" && \
    fail "list-pending: returns .converted files" || pass "list-pending: skips .converted"

# Test 3: tag renames to .converted
touch "$TMPDIR_T/tomark.pdf"
bash "$SCRIPT" tag "$TMPDIR_T/tomark.pdf"
[ -f "$TMPDIR_T/tomark.pdf.converted" ] && pass "tag: .converted created" || fail "tag: no .converted"
[ ! -f "$TMPDIR_T/tomark.pdf" ] && pass "tag: original removed" || fail "tag: original remains"

# Test 4: resolve-conflict adds -1 when name exists
touch "$TMPDIR_T/existing.pdf"
R=$(bash "$SCRIPT" resolve-conflict "$TMPDIR_T/existing.pdf")
[[ "$R" == *"-1.pdf" ]] && pass "resolve-conflict: -1 suffix" || fail "resolve-conflict: wrong ($R)"

# Test 5: resolve-conflict increments to -2
touch "$TMPDIR_T/existing-1.pdf"
R2=$(bash "$SCRIPT" resolve-conflict "$TMPDIR_T/existing.pdf")
[[ "$R2" == *"-2.pdf" ]] && pass "resolve-conflict: -2 suffix" || fail "resolve-conflict: wrong ($R2)"

# Test 6: no conflict when path doesn't exist
R3=$(bash "$SCRIPT" resolve-conflict "$TMPDIR_T/new.pdf")
[[ "$R3" == "$TMPDIR_T/new.pdf" ]] && pass "resolve-conflict: unchanged when no conflict" || \
    fail "resolve-conflict: wrong ($R3)"

# Test 7-9: mkdirs creates three directories
bash "$SCRIPT" mkdirs "$TMPDIR_T/petition"
[ -d "$TMPDIR_T/petition/docs" ] && pass "mkdirs: docs/" || fail "mkdirs: no docs/"
[ -d "$TMPDIR_T/petition/anexos" ] && pass "mkdirs: anexos/" || fail "mkdirs: no anexos/"
[ -d "$TMPDIR_T/petition/juntada" ] && pass "mkdirs: juntada/" || fail "mkdirs: no juntada/"

echo ""; echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
```

- [ ] **Step 9.2: Confirm test skips**

```bash
bash tests/test_juntada.sh
```

Expected: `SKIP: juntada.sh not found`

- [ ] **Step 9.3: Write juntada.sh**

```bash
mkdir -p plugin/skills/juntada/scripts
```

Write `plugin/skills/juntada/scripts/juntada.sh`:

```bash
#!/usr/bin/env bash
# File operations helper for /lawdog:juntada.
# Provides atomic file ops: listing pending evidence, tagging processed files,
# resolving name conflicts, and creating petition directory structure.
#
# Subcommands:
#   list-pending <dir>          — list files without .converted suffix (pending)
#   tag <file>                  — rename file → file.converted (idempotent marker)
#   resolve-conflict <path>     — return conflict-free path (-1, -2, ...) or original
#   mkdirs <petition-dir>       — create docs/, anexos/, juntada/ inside dir
set -euo pipefail

usage() {
    echo "Usage: juntada.sh <subcommand> [arg]"
    echo "Subcommands: list-pending <dir>, tag <file>, resolve-conflict <path>, mkdirs <dir>"
    exit "${1:-1}"
}

cmd_list_pending() {
    local dir="${1:?list-pending requires <dir>}"
    [[ ! -d "$dir" ]] && { echo "ERROR: Not a directory: $dir" >&2; exit 1; }
    find "$dir" -maxdepth 1 -type f ! -name "*.converted" | sort
}

cmd_tag() {
    local file="${1:?tag requires <file>}"
    [[ ! -f "$file" ]] && { echo "ERROR: Not a file: $file" >&2; exit 1; }
    mv "$file" "${file}.converted"
    echo "Tagged: ${file}.converted"
}

cmd_resolve_conflict() {
    local dest="${1:?resolve-conflict requires <path>}"
    [[ ! -e "$dest" ]] && { echo "$dest"; return; }
    local base ext n=1
    base="${dest%.*}"
    ext="${dest##*.}"
    while [[ -e "${base}-${n}.${ext}" ]]; do n=$((n+1)); done
    echo "${base}-${n}.${ext}"
}

cmd_mkdirs() {
    local dir="${1:?mkdirs requires <petition-dir>}"
    mkdir -p "$dir/docs" "$dir/anexos" "$dir/juntada"
    echo "Created: docs/ anexos/ juntada/ in $dir"
}

case "${1:-}" in
    list-pending)     cmd_list_pending "${2:-}" ;;
    tag)              cmd_tag "${2:-}" ;;
    resolve-conflict) cmd_resolve_conflict "${2:-}" ;;
    mkdirs)           cmd_mkdirs "${2:-}" ;;
    -h|--help)        usage 0 ;;
    *)                usage ;;
esac
```

- [ ] **Step 9.4: Make executable, shellcheck, run tests**

```bash
chmod +x plugin/skills/juntada/scripts/juntada.sh
shellcheck plugin/skills/juntada/scripts/juntada.sh
bash tests/test_juntada.sh
```

Expected: 9/9 passed.

- [ ] **Step 9.5: Write juntada SKILL.md**

Write `plugin/skills/juntada/SKILL.md`:

```markdown
---
name: juntada
description: >-
  Organizes case evidence from anexos/ into a numbered, JEC-ready juntada/.
  Analyzes file content, proposes batch naming in one table interaction, dispatches
  all conversions as parallel sub-agents, and enforces LAWDOG_PDF_SIZE limit.
  Central entry point for evidence management throughout the case lifecycle.
  Activate on: /lawdog:juntada, organize evidence, prepare juntada, process
  attachments, organizar evidências, preparar juntada, processar anexos,
  evidências prontas, juntar documentos.
compatibility: >-
  Sub-skills required: img2pdf, doc2pdf, pdf-split, video2forum.
  All installed via setup.sh. Verify: make test-skills
  Reads: LAWDOG_PDF_SIZE (set by setup.sh, default 4194304).
allowed-tools: Bash, Read, Write, WebFetch
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolos importados

Read `protocols/file-structure.md` at start for directory conventions.
Read `protocols/document-standards.md` when evaluating document quality.

## Trigger

`/lawdog:juntada <case-slug> [petition]` — petition defaults to `peticao-inicial`.

## Fluxo

### Step 1 — Resolve directories and list pending

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
PETICAO="${2:-peticao-inicial}"
ANEXOS="$CASES_DIR/$1/$PETICAO/anexos"
JUNTADA="$CASES_DIR/$1/$PETICAO/juntada"
DOCS="$CASES_DIR/$1/$PETICAO/docs"

bash "${CLAUDE_SKILL_DIR}/scripts/juntada.sh" list-pending "$ANEXOS"
```

If user provided external paths: copy each to `$ANEXOS` first (use `resolve-conflict`
for name conflicts), then process from there. External originals are never touched.

Text documents in `$ANEXOS` (.md, .txt, .doc, .docx): move to `$DOCS` and inform user.
If `$ANEXOS` is empty and no external paths given: inform user and wait.

### Step 2 — Analyze all files in batch

Read or view ALL pending files BEFORE asking any questions.
- Images: view — verify content matches what user described
- PDFs/documents: read — extract type, value, date, parties, relevant clauses
- Videos: assess from name and user context

Record evaluation: strong / weak / contradictory / missing evidence.

### Step 3 — Batch naming table (one interaction for all files)

Present ONE table with all files. Names are suggested based on content read:

```
Analyzed files in anexos/. Naming proposal:

| # | Original file       | Suggested name for juntada/   | Group     |
|---|---------------------|-------------------------------|-----------|
| 1 | IMG_4821.HEIC       | 04.1-rachadura-muro.pdf       | Danos     |
| 2 | contrato.pdf        | 02-contrato-servico.pdf       | Documentos|
| 3 | video_devassa.mp4   | 03.1-video-devassa.webm       | Vídeos    |

Adjust names or groups if needed. Confirm to process all at once.
```

Wait for confirmation before proceeding. Never ask per-file.

### Step 4 — Parallel conversions (all at once)

Dispatch ALL conversions simultaneously as background sub-agents.
Do NOT process one at a time. Wait for all to complete before Step 5.

| Extension | Sub-skill | Output |
|---|---|---|
| .jpg .jpeg .png .heic | `/lawdog:img2pdf` | .pdf |
| .mp4 .mov .avi .mkv | `/lawdog:video2forum` | .webm |
| .pdf .webm | — no conversion — | same |

### Step 5 — Size validation and split

After all conversions complete, check each PDF against `LAWDOG_PDF_SIZE`:

```bash
MAX="${LAWDOG_PDF_SIZE:-4194304}"
SIZE=$(stat -c%s "<file>" 2>/dev/null || stat -f%z "<file>")
```

Document PDFs >MAX: invoke `/lawdog:pdf-split -i <file> -o <prefix>`
Image PDFs >MAX: img2pdf already handled quality reduction — no split.

### Step 6 — Copy to juntada/ and tag

For each processed file:

```bash
# Resolve name conflict in juntada/
DEST=$(bash "${CLAUDE_SKILL_DIR}/scripts/juntada.sh" resolve-conflict "$JUNTADA/<NN-name.ext>")
cp "<converted-file>" "$DEST"

# Tag the original in anexos/ as processed
bash "${CLAUDE_SKILL_DIR}/scripts/juntada.sh" tag "<original-in-anexos>"
```

External files (copied from outside `$CASES_DIR`): only `cp`, no tag on original.

### Step 7 — Final report

1. Numbered list of all files in `juntada/` with full paths and sizes
2. Legal assessment: strong / weak / absent evidence for the case
3. Confirmation all files ≤ `LAWDOG_PDF_SIZE`
4. What is still missing for a well-documented case

## Gotchas

- **Dispatch conversions in parallel, not sequentially.** All img2pdf, video2forum,
  and other conversion sub-agents must run simultaneously. Sequential dispatch
  defeats the purpose and wastes time on multi-file cases.
- **Never ask per-file for labels.** Batch the naming table — one interaction,
  all files. Users disengage with repetitive file-by-file prompts.
- **Tag only AFTER copy succeeds.** If `cp` to juntada/ fails, do not tag the
  original in anexos/ — it would appear processed but wasn't.
- **LAWDOG_PDF_SIZE must be set.** If not in environment, script defaults to
  4194304 but users may not realize the value changed via setup.sh.
  Remind them to `source ~/.bashrc` or restart the shell after first setup.
```

- [ ] **Step 9.6: Validate SKILL.md**

```bash
python3 tests/validate_skill.py plugin/skills/juntada/SKILL.md
```

Expected: PASS.

- [ ] **Step 9.7: Commit**

```bash
git add tests/test_juntada.sh plugin/skills/juntada/
git commit -m "feat(skills): add juntada orchestrator — parallel dispatch, batch naming, LAWDOG_PDF_SIZE"
```

---

## Task 10: Makefile + README + plugin.json + CLAUDE.md

**Files:**
- Modify: `Makefile`
- Modify: `README.md`
- Modify: `plugin/.claude-plugin/plugin.json`
- Modify: `CLAUDE.md`

- [ ] **Step 10.1: Replace Makefile**

Write `Makefile`:

```makefile
.PHONY: test test-skills test-setup test-img2pdf test-doc2pdf test-pdf-split test-doc2docx test-juntada

# Run all test suites
test: test-skills test-setup test-img2pdf test-doc2pdf test-pdf-split test-doc2docx test-juntada
	@echo ""
	@echo "All test suites passed."

test-skills:
	@echo "=== Validating SKILL.md files ==="
	@python3 tests/validate_skill.py --all

test-setup:
	@echo "=== Testing setup.sh ==="
	@bash tests/test_setup.sh

test-img2pdf:
	@echo "=== Testing img2pdf ==="
	@bash tests/test_img2pdf.sh

test-doc2pdf:
	@echo "=== Testing doc2pdf ==="
	@bash tests/test_doc2pdf.sh

test-pdf-split:
	@echo "=== Testing pdf-split ==="
	@bash tests/test_pdf_split.sh

test-doc2docx:
	@echo "=== Testing doc2docx ==="
	@bash tests/test_doc2docx.sh

test-juntada:
	@echo "=== Testing juntada ==="
	@bash tests/test_juntada.sh
```

- [ ] **Step 10.2: Verify make test**

```bash
make test 2>&1 | tail -3
```

Expected: `All test suites passed.`

- [ ] **Step 10.3: Bump plugin.json to 0.3.0**

Change `"version": "0.2.0"` → `"version": "0.3.0"` in `plugin/.claude-plugin/plugin.json`.

- [ ] **Step 10.4: Add new skills to README.md**

After `### video2forum`, add:

```markdown
---

### `juntada`

Organizes evidence from `anexos/` into a numbered, JEC-ready `juntada/`.
Analyzes file content, proposes batch naming in one interaction, dispatches
parallel conversions, and enforces the `LAWDOG_PDF_SIZE` JEC limit.

```
/lawdog:juntada obra-irregular
/lawdog:juntada obra-irregular peticao-02
```

---

### Conversion skills

Invoked by `juntada`, also usable directly:

| Skill | Input → Output | Notes |
|---|---|---|
| `img2pdf` | `.jpg` `.png` `.heic` → `.pdf` | Quality reduction if > `LAWDOG_PDF_SIZE` |
| `doc2pdf` | `.md` `.txt` `.doc` `.docx` → `.pdf` | Pandoc + pdflatex + `base-legal.latex` |
| `pdf-split` | `.pdf` >4MB → parts `-1.pdf` `-2.pdf` | Document PDFs only — not for images |
| `doc2docx` | `.md` `.txt` → `.docx` | Editable; convert back to PDF before juntada |
```

- [ ] **Step 10.5: Update CLAUDE.md skills table**

In `CLAUDE.md`, update the pending skills list under `## Architecture` to show all as implemented at v0.3.0:

Change:
```
        ├── img2pdf/       (PENDING) image → PDF
        ├── doc2pdf/       (PENDING) document → PDF via pandoc+pdflatex
        ├── pdf-split/     (PENDING) PDF > LAWDOG_PDF_SIZE → parts
        ├── doc2docx/      (PENDING) markdown → editable DOCX
        └── juntada/       (PENDING) evidence orchestrator
```

To:
```
        ├── img2pdf/       image → PDF (LAWDOG_PDF_SIZE quality reduction)
        ├── doc2pdf/       document → PDF via pandoc+pdflatex+base-legal.latex
        ├── pdf-split/     PDF > LAWDOG_PDF_SIZE → parts (pypdf + PEP 723)
        ├── doc2docx/      markdown → editable DOCX
        └── juntada/       evidence orchestrator (parallel sub-agent dispatch)
```

- [ ] **Step 10.6: Commit**

```bash
git add Makefile README.md plugin/.claude-plugin/plugin.json CLAUDE.md
git commit -m "docs: Makefile, README, plugin.json v0.3.0, CLAUDE.md for juntada stack"
```

---

## Task 11: Final Verification

- [ ] **Step 11.1: Run full test suite**

```bash
make test
```

Expected: all 8 suites pass.

- [ ] **Step 11.2: Verify 8 SKILL.md files validate**

```bash
python3 tests/validate_skill.py --all
```

Expected: `Results: 8/8 passed`

- [ ] **Step 11.3: Verify all scripts exist and are executable**

```bash
for f in \
    plugin/skills/img2pdf/scripts/img2pdf.sh \
    plugin/skills/doc2pdf/scripts/doc2pdf.sh \
    plugin/skills/pdf-split/scripts/pdf_split.py \
    plugin/skills/doc2docx/scripts/doc2docx.sh \
    plugin/skills/juntada/scripts/juntada.sh \
    plugin/templates/base-legal.latex; do
    [ -f "$f" ] && echo "  PASS: $f" || echo "  FAIL: missing $f"
done
```

Expected: 6 PASS lines.

- [ ] **Step 11.4: Verify LAWDOG_PDF_SIZE is referenced in all relevant scripts**

```bash
grep -rl "LAWDOG_PDF_SIZE" \
    plugin/scripts/setup.sh \
    plugin/skills/img2pdf/scripts/ \
    plugin/skills/pdf-split/scripts/ \
    plugin/skills/doc2pdf/SKILL.md \
    plugin/skills/juntada/SKILL.md 2>/dev/null | wc -l
```

Expected: ≥ 5 files reference the variable.

- [ ] **Step 11.5: End-to-end smoke test**

```bash
TMPDIR_IT=$(mktemp -d)
bash plugin/skills/juntada/scripts/juntada.sh mkdirs "$TMPDIR_IT/peticao-inicial"

# Stage a test image
convert -size 200x200 xc:green "$TMPDIR_IT/peticao-inicial/anexos/foto-dano.png"

# Convert to PDF
bash plugin/skills/img2pdf/scripts/img2pdf.sh \
    -i "$TMPDIR_IT/peticao-inicial/anexos/foto-dano.png" \
    -o "$TMPDIR_IT/peticao-inicial/juntada/01-foto-dano.pdf"

# Tag as processed
bash plugin/skills/juntada/scripts/juntada.sh \
    tag "$TMPDIR_IT/peticao-inicial/anexos/foto-dano.png"

# Verify results
[ -f "$TMPDIR_IT/peticao-inicial/juntada/01-foto-dano.pdf" ] && echo "PASS: juntada PDF created"
[ -f "$TMPDIR_IT/peticao-inicial/anexos/foto-dano.png.converted" ] && echo "PASS: original tagged"
[ ! -f "$TMPDIR_IT/peticao-inicial/anexos/foto-dano.png" ] && echo "PASS: original removed from pending"
PENDING=$(bash plugin/skills/juntada/scripts/juntada.sh \
    list-pending "$TMPDIR_IT/peticao-inicial/anexos")
[ -z "$PENDING" ] && echo "PASS: no pending files" || echo "FAIL: still pending: $PENDING"

rm -rf "$TMPDIR_IT"
```

Expected: 4 PASS lines.
