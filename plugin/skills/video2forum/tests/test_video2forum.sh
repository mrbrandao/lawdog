#!/usr/bin/env bash
# Tests for plugin/skills/video2forum/scripts/video2forum.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../scripts/video2forum.sh"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: video2forum.sh not found"; exit 0; }

# Use custom ffmpeg if system one lacks libx264
FFMPEG_BIN="${FFMPEG:-$(which ffmpeg 2>/dev/null || true)}"
FFPROBE_BIN="${FFPROBE:-$(which ffprobe 2>/dev/null || true)}"

# Check for libx264 support
if ! "$FFMPEG_BIN" -encoders 2>/dev/null | grep -q libx264; then
    # Try ~/bin/ffmpeg
    if [ -x "$HOME/bin/ffmpeg" ]; then
        FFMPEG_BIN="$HOME/bin/ffmpeg"
        FFPROBE_BIN="$HOME/bin/ffprobe"
    else
        echo "SKIP: ffmpeg with libx264 not found (set FFMPEG=/path/to/ffmpeg)"
        exit 0
    fi
fi

export FFMPEG="$FFMPEG_BIN"
export FFPROBE="$FFPROBE_BIN"

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running video2forum.sh tests (using $FFMPEG_BIN)..."

# Create test fixture: H.264+AAC MP4 (should passthrough)
"$FFMPEG_BIN" -f lavfi -i testsrc=duration=1:size=160x90:rate=5 \
              -f lavfi -i sine=frequency=440:duration=1 \
              -c:v libx264 -profile:v high -pix_fmt yuv420p \
              -c:a aac -b:a 64k -movflags +faststart \
              -y "$TMPDIR_T/h264_aac.mp4" >/dev/null 2>&1

# Create test fixture: WebM VP8 (must convert to MP4)
"$FFMPEG_BIN" -f lavfi -i testsrc=duration=1:size=160x90:rate=5 \
              -f lavfi -i sine=frequency=440:duration=1 \
              -c:v libvpx -c:a libvorbis \
              -y "$TMPDIR_T/vp8.webm" >/dev/null 2>&1

# Test 1: H.264+AAC MP4 → passthrough (output is identical copy)
bash "$SCRIPT" -i "$TMPDIR_T/h264_aac.mp4" -o "$TMPDIR_T/pass.mp4" 2>/dev/null
[ -f "$TMPDIR_T/pass.mp4" ] && pass "H.264+AAC → output created" || fail "no output"
IN_SIZE=$(stat -c%s "$TMPDIR_T/h264_aac.mp4" 2>/dev/null || stat -f%z "$TMPDIR_T/h264_aac.mp4")
OUT_SIZE=$(stat -c%s "$TMPDIR_T/pass.mp4" 2>/dev/null || stat -f%z "$TMPDIR_T/pass.mp4")
[ "$IN_SIZE" -eq "$OUT_SIZE" ] && pass "H.264+AAC → passthrough (sizes match)" || \
    fail "passthrough changed size (in=$IN_SIZE out=$OUT_SIZE)"

# Test 2: WebM VP8 → converted to MP4 (different file, re-encoded)
bash "$SCRIPT" -i "$TMPDIR_T/vp8.webm" -o "$TMPDIR_T/conv.mp4" 2>/dev/null
[ -f "$TMPDIR_T/conv.mp4" ] && pass "VP8 WebM → MP4 output created" || fail "no MP4 output"
WEBM_SIZE=$(stat -c%s "$TMPDIR_T/vp8.webm" 2>/dev/null || stat -f%z "$TMPDIR_T/vp8.webm")
MP4_SIZE=$(stat -c%s "$TMPDIR_T/conv.mp4" 2>/dev/null || stat -f%z "$TMPDIR_T/conv.mp4")
[ "$WEBM_SIZE" -ne "$MP4_SIZE" ] && pass "VP8 → MP4 re-encoded (sizes differ)" || \
    fail "VP8 → MP4 sizes equal (passthrough when should convert?)"

# Test 3: --webm flag forces WebM output from MP4 input
bash "$SCRIPT" -i "$TMPDIR_T/h264_aac.mp4" -o "$TMPDIR_T/forced.webm" --webm 2>/dev/null
[ -f "$TMPDIR_T/forced.webm" ] && pass "--webm flag creates WebM output" || fail "no WebM output"
WEBM_OUT=$(stat -c%s "$TMPDIR_T/forced.webm" 2>/dev/null || stat -f%z "$TMPDIR_T/forced.webm")
[ "$IN_SIZE" -ne "$WEBM_OUT" ] && pass "--webm produced different file (re-encoded)" || \
    fail "--webm identical to input (should have re-encoded)"

# Test 4: missing input exits nonzero with error message on stderr
OUTPUT=$(bash "$SCRIPT" -i "$TMPDIR_T/nope.mp4" -o "$TMPDIR_T/out.mp4" 2>&1 || true)
echo "$OUTPUT" | grep -qi "error\|not found" && pass "missing input gives error" || \
    fail "missing input silent"

# Test 5: --help produces usage on stdout or stderr
bash "$SCRIPT" --help 2>&1 | grep -qi "usage\|-i\|webm" && \
    pass "--help produces usage" || fail "--help not implemented"

echo ""
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
