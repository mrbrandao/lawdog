# audio2text Design Spec

**Date:** 2026-07-08
**Status:** approved
**Scope:** `/lawdog:audio2text` skill — transcribes audio and video files using
faster-whisper (local, PT-BR optimized), saves transcript to `docs/`, and
analyzes the content as legal evidence. Integrated into `/lawdog:juntada` with
user confirmation before transcription. DRY ffmpeg path via `setup.sh` exports.

---

## 1. Context

Lawdog users submit audio (WhatsApp messages, phone recordings) and video
(witness testimony, site inspections) as evidence in JEC cases. Without
transcription, the AI cannot read the content — it can only organize the files.
With transcription, Dr. LawDog can identify admissions, quote specific statements
in petitions, and evaluate the legal weight of verbal evidence.

---

## 2. Architecture

```
/lawdog:audio2text <file-or-slug>
    │
    └── scripts/audio2text.py  (PEP 723: faster-whisper)
        ├── VIDEO input → ffmpeg extracts audio → faster-whisper transcribes
        └── AUDIO input → faster-whisper transcribes directly
        └── output: docs/transcricao-<name>.md + legal analysis by Dr. LawDog

/lawdog:juntada (updated)
    └── Step 2 table: audio/video rows include 🎙️ "Transcrever?" column
        └── user confirms which → dispatches audio2text as background subagent
```

**No daemon.** `audio2text.py` is invoked on-demand per file. Model is cached
on disk after first download (~244MB for `small`).

---

## 3. DRY: ffmpeg path via setup.sh

`setup.sh` is updated to detect and export ffmpeg and ffprobe paths at install
time. All scripts read these env vars — no detection logic in individual scripts.

**New exports added to setup.sh (written to shell profile):**

```bash
export FFMPEG=/path/to/ffmpeg       # auto-detected: ~/bin/ffmpeg > which ffmpeg
export FFPROBE=/path/to/ffprobe     # auto-detected: ~/bin/ffprobe > which ffprobe
export LAWDOG_WHISPER_MODEL=small   # faster-whisper model size
```

**Detection logic in setup.sh:**
```bash
detect_ffmpeg() {
    if [ -x "$HOME/bin/ffmpeg" ]; then
        echo "$HOME/bin/ffmpeg"
    elif command -v ffmpeg >/dev/null 2>&1; then
        command -v ffmpeg
    else
        echo ""
    fi
}
```

`video2forum.sh` already reads `$FFMPEG` — zero change needed.
`audio2text.py` reads `os.environ.get('FFMPEG', 'ffmpeg')` — same convention.

---

## 4. audio2text.py — script spec

**PEP 723 dependencies:**
```python
# /// script
# dependencies = ["faster-whisper>=1.0.0"]
# ///
```

**Usage:**
```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/audio2text.py" \
    -i <input-file> \
    -o <output-transcript.md> \
    [--model small] \
    [--lang pt]
```

**Flags:**
- `-i` / `--input` — audio or video file (required)
- `-o` / `--output` — output markdown path (required)
- `--model` — whisper model size, default: `$LAWDOG_WHISPER_MODEL` or `small`
- `--lang` — language hint, default: `pt` (Brazilian Portuguese)

**Logic:**
1. Detect file type: if video (mp4, mov, avi, mkv, webm) → extract audio with ffmpeg first
2. Run faster-whisper transcription with timestamps
3. Write transcript to output `.md` file (see format below)
4. Print summary to stderr (no frame-by-frame output)
5. Print `Done: <output>` on success

**ffmpeg audio extraction (for video inputs):**
```python
import subprocess, os
ffmpeg = os.environ.get('FFMPEG', 'ffmpeg')
subprocess.run([ffmpeg, '-nostdin', '-loglevel', 'error',
    '-i', input_file, '-vn', '-ar', '16000', '-ac', '1',
    '-y', audio_tmp], check=True)
```

**Exit codes:**
- 0: success
- 1: input file not found
- 2: ffmpeg error (audio extraction failed)
- 3: faster-whisper error (transcription failed)

---

## 5. Transcript output format

