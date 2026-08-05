# video2forum v1.2 — MP4 Default Format Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update video2forum to use MP4/H.264+AAC as the default output (proven accepted by PROJUDI with better quality), with probe-based passthrough for already-compatible files and WebM as an explicit --webm fallback.

**Architecture:** video2forum.sh gains three modes: (1) passthrough when input is already H.264+AAC MP4, (2) convert to MP4/H.264+AAC for other formats, (3) convert to WebM with --webm flag. ffprobe determines which mode to use. SKILL.md is updated to document the new behavior, fallback guidance, and version bumped to 1.2.

**Tech Stack:** bash, ffmpeg (libx264, aac), ffprobe (codec detection), existing lawdog skill patterns.

---

## File Map

| Action | Path | Change |
|---|---|---|
| Modify | `plugin/skills/video2forum/scripts/video2forum.sh` | Probe logic, MP4 default, --webm flag, passthrough |
| Create | `plugin/skills/video2forum/tests/test_video2forum.sh` | Per-skill tests (passthrough, conversion, --webm, error) |
| Modify | `plugin/skills/video2forum/SKILL.md` | Description, format spec, fallback guidance, v1.2 |
| Modify | `plugin/.claude-plugin/plugin.json` | Version bump |
| Modify | `plugin/.claude-plugin/marketplace.json` | Version bump |
| Modify | `CLAUDE.md` | Plugin versioning rule |
| Modify | `Makefile` | Add test-video2forum target |

---

## Task 1: Update video2forum.sh with probe + MP4 default

**Files:**
- Modify: `plugin/skills/video2forum/scripts/video2forum.sh`

- [ ] **Step 1.1: Read current video2forum.sh**

```bash
cat plugin/skills/video2forum/scripts/video2forum.sh
```

- [ ] **Step 1.2: Replace video2forum.sh with the new implementation**

Write `plugin/skills/video2forum/scripts/video2forum.sh`:

