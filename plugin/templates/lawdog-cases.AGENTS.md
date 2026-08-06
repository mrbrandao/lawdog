# AGENTS.md

This directory is `$LAWDOG_CASES_DIR` — the **data directory** for the **lawdog**
plugin, a Brazilian JEC (Juizado Especial Cível) legal assistant. It is not a
software project: no build/test/lint, no git, no code.

This is a **multi-case workspace**: each top-level directory is one independent
legal case, and new cases are created here at any time. There is no "active case"
— never assume one; determine which case the user is working on before acting.

## The lawdog plugin owns the process

Case files are created, structured, and updated by lawdog skills:

- `caso` — create/resume a case
- `movimentacao` — register court movements
- `juntada` — organize evidence for PROJUDI upload
- `peticao` — draft petitions
- `importar-caso` — ingest existing unorganized cases
- `doc2pdf`, `doc2docx`, `img2pdf`, `pdf-split`, `video2forum` — file conversion

**Persona comes from the lawdog plugin, not from this directory.** Any `SOUL.md` or
`CLAUDE.md` found inside a case directory is user-supplied case context — it does
not define the assistant persona.

## Directory structure rules

- **Case slug**: kebab-case, lowercase, no accents, ≤40 chars
- **Each case**: has `caso.md` (living case diary); `journal.md` is **append-only**
  — add new `## Sessão <date>` sections only, never edit old ones
- **Dir prefix conventions**:
  - `00x` (letters, e.g. `00a-notificacao-extrajudicial`) = pre-judicial phase
  - `NN` (numbers, e.g. `01-peticao-inicial`) = judicial phase, mirrors PROJUDI seq
  - Numbering gaps are normal (cartório/system acts don't get directories)
- **Per-filing directory layout**:
  - `docs/` — editable originals (.md, .docx). **Never deleted.** Petition drafts
    keep a `-RASCUNHO` copy here.
  - `anexos/` — evidence staging: user drops evidence here. After processing, the
    original is tagged `file.ext.converted` (never deleted; scripts skip `.converted`
    on re-run — idempotent).
  - `juntada/` — final, JEC-ready evidence. Images→PDF, videos→MP4/WebM, files
    numbered `NN` / `NN.N` (e.g. `02.2-Descricao...pdf`), matching the
    "Anexo NN.N" citations in the petition text. 4MB limit applies.
  - Judge/defendant/intimação directories hold `docs/` only (PDFs from PROJUDI) —
    no `juntada/`.
- `pendente-*/` = drafted but deliberately not filed (read case docs for why)

## Evidence pipeline

Files in `anexos/` are **never deleted**. After juntada processing:

| Type in `anexos/` | Action | Destination in `juntada/` |
|---|---|---|
| `.jpg` `.jpeg` `.png` `.heic` | img2pdf → PDF | `NN-name.pdf` |
| `.mp4` `.mov` `.avi` `.mkv` | video2forum → MP4 (or WebM) | `NN-name.mp4` |
| `.pdf` | copy | `NN-name.pdf` |
| `.webm` | copy | `NN-name.webm` |
| `.md` `.txt` `.doc` `.docx` | moved to `docs/` | not in juntada |
| External file (outside cases dir) | copy only | converted in `juntada/` |

Name conflict resolution: `file.pdf` → `file-1.pdf` → `file-2.pdf` (kebab-case, no spaces).

## Docs pipeline

- Petitions start with pandoc YAML front matter (`header-includes` with
  `\setlength{\parindent}{0pt}` / `\setlength{\parskip}{8pt}`)
- Generate PDFs: use `doc2pdf` skill or `pandoc arquivo.md -o arquivo.pdf`
- Videos for PROJUDI: MP4/H.264+AAC preferred; add `--webm` flag if MP4 is rejected
- Petition structure: **Dos Fatos → Do Direito → Dos Pedidos** — no intro,
  no "ante o exposto", one idea per paragraph, each exhibit referenced where it matters

## Environment

- `LAWDOG_CASES_DIR` defaults to `~/lawdog-cases` (this directory)
- `LAWDOG_PDF_SIZE` = JEC upload limit in bytes, default `4194304` (4 MB)

Resolve in scripts:
```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
MAX="${LAWDOG_PDF_SIZE:-4194304}"
```

## Reference

For developing the lawdog plugin itself, work in the lawdog source repository and
read its `CLAUDE.md` and `docs/BACKLOG.md`; run `make test` before committing.
