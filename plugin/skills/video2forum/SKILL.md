---
name: video2forum
description: >-
  Convert video files (.MOV, .MP4, .AVI, .MKV, etc.) to WebM format
  required by Brazilian court systems (PROJUDI/TJPR) and legal forums.
  Activate on: /lawdog:video2forum, convert videos for forum,
  convert .mov to webm, videos for PROJUDI, forum video upload,
  court-compatible video conversion.
compatibility: >-
  Requires ffmpeg in PATH, or set FFMPEG=/path/to/ffmpeg.
  Static builds at https://johnvansickle.com/ffmpeg/ or
  https://www.ffmpeg.org/download.html
allowed-tools: Bash
metadata:
  author: mrbrandao
  version: "1.1"
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

## Steps

1. **ffmpeg setup** — Scan the raw args for a token that looks like an
   ffmpeg binary path (ends with `/ffmpeg` or equals `ffmpeg`). If found:
   - `export FFMPEG=<path>` and remove that token from the file list.
   If no such token is present, leave `FFMPEG` unset — the script
   auto-detects via `which ffmpeg` and prints a clear error if not found.
   **Never ask the user.**

2. **Expand** glob(s) into a concrete file list. Abort with a clear
   message if no files matched.

3. **Derive output path** for each file: same directory, same base
   name, extension → `.webm`.

4. **Convert** all files in parallel — launch each conversion as a
   background task (`run_in_background: true`). Use:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/video2forum.sh" \
     -i "<input>" -o "<output>"
   ```
   With custom ffmpeg:
   ```bash
   FFMPEG="$FFMPEG" bash "${CLAUDE_SKILL_DIR}/scripts/video2forum.sh" \
     -i "<input>" -o "<output>"
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

Output: VP8 video + Vorbis audio, WebM container, 500 kbps video,
Vorbis quality 4. Matches PROJUDI/TJPR court system requirements.