```bash
#!/usr/bin/env bash
# Converts video files for PROJUDI/TJPR forum upload.
# Default output: MP4/H.264+AAC (proven PROJUDI-compatible, better quality).
# Passthrough: if input is already H.264+AAC MP4, copies without re-encoding.
# Fallback: WebM/VP8+Vorbis with --webm flag when forum rejects MP4.
#
# Usage: video2forum.sh -i <input> -o <output> [--webm]
set -euo pipefail

FFMPEG="${FFMPEG:-$(which ffmpeg 2>/dev/null || true)}"
FFPROBE="${FFPROBE:-$(which ffprobe 2>/dev/null || true)}"
WEBM=false

usage() {
    echo "Usage: video2forum.sh -i <input> -o <output.mp4|.webm> [--webm]"
    echo "  Default: converts to MP4/H.264+AAC (PROJUDI preferred format)"
    echo "  --webm   Force WebM output (fallback if forum rejects MP4)"
    exit "${1:-1}"
}

# ── arg parsing ────────────────────────────────────────────────────────────

INPUT="" OUTPUT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -i)     INPUT="$2";  shift 2 ;;
        -o)     OUTPUT="$2"; shift 2 ;;
        --webm) WEBM=true;   shift   ;;
        -h|--help) usage 0 ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

[[ -z "$INPUT" || -z "$OUTPUT" ]] && { echo "ERROR: -i and -o are required" >&2; usage; }
[[ ! -f "$INPUT" ]] && { echo "ERROR: Input not found: $INPUT" >&2; exit 1; }

if [[ -z "$FFMPEG" || ! -x "$FFMPEG" ]]; then
    echo "ERROR: ffmpeg not found. Install or set FFMPEG=/path/to/ffmpeg" >&2
    exit 1
fi

# ── probe: check if input is already H.264 + AAC in MP4 container ──────────
# Returns 0 (true) if passthrough is safe. Returns 1 if ffprobe unavailable
# (degrade gracefully: always re-encode when probe is not possible).

is_h264_aac_mp4() {
    local file="$1"
    [[ -z "$FFPROBE" || ! -x "$FFPROBE" ]] && return 1

    local fmt video_codec audio_codec
    fmt=$("$FFPROBE" -v quiet -show_entries format=format_name \
        -of csv=p=0 "$file" 2>/dev/null | head -1)
    video_codec=$("$FFPROBE" -v quiet -select_streams v:0 \
        -show_entries stream=codec_name -of csv=p=0 "$file" 2>/dev/null | head -1)
    audio_codec=$("$FFPROBE" -v quiet -select_streams a:0 \
        -show_entries stream=codec_name -of csv=p=0 "$file" 2>/dev/null | head -1)

    # Both video and audio codecs must match AND container must be MP4/MOV
    [[ ("$fmt" == *"mp4"* || "$fmt" == *"mov"*) \
       && "$video_codec" == "h264" \
       && "$audio_codec" == "aac" ]]
}

# ── convert ────────────────────────────────────────────────────────────────

echo "Processing: $INPUT → $OUTPUT" >&2

if [[ "$WEBM" == "true" ]]; then
    # Mode: WebM fallback (VP8+Vorbis — legacy format for older PROJUDI setups)
    echo "  Mode: WebM/VP8+Vorbis (--webm fallback)" >&2
    "$FFMPEG" -v quiet -stats \
        -i "$INPUT" \
        -c:v libvpx -quality good -cpu-used 5 -threads 4 -b:v 500k \
        -c:a libvorbis -q:a 4 \
        -y "$OUTPUT"

elif is_h264_aac_mp4 "$INPUT"; then
    # Mode: passthrough (input already correct format — copy without re-encoding)
    echo "  Mode: passthrough (H.264+AAC detected — no re-encode needed)" >&2
    cp "$INPUT" "$OUTPUT"

else
    # Mode: convert to MP4/H.264+AAC
    # Specs match reference file proven by PROJUDI: High Profile, Level 3.0,
    # CRF 23 (~1-2Mbps), AAC 128kbps 48kHz, +faststart for browser streaming
    echo "  Mode: convert to MP4/H.264+AAC" >&2
    "$FFMPEG" -v quiet -stats \
        -i "$INPUT" \
        -c:v libx264 -profile:v high -level:v 3.0 -pix_fmt yuv420p \
        -crf 23 -threads 4 \
        -c:a aac -b:a 128k -ar 48000 \
        -movflags +faststart \
        -y "$OUTPUT"
fi

echo "Done: $OUTPUT" >&2
```

- [ ] **Step 1.3: Make executable and run shellcheck**

```bash
chmod +x plugin/skills/video2forum/scripts/video2forum.sh
shellcheck plugin/skills/video2forum/scripts/video2forum.sh
```

Expected: no output (no errors).

- [ ] **Step 1.4: Quick smoke test — passthrough detection**

```bash
# Create a minimal H.264+AAC MP4 test file
ffmpeg -f lavfi -i testsrc=duration=1:size=160x90:rate=5 \
       -f lavfi -i sine=frequency=440:duration=1 \
       -c:v libx264 -profile:v high -pix_fmt yuv420p \
       -c:a aac -b:a 64k -movflags +faststart \
       -y /tmp/ld_test_h264.mp4 2>/dev/null

bash plugin/skills/video2forum/scripts/video2forum.sh \
    -i /tmp/ld_test_h264.mp4 \
    -o /tmp/ld_test_out.mp4 2>&1
```

Expected: output shows `Mode: passthrough (H.264+AAC detected — no re-encode needed)`.

- [ ] **Step 1.5: Commit**

```bash
git add plugin/skills/video2forum/scripts/video2forum.sh
git commit -m "feat(video2forum): MP4/H.264+AAC default with probe passthrough"
git push bare main
```

---

## Task 2: Add per-skill tests

**Files:**
- Create: `plugin/skills/video2forum/tests/test_video2forum.sh`

- [ ] **Step 2.1: Create tests directory and write test file**

```bash
mkdir -p plugin/skills/video2forum/tests
```

Write `plugin/skills/video2forum/tests/test_video2forum.sh`:

