#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../plugin/skills/doc2pdf/scripts/doc2pdf.py"
TEMPLATE="$SCRIPT_DIR/../plugin/templates/base-legal.latex"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: doc2pdf.py not found"; exit 0; }
command -v uv >/dev/null 2>&1 || { echo "SKIP: uv not found"; exit 0; }

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running doc2pdf.py tests..."

uv run "$SCRIPT" --help 2>&1 | grep -qi "usage\|-i\|input" && \
    pass "--help produces usage" || fail "--help not implemented"

cat > "$TMPDIR_T/test.md" <<'MDEOF'
---
title: "Teste"
---

## Dos Fatos

Fato.

## Dos Pedidos

1. Pedido.
MDEOF
uv run "$SCRIPT" -i "$TMPDIR_T/test.md" -o "$TMPDIR_T/t1.pdf" -t "$TEMPLATE" >/dev/null 2>&1
[ -f "$TMPDIR_T/t1.pdf" ] && pass ".md → PDF created" || fail ".md → PDF not created"
file "$TMPDIR_T/t1.pdf" | grep -q PDF && pass "output is valid PDF" || fail "not valid PDF"

echo "Texto simples." > "$TMPDIR_T/test.txt"
uv run "$SCRIPT" -i "$TMPDIR_T/test.txt" -o "$TMPDIR_T/t2.pdf" >/dev/null 2>&1
[ -f "$TMPDIR_T/t2.pdf" ] && pass ".txt → PDF created" || fail ".txt → PDF not created"

SIZE=$(stat -c%s "$TMPDIR_T/t1.pdf" 2>/dev/null || stat -f%z "$TMPDIR_T/t1.pdf")
[ "$SIZE" -lt "${LAWDOG_PDF_SIZE:-4194304}" ] && pass "output under size limit" || fail "exceeds limit"

uv run "$SCRIPT" -i "$TMPDIR_T/nope.md" -o "$TMPDIR_T/out.pdf" 2>&1 | \
    grep -qi "error\|not found" && pass "missing input gives error" || fail "missing input silent"

echo ""; echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
