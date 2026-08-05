# lawdog

AI legal assistant plugin for Brazilian court workflows. Provides skills and tools for individuals navigating civil proceedings — evidence preparation, document handling, and procedural guidance.

## Install

### Claude Code (plugin)

```bash
claude --plugin-dir ./lawdog/plugin
```

Or install permanently via the plugin manager:

```bash
/plugin install https://github.com/mrbrandao/lawdog
```

Skills are namespaced as `/lawdog:<skill-name>`.

### Lola (AI Context Module)

```bash
lola mod add ./lawdog --module-content plugin
lola install lawdog
```

### OpenClaw

Skills are installed automatically by lola into `~/.openclaw/workspace/skills/`.

## Skills

### `caso`

Opens and manages a JEC case. Conducts the full intake flow (free narrative →
triage → gap filling → adversarial simulation), creates the case directory
structure, and generates `caso.md` with the initial case summary.

```
/lawdog:caso
```

**Requires:** `LAWDOG_CASES_DIR` set. Run `bash plugin/scripts/setup.sh` on first install.

---

### `fetch-law`

Fetches the current official text of a legal article from planalto.gov.br or
the relevant TJ. Used internally by other skills; can also be invoked directly.

```
/lawdog:fetch-law Lei 9.099/95 Art. 3
/lawdog:fetch-law CDC Art. 42
/lawdog:fetch-law Código Civil Art. 927
```

---

### `video2forum`

Converts video evidence (.MOV, .MP4, .AVI, .MKV, etc.) to WebM — the format
accepted by PROJUDI/TJPR for evidence uploads.

```
/lawdog:video2forum ~/docs/case/*.MOV
```

**Requirements:** `ffmpeg` in PATH, or set `FFMPEG=/path/to/ffmpeg`.

---

### `juntada`

Organizes evidence from `anexos/` into a numbered, JEC-ready `juntada/`.
Analyzes content, proposes batch naming in one interaction, dispatches
parallel sub-agent conversions, and enforces `LAWDOG_PDF_SIZE`.

```
/lawdog:juntada obra-irregular
/lawdog:juntada obra-irregular peticao-02
```

---

### Conversion skills

| Skill | Input → Output | Notes |
|---|---|---|
| `img2pdf` | `.jpg` `.png` `.heic` → `.pdf` | Quality reduction if > `LAWDOG_PDF_SIZE` |
| `doc2pdf` | `.md` `.txt` `.doc` `.docx` → `.pdf` | pandoc + pdflatex + `base-legal.latex` |
| `pdf-split` | `.pdf` >4MB → parts | Document PDFs only — not for images |
| `doc2docx` | `.md` `.txt` → `.docx` | Inline pandoc — no script file needed |

## Plugin structure

```
lawdog/
├── plugin/
│   ├── .claude-plugin/
│   │   └── plugin.json             # Claude Code plugin manifest
│   ├── AGENTS.md                   # Lawdog persona core
│   ├── protocols/
│   │   ├── case-intake.md          # Intake flow contract
│   │   ├── file-structure.md       # Directory naming (single source of truth)
│   │   └── knowledge-sources.md    # Legal lookup order contract
│   ├── knowledge/
│   │   ├── index.md                # Legal topic index
│   │   ├── codigo-civil-jec.md     # Verified articles (CC + CDC + Lei 9.099/95)
│   │   └── court-portals.md        # TJ/PROJUDI by state + navigation
│   ├── skills/
│   │   ├── caso/
│   │   │   └── SKILL.md
│   │   ├── fetch-law/
│   │   │   └── SKILL.md
│   │   └── video2forum/
│   │       ├── SKILL.md
│   │       └── scripts/
│   │           └── video2forum.sh
│   └── scripts/
│       └── setup.sh                # Bootstrap: LAWDOG_CASES_DIR + deps
├── tests/
│   ├── validate_skill.py           # SKILL.md structure validator
│   └── test_setup.sh               # setup.sh behavior tests
├── Makefile                        # make test entry point
└── README.md
```

## License

MIT