```bash
#!/usr/bin/env bash
# Tests for plugin/skills/video2forum/scripts/video2forum.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/../scripts/video2forum.sh"
PASS_COUNT=0; FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ -f "$SCRIPT" ] || { echo "SKIP: video2forum.sh not found"; exit 0; }
command -v ffmpeg >/dev/null 2>&1 || { echo "SKIP: ffmpeg not found"; exit 0; }
command -v ffprobe >/dev/null 2>&1 || { echo "SKIP: ffprobe not found"; exit 0; }

TMPDIR_T="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_T"' EXIT

echo "Running video2forum.sh tests..."

# Create test fixture: H.264+AAC MP4 (should passthrough)
ffmpeg -f lavfi -i testsrc=duration=1:size=160x90:rate=5 \
       -f lavfi -i sine=frequency=440:duration=1 \
       -c:v libx264 -profile:v high -pix_fmt yuv420p \
       -c:a aac -b:a 64k -movflags +faststart \
       -y "$TMPDIR_T/h264_aac.mp4" >/dev/null 2>&1

# Create test fixture: WebM VP8 (must convert)
ffmpeg -f lavfi -i testsrc=duration=1:size=160x90:rate=5 \
       -f lavfi -i sine=frequency=440:duration=1 \
       -c:v libvpx -c:a libvorbis \
       -y "$TMPDIR_T/vp8.webm" >/dev/null 2>&1

# Test 1: H.264+AAC MP4 → passthrough (output = copy of input)
bash "$SCRIPT" -i "$TMPDIR_T/h264_aac.mp4" -o "$TMPDIR_T/pass.mp4" >/dev/null 2>&1
[ -f "$TMPDIR_T/pass.mp4" ] && pass "H.264+AAC → output created" || fail "no output"
IN_SIZE=$(stat -c%s "$TMPDIR_T/h264_aac.mp4" 2>/dev/null || stat -f%z "$TMPDIR_T/h264_aac.mp4")
OUT_SIZE=$(stat -c%s "$TMPDIR_T/pass.mp4" 2>/dev/null || stat -f%z "$TMPDIR_T/pass.mp4")
[ "$IN_SIZE" -eq "$OUT_SIZE" ] && pass "H.264+AAC → passthrough (sizes match)" || \
    fail "passthrough changed size (in=$IN_SIZE out=$OUT_SIZE)"

# Test 2: WebM VP8 → converted to MP4
bash "$SCRIPT" -i "$TMPDIR_T/vp8.webm" -o "$TMPDIR_T/conv.mp4" >/dev/null 2>&1
[ -f "$TMPDIR_T/conv.mp4" ] && pass "VP8 WebM → MP4 output created" || fail "no MP4 output"
# Verify it's a different size from input (was re-encoded)
WEBM_SIZE=$(stat -c%s "$TMPDIR_T/vp8.webm" 2>/dev/null || stat -f%z "$TMPDIR_T/vp8.webm")
MP4_SIZE=$(stat -c%s "$TMPDIR_T/conv.mp4" 2>/dev/null || stat -f%z "$TMPDIR_T/conv.mp4")
[ "$WEBM_SIZE" -ne "$MP4_SIZE" ] && pass "VP8 → MP4 produced different file (re-encoded)" || \
    fail "VP8 → MP4 output unchanged (passthrough when should convert?)"

# Test 3: --webm flag forces WebM output from MP4 input
bash "$SCRIPT" -i "$TMPDIR_T/h264_aac.mp4" -o "$TMPDIR_T/forced.webm" --webm >/dev/null 2>&1
[ -f "$TMPDIR_T/forced.webm" ] && pass "--webm flag creates WebM output" || fail "no WebM output"
# WebM must be different from MP4 input (was re-encoded to VP8+Vorbis)
WEBM_OUT_SIZE=$(stat -c%s "$TMPDIR_T/forced.webm" 2>/dev/null || stat -f%z "$TMPDIR_T/forced.webm")
[ "$IN_SIZE" -ne "$WEBM_OUT_SIZE" ] && pass "--webm produced different file (re-encoded)" || \
    fail "--webm output identical to input (passthrough when should convert)"

# Test 4: missing input exits nonzero with error message
bash "$SCRIPT" -i "$TMPDIR_T/nope.mp4" -o "$TMPDIR_T/out.mp4" 2>&1 | \
    grep -qi "error\|not found" && pass "missing input gives error" || fail "missing input silent"

# Test 5: --help produces usage
bash "$SCRIPT" --help 2>&1 | grep -qi "usage\|-i\|webm" && \
    pass "--help produces usage" || fail "--help not implemented"

echo ""
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
```