File: `docs/transcricao-<filename>.md` (in the current petition's docs/ dir)

```markdown
# Transcrição: video-devassa-visual.mp4

**Arquivo:** video-devassa-visual.mp4
**Duração:** 2m34s
**Idioma detectado:** pt (confiança: 98%)
**Modelo:** faster-whisper small
**Data:** YYYY-MM-DD

---

## Texto

[00:00] "Olha aqui a janela que dá diretamente para o meu banheiro..."
[00:15] "Pode ver que dá pra enxergar tudo, não tem privacidade nenhuma..."
[01:02] "Eu coloquei essa estrutura aqui antes de comprar o imóvel."

---

## Análise Jurídica

*(Preenchida por Dr. LawDog após a transcrição)*

**Relevância para o caso:** [Alta/Média/Baixa] — [descrição]

**Pontos chave:**
- [00:15] Admissão de visibilidade direta — citável na petição
- [01:02] Afirmação temporal relevante (pré-existência da obra)

**Artigos aplicáveis:** [verificados via knowledge/ ou fetch-law]
```

The "Análise Jurídica" section is written by Dr. LawDog **after** the script
runs — the script writes only the metadata and transcript. Dr. LawDog then reads
the file and appends the legal analysis section.

---

## 6. juntada integration

In `/lawdog:juntada` Step 2 (batch analysis table), audio and video rows gain
a transcription column:

```
| # | Arquivo                | Tipo   | Ação            | 🎙️ Transcrever? |
|---|------------------------|--------|-----------------|-----------------|
| 3 | video-devassa.mp4      | Vídeo  | passthrough     | ☐ (marcar)      |
| 4 | audio-sindico.m4a      | Áudio  | copy to juntada | ☐ (marcar)      |
```

After table confirmation (Phase 3), if any files are marked for transcription:
- Dispatch one background subagent per file calling `/lawdog:audio2text`
- Continue conversation with user while transcription runs in background
- Subagent reports completion; transcript appears in `docs/`
- Dr. LawDog then reads transcript and appends legal analysis

**If NO files are marked:** skip transcription entirely — no change to existing flow.

---

## 7. SKILL.md

**Trigger phrases:** `/lawdog:audio2text`, "transcrever vídeo", "transcrever áudio",
"o que está sendo dito nesse vídeo", "extrair texto do áudio", "ler o vídeo",
"analisar o que foi dito"

**TRIGGER/SKIP:** TRIGGER when user submits audio/video and wants content
extracted. SKIP for video format conversion (use `/lawdog:video2forum`) or
evidence organization (use `/lawdog:juntada`).

**allowed-tools:** `Bash Read Write`

---

## 8. Files to create/modify

| Action | File | Change |
|---|---|---|
| Create | `plugin/skills/audio2text/SKILL.md` | New skill |
| Create | `plugin/skills/audio2text/scripts/audio2text.py` | PEP 723 script |
| Create | `plugin/skills/audio2text/tests/test_audio2text.py` | pytest behavioral tests |
| Modify | `plugin/scripts/setup.sh` | Export FFMPEG, FFPROBE, LAWDOG_WHISPER_MODEL |
| Modify | `plugin/skills/juntada/SKILL.md` | Add 🎙️ transcription column to Step 2 table |
| Modify | `plugin/AGENTS.md` | Add audio2text to Skills Disponíveis |
| Modify | `plugin/hooks/session-start` | Add audio2text to skills table + MANDATORY_RULE |
| Modify | `CLAUDE.md` | Add audio2text to architecture skills list |

---

## 9. Design decisions

| Decision | Choice | Reason |
|---|---|---|
| Engine | faster-whisper via PEP 723 | Zero install, good PT-BR, no API key, on-demand |
| Default model | `small` (244MB) | Best accuracy/speed balance for PT-BR on CPU |
| Model var | `LAWDOG_WHISPER_MODEL` | Env var follows existing pattern (LAWDOG_PDF_SIZE) |
| ffmpeg DRY | Export from setup.sh | Single source; video2forum already reads $FFMPEG |
| Output format | Markdown with timestamps | Quotable in petitions; readable by Dr. LawDog |
| Legal analysis | Written by Dr. LawDog after script | Script does one thing (transcription); AI does analysis |
| juntada integration | Confirmation table + background subagent | User controls; no token waste during long transcriptions |
| Language hint | `pt` default | Whisper auto-detects but hint improves PT-BR accuracy |
