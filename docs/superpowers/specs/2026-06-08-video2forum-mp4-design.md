# video2forum v1.2 — MP4 as Default Format Design

**Date:** 2026-06-08
**Status:** approved
**Scope:** Update `video2forum` skill and script to use MP4/H.264+AAC as the
default output format, with intelligent probe-based passthrough and WebM as
explicit fallback when the forum rejects MP4.

---

## 1. Context

A MP4 file was successfully uploaded to PROJUDI/TJPR (case 0014101-52.2026.8.16.0182)
with better quality than the WebM conversions previously used. ffprobe analysis of
the accepted file reveals its exact specs:

```
Container: MP4 (ISO Media / QuickTime)
Video:     H.264, High Profile, Level 3.0, yuv420p, 30fps, ~1.3Mbps
Audio:     AAC, 48kHz, stereo, 128kbps
Total:     ~1.4Mbps bitrate, 4.2MB for 24s
```

The WebM conversion (VP8 + Vorbis) was causing unnecessary quality loss and slow
encoding. MP4/H.264+AAC is now the proven, preferred format.

---

## 2. Three-mode operation

```
INPUT
  │
  ▼ ffprobe check
  ├─ MP4 with H.264 + AAC? → PASSTHROUGH (copy, zero re-encode)
  ├─ Other format?         → CONVERT to MP4/H.264+AAC (reference specs)
  └─ --webm flag?          → CONVERT to WebM/VP8+Vorbis (legacy fallback)
```

**Passthrough condition:** input is MP4 container AND video codec is h264 AND
audio codec is aac. Both conditions must be true. If either fails, re-encode.

---

## 3. Conversion specs (matching reference file)

```bash
ffmpeg -v quiet -stats \
  -i "$INPUT" \
  -c:v libx264 -profile:v high -level:v 3.0 -pix_fmt yuv420p \
  -crf 23 -threads 4 \
  -c:a aac -b:a 128k -ar 48000 \
  -movflags +faststart \
  -y "$OUTPUT"
```

Key flags:
- `-crf 23` — quality-based encoding (adapts to content complexity, ~1-2Mbps typical)
- `-movflags +faststart` — moves MP4 index to file start for browser streaming
- `-threads 4` — parallel encoding
- `-v quiet -stats` — suppress verbose output, show only final stats

WebM fallback (existing behavior, kept for compatibility):
```bash
ffmpeg -v quiet -stats \
  -i "$INPUT" \
  -c:v libvpx -quality good -cpu-used 5 -threads 4 -b:v 500k \
  -c:a libvorbis -q:a 4 \
  -y "$OUTPUT"
```

---

## 4. Script interface

**Flags:**
- `-i <input>` — input video file (required)
- `-o <output>` — output file path (required; extension determines format)
- `--webm` — force WebM output regardless of input format

**Output filename convention:**
- Default: same basename, extension `.mp4`
- WebM fallback: same basename, extension `.webm`

**Exit codes:**
- 0: success
- 1: input not found or ffmpeg error
- 2: ffprobe not available (degrades gracefully: skips probe, always converts)

---

## 5. SKILL.md changes

**Description update:** replace "WebM format required by Brazilian court systems"
with "MP4/H.264+AAC (preferred) or WebM (fallback) for PROJUDI/TJPR upload."

**Trigger phrases:** add "converter para mp4", "video para tribunal" alongside
existing WebM-specific phrases.

**Format spec section:** document the reference file specs, the probe logic,
and the --webm fallback trigger.

**Fallback guidance in Fluxo:**

After conversion to MP4, instruct user to attempt PROJUDI upload.
If user returns saying the MP4 was rejected by the forum, respond with:
> "O PROJUDI não aceitou o MP4? Vou converter para WebM (formato legado).
> Use: `/lawdog:video2forum --webm <arquivo>` — ou me diga que não aceitou
> e faço o fallback agora."

**Version:** bump to `1.2`

---

## 6. Plugin versioning rule (for CLAUDE.md)

Any change to `video2forum` that alters the default output format requires:
1. Bump `plugin/.claude-plugin/plugin.json` version
2. Bump `plugin/.claude-plugin/marketplace.json` version
3. User must reinstall: `/plugin uninstall lawdog` → `/plugin install <path>`

This rule applies to any skill change that affects output format, file naming
conventions, or behavior observable to the user.

---

## 7. Files to modify

| File | Change |
|---|---|
| `plugin/skills/video2forum/scripts/video2forum.sh` | Add probe logic, MP4 as default, --webm flag |
| `plugin/skills/video2forum/SKILL.md` | Update description, format spec, fallback guidance, version 1.2 |
| `plugin/.claude-plugin/plugin.json` | Version bump |
| `plugin/.claude-plugin/marketplace.json` | Version bump |
| `CLAUDE.md` | Add plugin versioning rule |

---

## 8. Design decisions

| Decision | Choice | Reason |
|---|---|---|
| Default format | MP4/H.264+AAC | Proven accepted by PROJUDI, better quality, faster encode |
| Probe strategy | ffprobe on input | Avoids unnecessary re-encode for files already in correct format |
| Passthrough condition | H.264 + AAC both required | Either wrong codec = re-encode to ensure compatibility |
| CRF vs fixed bitrate | CRF 23 | Adapts to content; reference file was ~1.3Mbps which CRF 23 targets naturally |
| +faststart | Always | MP4 index at start = PROJUDI browser player can stream without full download |
| WebM fallback | --webm flag + conversational trigger | User knows from forum rejection; skill responds to "não aceitou" |
| ffprobe unavailable | Degrade gracefully (always convert) | Robustness over elegance |