- [ ] **Step 2.2: Run tests**

```bash
bash plugin/skills/video2forum/tests/test_video2forum.sh
```

Expected: 5/5 passed.

- [ ] **Step 2.3: Commit**

```bash
git add plugin/skills/video2forum/tests/test_video2forum.sh
git commit -m "test(video2forum): add per-skill tests for MP4 passthrough and WebM fallback"
git push bare main
```

---

## Task 3: Update SKILL.md to v1.2

**Files:**
- Modify: `plugin/skills/video2forum/SKILL.md`

- [ ] **Step 3.1: Read current SKILL.md**

```bash
cat plugin/skills/video2forum/SKILL.md
```

- [ ] **Step 3.2: Update the description**

Replace the current `description` in the frontmatter with:

```yaml
description: >-
  Prepares video files for PROJUDI/TJPR upload: MP4/H.264+AAC (preferred, proven
  PROJUDI-compatible) or WebM (fallback with --webm flag). Automatically detects
  if input is already H.264+AAC — passes through without re-encoding to preserve
  quality. For MOV, AVI, MKV, VP8/VP9 inputs: converts to MP4/H.264+AAC.
  Activate on: /lawdog:video2forum, convert videos for forum, converter vídeo para
  PROJUDI, vídeo para tribunal, videos for upload, court-compatible video.
```

- [ ] **Step 3.3: Update metadata version**

Change `version: "1.1"` to `version: "1.2"`.

- [ ] **Step 3.4: Replace the Format spec section**

Find `## Format spec` and replace with:

```markdown
## Format spec

**Default output — MP4 (PROJUDI preferred):**
- Container: MP4 with +faststart (browser streaming optimized)
- Video: H.264, High Profile, Level 3.0, yuv420p, CRF 23 (~1-2Mbps)
- Audio: AAC, 128kbps, 48kHz, stereo
- Reference: file proven accepted by PROJUDI/TJPR (4.2MB/24s)

**Passthrough:** if input is already H.264+AAC in MP4 container, the file is
copied directly without re-encoding. Zero quality loss, instant.

**Fallback — WebM (--webm flag):**
- Container: WebM
- Video: VP8, 500kbps
- Audio: Vorbis, quality 4
- Use when: forum rejects MP4 (older PROJUDI setups)

**If MP4 is rejected by the forum:**
> "O PROJUDI não aceitou o MP4? Use `--webm` para o formato legado:
> `/lawdog:video2forum --webm <arquivo>`"
```

- [ ] **Step 3.5: Update the Fluxo section to reflect new behavior**

In the Fluxo section, update Step 3 (Derive output path) and Step 4 (Convert):

Replace Step 3:
```markdown
3. **Derive output path** for each file: same directory, same base
   name, extension → `.mp4` (default) or `.webm` (with --webm flag).
```

Replace Step 4:
```markdown
4. **Convert** all files in parallel — launch each conversion as a
   background task (`run_in_background: true`). Use:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/video2forum.sh" \
     -i "<input>" -o "<output>.mp4"
   ```
   For WebM fallback:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/video2forum.sh" \
     -i "<input>" -o "<output>.webm" --webm
   ```
   Wait for all background tasks to finish before proceeding to Step 5.
```

- [ ] **Step 3.6: Validate SKILL.md**

```bash
python3 tests/validate_skill.py plugin/skills/video2forum/SKILL.md
```

Expected: PASS.

- [ ] **Step 3.7: Run make test-skills**

```bash
make test-skills
```

Expected: all 11 SKILL.md pass.

- [ ] **Step 3.8: Commit**

```bash
git add plugin/skills/video2forum/SKILL.md
git commit -m "feat(video2forum): update SKILL.md v1.2 — MP4 default, passthrough, WebM fallback"
git push bare main
```

---

