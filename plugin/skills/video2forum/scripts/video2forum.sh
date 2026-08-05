#!/usr/bin/env bash
# Converts any video to WebM (VP8+Vorbis) compatible with PROJUDI/TJPR court system
# Usage: ./video-para-forum.sh -i input.MOV -o output.webm
# Custom ffmpeg path: FFMPEG=/path/to/ffmpeg ./video-para-forum.sh ...

if [ -z "$FFMPEG" ]; then
    FFMPEG="$(which ffmpeg 2>/dev/null)"
fi

if [ -z "$FFMPEG" ] || [ ! -x "$FFMPEG" ]; then
    printf "Error: ffmpeg not found.\n\
Please install ffmpeg or download a static build:\n\
  Official builds:      https://www.ffmpeg.org/download.html\n\
  Static Linux builds:  https://johnvansickle.com/ffmpeg/\n\
\n\
Then provide the path with: FFMPEG=/path/to/ffmpeg %s ...\n" "$0"
    exit 1
fi

usage() {
    printf "Usage: %s -i <input_file> -o <output_file.webm>\n" "$0"
    exit 1
}

while getopts "i:o:" opt; do
    case $opt in
        i) INPUT="$OPTARG" ;;
        o) OUTPUT="$OPTARG" ;;
        *) usage ;;
    esac
done

[ -z "$INPUT" ] || [ -z "$OUTPUT" ] && usage

if [ ! -f "$INPUT" ]; then
    printf "Error: input file not found: %s\n" "$INPUT"
    exit 1
fi

"$FFMPEG" -i "$INPUT" \
    -c:v libvpx -quality good -cpu-used 0 -b:v 500k \
    -c:a libvorbis -q:a 4 \
    -y "$OUTPUT"

printf "Done: %s\n" "$OUTPUT"
