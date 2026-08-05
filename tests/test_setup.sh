#!/usr/bin/env bash
# Tests for plugin/scripts/setup.sh
# Usage: bash tests/test_setup.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETUP_SCRIPT="$SCRIPT_DIR/../plugin/scripts/setup.sh"
PASS_COUNT=0
FAIL_COUNT=0

# ── helpers ────────────────────────────────────────────────────────────────

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

run_setup() {
    # $1 = stdin input (empty string = Enter/default)
    local input="$1"
    echo "$input" | bash "$SETUP_SCRIPT" >/dev/null 2>&1 || true
}

detect_test_profile() {
    if [ -f "$TMPDIR_TEST/.zshrc" ]; then echo "$TMPDIR_TEST/.zshrc"
    elif [ -f "$TMPDIR_TEST/.bashrc" ]; then echo "$TMPDIR_TEST/.bashrc"
    fi
}

assert_dir_exists() {
    local dir="$1" label="$2"
    [ -d "$dir" ] && pass "$label" || fail "$label (dir not found: $dir)"
}

assert_file_contains() {
    local file="$1" pattern="$2" label="$3"
    grep -q "$pattern" "$file" 2>/dev/null && pass "$label" || fail "$label (pattern not in $file)"
}

assert_count_le() {
    local file="$1" pattern="$2" max="$3" label="$4"
    local count
    count=$(grep -c "$pattern" "$file" 2>/dev/null || echo 0)
    [ "$count" -le "$max" ] && pass "$label" || fail "$label (count=$count, max=$max)"
}

# ── setup ──────────────────────────────────────────────────────────────────

TMPDIR_TEST="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR_TEST"; }
trap cleanup EXIT
export HOME="$TMPDIR_TEST"

# ── tests ──────────────────────────────────────────────────────────────────

echo "Running setup.sh tests..."

[ -f "$SETUP_SCRIPT" ] || { echo "SKIP: setup.sh not found at $SETUP_SCRIPT (run Task 2 first)"; exit 0; }

# Test 1: Default (empty input) creates ~/lawdog-cases
run_setup ""
assert_dir_exists "$TMPDIR_TEST/lawdog-cases" "default input creates ~/lawdog-cases"

# Test 2: Custom absolute path is created
CUSTOM_DIR="$TMPDIR_TEST/my-legal-cases"
run_setup "$CUSTOM_DIR"
assert_dir_exists "$CUSTOM_DIR" "custom path is created"

# Test 3: LAWDOG_CASES_DIR is written to shell profile
run_setup ""
PROFILE="$(detect_test_profile)"
[ -n "$PROFILE" ] && assert_file_contains "$PROFILE" "LAWDOG_CASES_DIR" \
    "LAWDOG_CASES_DIR exported to shell profile" || \
    fail "No shell profile created"

# Test 4: Script is idempotent — no duplicate exports
run_setup ""
run_setup ""
PROFILE="$(detect_test_profile)"
[ -n "$PROFILE" ] && assert_count_le "$PROFILE" "LAWDOG_CASES_DIR" 1 \
    "idempotent: no duplicate LAWDOG_CASES_DIR in profile" || \
    fail "No shell profile found for idempotency check"

# Test 5: Tilde expansion — ~/custom becomes absolute path
run_setup "~/lawdog-alt"
assert_dir_exists "$TMPDIR_TEST/lawdog-alt" "tilde expansion works"

# ── summary ────────────────────────────────────────────────────────────────

echo ""
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
