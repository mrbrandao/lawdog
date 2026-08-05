---
name: video2forum
description: >-
  Prepares video files for PROJUDI/TJPR upload: MP4/H.264+AAC (preferred, proven
  PROJUDI-compatible) or WebM (fallback with --webm flag when forum rejects MP4).
  Automatically detects if input is already H.264+AAC — passes through without
  re-encoding to preserve quality. MOV, AVI, MKV, VP8/VP9: converted to MP4/H.264+AAC.
  Activate on: /lawdog:video2forum, convert videos for forum, converter vídeo para
  PROJUDI, vídeo para tribunal, videos for upload, court-compatible video.
compatibility: >-
  Requires ffmpeg in PATH, or set FFMPEG=/path/to/ffmpeg.
  Static builds at https://johnvansickle.com/ffmpeg/ or
  https://www.ffmpeg.org/download.html
allowed-tools: Bash
metadata:
  author: mrbrandao
  version: "1.2"
---

## Trigger

User types `/lawdog:video2forum <path-or-glob>` or asks to convert
video files to WebM for court/forum upload.

## Input

One or more file paths or glob patterns. Examples:

- `/lawdog:video2forum ~/videos/evidence.MOV`
- `/lawdog:video2forum ~/docs/case/*.MOV`
- `/lawdog:video2forum /path/*.mov /path/*.mp4`

## Output

Each input file converted to `.webm` in the same directory, same
base name, overwriting if exists.

## Fluxo

1. **ffmpeg setup** — Scan the raw args for a token that looks like an
   ffmpeg binary path (ends with `/ffmpeg` or equals `ffmpeg`). If found:
   - `export FFMPEG=<path>` and remove that token from the file list.
   If no such token is present, leave `FFMPEG` unset — the script
   auto-detects via `which ffmpeg` and prints a clear error if not found.
   **Never ask the user.**

2. **Expand** glob(s) into a concrete file list. Abort with a clear
   message if no files matched.

3. **Derive output path** for each file: same directory, same base
   name, extension → `.mp4` (default) or `.webm` (with --webm flag).

4. **Convert** all files in parallel — launch each conversion as a
   background task (`run_in_background: true`). Use:
   ```bash
   FFMPEG="${FFMPEG:-$HOME/bin/ffmpeg}" \
   bash "${CLAUDE_SKILL_DIR}/scripts/video2forum.sh" \
     -i "<input>" -o "<output>.mp4"
   ```
   For WebM fallback (--webm):
   ```bash
   FFMPEG="${FFMPEG:-$HOME/bin/ffmpeg}" \
   bash "${CLAUDE_SKILL_DIR}/scripts/video2forum.sh" \
     -i "<input>" -o "<output>.webm" --webm
   ```
   Wait for all background tasks to finish before proceeding to Step 5.

5. **Report** after all conversions: total count, each
   input → output pair, output file size.

## Error handling

Never mask or summarize errors. Always surface raw script output —
exit codes, stderr, and stdout — directly to the user and agent
context so the root cause is visible. On any failure:

- Show the complete raw error output from the script.
- Skip that file and continue with remaining files.
- Include failed files in the final report.

## Format spec

**Default output — MP4 (PROJUDI preferred):**
- Container: MP4 with +faststart (browser streaming optimized)
- Video: H.264, High Profile, Level 3.0, yuv420p, CRF 23 (~1-2Mbps)
- Audio: AAC, 128kbps, 48kHz, stereo
- Reference: format proven accepted by PROJUDI/TJPR

**Passthrough:** if input is already H.264+AAC in MP4 container, copied
directly without re-encoding. Zero quality loss, instant operation.

**Fallback — WebM (--webm flag):**
- Container: WebM, Video: VP8 500kbps, Audio: Vorbis quality 4
- Use when: PROJUDI rejects the MP4 (rare — older court setups)

**If MP4 is rejected by the forum, say in Portuguese:**
> "O PROJUDI não aceitou o MP4? Use `--webm` para o formato legado:
> `/lawdog:video2forum --webm <arquivo>`"

**Output is silent during conversion** — no frame-by-frame progress.
Only start, mode, and completion messages are shown. Real errors ARE
printed so the agent can diagnose and advise the user.

**Custom ffmpeg:** if `~/bin/ffmpeg` exists with full codec support,
set `FFMPEG=~/bin/ffmpeg` before calling the script. The system ffmpeg
may lack libx264.
