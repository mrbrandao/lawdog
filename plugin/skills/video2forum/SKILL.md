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
  version: "1.0"
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

1. **ffmpeg setup (first run)** — If `FFMPEG` is not set, ask:
   > "Which ffmpeg to use? Enter a path or press Enter to
   > auto-detect via PATH."
   - User provides path → `export FFMPEG=<path>` before proceeding.
   - User presses Enter → leave unset; script auto-detects via
     `which ffmpeg`.

2. **Expand** glob(s) into a concrete file list. Abort with a clear
   message if no files matched.

3. **Derive output path** for each file: same directory, same base
   name, extension → `.webm`.

4. **Convert** each file using the bundled script:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/video2forum.sh" \
     -i "<input>" -o "<output>"
   ```
   With custom ffmpeg exported:
   ```bash
   FFMPEG="$FFMPEG" bash "${CLAUDE_SKILL_DIR}/scripts/video2forum.sh"\
     -i "<input>" -o "<output>"
   ```

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
