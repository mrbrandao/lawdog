#!/usr/bin/env bash
# Converts video files for PROJUDI/TJPR forum upload.
# Default output: MP4/H.264+AAC (proven PROJUDI-compatible, better quality).
# Passthrough: if input is already H.264+AAC MP4, copies without re-encoding.
# Fallback: WebM/VP8+Vorbis with --webm flag when forum rejects MP4.
#
# Usage: video2forum.sh -i <input> -o <output.mp4|.webm> [--webm]
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