## Task 4: Bump plugin versions + update CLAUDE.md

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json`
- Modify: `plugin/.claude-plugin/marketplace.json`
- Modify: `CLAUDE.md`

- [ ] **Step 4.1: Bump plugin.json to 0.5.0**

Read `plugin/.claude-plugin/plugin.json`. Change `"version": "0.4.0"` to `"version": "0.5.0"`.

- [ ] **Step 4.2: Bump marketplace.json to 0.5.0**

Read `plugin/.claude-plugin/marketplace.json`. Change `"version": "0.4.0"` to `"version": "0.5.0"`.

- [ ] **Step 4.3: Add plugin versioning rule to CLAUDE.md**

Read `CLAUDE.md`. After the `## Conventions` table section, add a new section:

```markdown
## Plugin versioning — when to bump and reinstall

Any change that affects **observable behavior for the user** requires:
1. Bump version in `plugin/.claude-plugin/plugin.json`
2. Bump version in `plugin/.claude-plugin/marketplace.json`
3. User must reinstall the plugin in Claude Code:
   ```bash
   /plugin uninstall lawdog
   /plugin install /path/to/lawdog/plugin
   ```

**Changes that require version bump + reinstall:**
- Default output format of any skill changes (e.g., video2forum: WebM → MP4)
- New skill added or skill removed
- Session hook behavior changes
- SKILL.md trigger phrases change (affects when skill activates)

**Changes that do NOT require reinstall:**
- Protocol or knowledge file updates (loaded at skill activation time)
- Bug fixes that don't change observable behavior
- BACKLOG and docs updates
```

- [ ] **Step 4.4: Verify version consistency**

```bash
grep '"version"' plugin/.claude-plugin/plugin.json plugin/.claude-plugin/marketplace.json
```

Expected: both show `"version": "0.5.0"`

- [ ] **Step 4.5: Commit and push**

```bash
git add plugin/.claude-plugin/plugin.json plugin/.claude-plugin/marketplace.json CLAUDE.md
git commit -m "chore: bump plugin to 0.5.0, add versioning rule to CLAUDE.md"
git push bare main
```

---

## Task 5: Update Makefile and run full verification

**Files:**
- Modify: `Makefile`

- [ ] **Step 5.1: Read current Makefile**

```bash
cat Makefile
```

- [ ] **Step 5.2: Add test-video2forum target**

Add to `.PHONY` line: `test-video2forum`

Add to `test:` dependency list: `test-video2forum`

Add the new target after the existing test targets:

```makefile
test-video2forum:
	@echo "=== Testing video2forum ==="
	@bash plugin/skills/video2forum/tests/test_video2forum.sh
```

- [ ] **Step 5.3: Run full test suite**

```bash
make test
```

Expected: all suites pass, including the new test-video2forum (5 tests).

- [ ] **Step 5.4: Verify passthrough behavior end-to-end with real file**

```bash
# Use the actual PROJUDI-accepted file as reference
REFERENCE="/home/user/lawdog-cases/obra-irregular-sobrado04/20-manifestacao-liminar-reu/docs/20.6-Video-Pedreiro-Ausencia-Risco-Danos.mp4"

if [ -f "$REFERENCE" ]; then
    bash plugin/skills/video2forum/scripts/video2forum.sh \
        -i "$REFERENCE" \
        -o /tmp/ld_reference_test.mp4 2>&1
    
    IN_SIZE=$(stat -c%s "$REFERENCE" 2>/dev/null || stat -f%z "$REFERENCE")
    OUT_SIZE=$(stat -c%s /tmp/ld_reference_test.mp4 2>/dev/null || stat -f%z /tmp/ld_reference_test.mp4)
    
    [ "$IN_SIZE" -eq "$OUT_SIZE" ] && \
        echo "PASS: Reference PROJUDI file → passthrough (sizes match: ${IN_SIZE} bytes)" || \
        echo "WARN: Reference file was re-encoded (input: ${IN_SIZE}, output: ${OUT_SIZE})"
    
    rm -f /tmp/ld_reference_test.mp4
else
    echo "SKIP: Reference file not available"
fi
```

Expected: `PASS: Reference PROJUDI file → passthrough (sizes match: 4364288 bytes)`

- [ ] **Step 5.5: Commit Makefile and push**

```bash
git add Makefile
git commit -m "build: add test-video2forum to Makefile"
git push bare main
```
