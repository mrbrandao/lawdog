#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../plugin/skills/img2pdf/scripts/image_to_pdf.py"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: image_to_pdf.py not found"; exit 0; }
command -v uv >/dev/null 2>&1 || { echo "SKIP: uv not found"; exit 0; }

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running img2pdf.py tests..."

# Test 1: --help works (required by agentskills.io spec)
uv run "$SCRIPT" --help 2>&1 | grep -qi "usage\|input\|-i" && \
    pass "--help produces usage" || fail "--help not implemented"

# Test 2: PNG → valid PDF
magick -size 100x100 xc:blue "$TMPDIR_T/blue.png" 2>/dev/null || convert -size 100x100 xc:blue "$TMPDIR_T/blue.png"
uv run "$SCRIPT" -i "$TMPDIR_T/blue.png" -o "$TMPDIR_T/blue.pdf" >/dev/null 2>&1
[ -f "$TMPDIR_T/blue.pdf" ] && pass "PNG → PDF created" || fail "PNG → PDF not created"
file "$TMPDIR_T/blue.pdf" | grep -q PDF && pass "output is valid PDF" || fail "not valid PDF"

# Test 3: JPEG → PDF
magick -size 100x100 xc:red "$TMPDIR_T/red.jpg" 2>/dev/null || convert -size 100x100 xc:red "$TMPDIR_T/red.jpg"
uv run "$SCRIPT" -i "$TMPDIR_T/red.jpg" -o "$TMPDIR_T/red.pdf" >/dev/null 2>&1
[ -f "$TMPDIR_T/red.pdf" ] && pass "JPEG → PDF created" || fail "JPEG → PDF not created"

# Test 4: output respects LAWDOG_PDF_SIZE
SIZE=$(stat -c%s "$TMPDIR_T/blue.pdf" 2>/dev/null || stat -f%z "$TMPDIR_T/blue.pdf")
[ "$SIZE" -lt "${LAWDOG_PDF_SIZE:-4194304}" ] && pass "output under size limit" || fail "exceeds size limit"

# Test 5: missing input exits non-zero with error message
err_out=$(uv run "$SCRIPT" -i "$TMPDIR_T/nope.png" -o "$TMPDIR_T/out.pdf" 2>&1 || true)
echo "$err_out" | grep -qi "error\|not found" && \
    pass "missing input gives error" || fail "missing input silent"

echo ""; echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
