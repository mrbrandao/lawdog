# Lawdog — Developer Guide for AI

This file is auto-loaded at the start of every session. It contains everything
an AI model needs to continue development, fix bugs, or extend lawdog without
losing context between sessions.

**Language rule:** Everything the model reads (CLAUDE.md, protocols/, scripts,
SKILL.md, code) is in English. Only user-facing content (AGENTS.md persona,
user messages in skills, legal knowledge texts) is in Portuguese.

---

## What lawdog is

A plugin for AI assistants (Claude Code, Gemini, Cursor). Helps Brazilians file
cases in the JEC (Juizado Especial Cível — small claims court) without a lawyer.
Lawdog acts as an experienced lawyer with magistrate background — knows CC, CDC,
Lei 9.099/95 and how a judge evaluates a case.

Active development branch: `main` (merged, all v0.4.0 work complete)
Main branch: `main`
Current version: v0.4.0 (Dr. Andre LawDog identity, case lifecycle, importar-caso)

---

## Architecture

```
hooks/              ← plugin hooks (Claude Code, Cursor, Copilot CLI)
    └── session-start   SessionStart: injects Dr. LawDog context, skills table,
                        model selection guidance, active case detection
AGENTS.md           ← persona core (who lawdog is — ~100 lines, constitution)
    │
    ├── protocols/  ← behavioral contracts (how lawdog acts)
    │   ├── case-intake.md         intake flow: narrative→triage→gaps→adversarial→decision
    │   ├── file-structure.md      directory naming (SINGLE SOURCE OF TRUTH)
    │   ├── knowledge-sources.md   mandatory legal lookup order
    │   └── document-standards.md  judicial document quality rules
    │
    ├── knowledge/  ← embedded legal knowledge base
    │   ├── index.md               topic index → article → file
    │   ├── codigo-civil-jec.md    verified articles: CC + CDC + Lei 9.099/95
    │   └── court-portals.md       TJ/PROJUDI by state (PR complete, others pending)
    │
    └── skills/     ← invocable skills (/lawdog:<name>)
        ├── caso/          full case intake + Step 0 state detection + importar-caso redirect
        ├── fetch-law/     fetch updated article: WebFetch → fallback WebSearch
        ├── video2forum/   video → WebM (PROJUDI/TJPR)
        ├── img2pdf/       image → PDF (PEP 723, pillow-heif, quality reduction)
        ├── doc2pdf/       document → PDF via pandoc+pdflatex or LibreOffice
        ├── pdf-split/     PDF > LAWDOG_PDF_SIZE → parts (document PDFs only)
        ├── doc2docx/      markdown → editable DOCX (inline pandoc)
        ├── juntada/       evidence orchestrator (parallel dispatch, batch naming)
        ├── movimentacao/  register court movements (PROJUDI PDF → caso.md update)
        ├── importar-caso/ ingest existing unorganized cases (batch 20, iterative table)
        └── peticao/       draft petition: rascunho → refinement → official PDF via doc2pdf
```

**Principle:** AGENTS.md defines character. Protocols define behavior. Skills
import only the protocols they need — never read AGENTS.md directly.

---

## Running tests

```bash
make test           # run all suites
make test-skills    # validate SKILL.md frontmatter only
make test-setup     # test setup.sh only
make test-python    # run per-skill pytest suites
```

All must pass before any commit.

---

## Conventions

| Aspect | Convention |
|---|---|
| Model-facing content | English (CLAUDE.md, protocols, scripts, SKILL.md) |
| User-facing content | Portuguese (AGENTS.md persona, user messages in skills) |
| File/directory names | kebab-case, no accents, no spaces |
| Case slugs | kebab-case, max 40 chars, no accents |
| Commits | Conventional Commits: `feat:`, `fix:`, `docs:`, `test:` |
| JEC limits | NEVER hardcode — always read from env var `LAWDOG_PDF_SIZE` |

---

## Skill writing standards (agentskills.io)

**Sources:**
- https://agentskills.io/skill-creation/best-practices
- https://agentskills.io/skill-creation/optimizing-descriptions
- https://github.com/anthropics/skills

### What the model loads and when

| Phase | Content | Approximate tokens |
|---|---|---|
| Startup (all skills, always) | `name` + `description` only | ~100 per skill |
| After activation | Full SKILL.md body | < 5,000 recommended |
| On demand | `references/`, `scripts/`, `protocols/` | Agent decides when to read |

Keep SKILL.md under 5,000 tokens. Every token in the body competes with
conversation history after activation.

### Description quality (the only trigger mechanism)

The description is loaded at startup for ALL skills. It is the sole mechanism
that determines when a skill activates. Bad descriptions = wrong activations.

**Hard limit:** 1,024 characters.

**Pattern A — domain-specific skills (simpler):**
```yaml
description: >-
  Does X. Activate on: /lawdog:skill, phrase 1, phrase 2.
```

**Pattern B — complex skills with false-positive risk (TRIGGER/SKIP):**
```yaml
description: >-
  Does X. TRIGGER when: condition1; condition2. SKIP: anti-condition.
```

**Principles:**
- List trigger phrases AND negative cases (what NOT to trigger on)
- Focus on user intent, not internal mechanics
- Be specific: "converts .mov and .mp4 to .webm" beats "converts videos"
- Add "even if they don't explicitly mention X" for indirect triggers

### Inline script vs. dedicated script file

| Use inline | Use `scripts/` directory |
|---|---|
| One-liner commands | Logic > 50 lines |
| Simple, one-time operations | Reusable across multiple runs |
| No edge cases needed | Needs tested error handling |
| | Used by multiple skills |

Scripts must:
- Accept all input via flags (never block on TTY prompts)
- Include `--help` output (primary interface for the agent)
- Write diagnostics to stderr, structured output to stdout
- Support `--dry-run` for destructive operations
- Use distinct exit codes for different failures
- Be invoked via `${CLAUDE_SKILL_DIR}/scripts/<name>` (relative, portable)

### Bash vs Python

**Use Bash when:** orchestrating tools (ffmpeg, git), simple file ops, short loops.

**Use Python when:** libraries needed (PDF, HTML, JSON), complex logic, testability matters.

Python scripts with PEP 723 inline dependencies (run with `uv run`):
```python
# /// script
# dependencies = ["pypdf>=4.3.0"]
# ///
```
Run: `uv run "${CLAUDE_SKILL_DIR}/scripts/pdf_split.py" -i input.pdf -o prefix`
No virtualenv, no global install — `uv` resolves deps on first run.

### allowed-tools — choose narrowly

Only include tools the skill uses on EVERY run. This reduces permission prompts.

```yaml
allowed-tools: Bash                      # shell-only (video2forum, img2pdf)
allowed-tools: WebFetch WebSearch        # network-only (fetch-law)
allowed-tools: Bash Read Write WebFetch  # intake + file creation + law lookup (caso)
```

### Required SKILL.md sections

Every SKILL.md must have:
1. `## Trigger` — when and how to invoke
2. `## Fluxo` — step-by-step flow
3. `## Gotchas` — the one fact the agent would get wrong without explicit instruction

**Gotchas examples:**
- `fetch-law`: "planalto.gov.br resets WebFetch connections — always fall back to WebSearch"
- `caso`: "JEC monetary limits change with minimum wage — never hardcode the BRL value"
- `pdf-split`: "never use on image PDFs — splitting a photo in half is meaningless"

### Skills referencing other skills

Reference by name as a recommended next step, never as an imperative mid-flow call.

```markdown
# Correct — conditional, with reason:
If PDF > LAWDOG_PDF_SIZE: invoke /lawdog:pdf-split -i <output> -o <prefix>

# Wrong — imperative, no context:
Call pdf-split now.
```

---

## How to add a new skill

1. Create `plugin/skills/<name>/SKILL.md`
2. Required frontmatter:
   ```yaml
   ---
   name: <name>             # kebab-case, matches directory name exactly
   description: >-
     <≤1024 chars with activation triggers>
     Activate on: /lawdog:<name>, <phrase 1>, <phrase 2>.
   compatibility: >-
     <dependencies and how to verify them>
   allowed-tools: <only what the skill actually uses>
   metadata:
     author: mrbrandao
     version: "1.0"
   ---
   ```
3. Required sections: `## Trigger`, `## Fluxo`, `## Gotchas`
4. Reference protocols conditionally: "Read X if Y" — not unconditionally
5. Run `make test-skills` — must pass
6. Add to "Skills Disponíveis" in `plugin/AGENTS.md`
7. Update `README.md`

Minimal reference: `plugin/skills/fetch-law/SKILL.md`
Complex reference: `plugin/skills/juntada/SKILL.md`

---

## How to update a protocol

Changes in `plugin/protocols/` affect ALL skills that import the file.

1. Edit the protocol
2. Find all skills that import it (search for the filename)
3. Confirm compatibility or update affected skills
4. No placeholders or TODOs — protocols are source of truth

**`file-structure.md` is critical** — any directory name change must propagate
to all skills that create or read case files.

---

## How to add legal articles to the knowledge base

1. Check `plugin/knowledge/index.md` — already there?
2. If not: add text to `plugin/knowledge/codigo-civil-jec.md`
3. Update the table in `plugin/knowledge/index.md`
4. Include source URL and verification date
5. Long or rare articles → mark as `fetch-law` in index

Never copy an article without verifying at planalto.gov.br. Always include URL and date.

---

## Case file structure

Defined in `plugin/protocols/file-structure.md` — read before any case file operation.
Case lifecycle governed by `plugin/protocols/case-lifecycle.md`.

```
$LAWDOG_CASES_DIR/          # env var, default ~/lawdog-cases
└── <case-slug>/
    ├── caso.md             # living case diary: Partes, Timeline, Estado atual, Movimentações
    ├── 00a-notificacao-extrajudicial/   # optional pre-judicial step
    ├── 00b-contranotificacao-reu/       # optional extrajudicial response
    ├── 01-peticao-inicial/   # NN-tipo/ pattern — mirrors PROJUDI seq numbers
    │   ├── docs/             # editable originals (.md, .docx) — never deleted
    │   ├── anexos/           # staging: user drops evidence here
    │   └── juntada/          # organized, numbered, JEC-ready for upload
    ├── 02-decisao-juiz/      # judge act — docs/ only (no juntada/)
    ├── 03-manifestacao-reu/  # defendant response — docs/ only
    └── 04-peticao/           # subsequent filing — docs/ + anexos/ + juntada/
```

**Movement type reference:** see `protocols/file-structure.md` → "Movement type reference" table.
**00x prefix** = pre-judicial phase. **NN numbers** = judicial phase (mirrors PROJUDI seq).

### Evidence file movement (juntada skill)

Files in `anexos/` are **never deleted**. After processing, the original is tagged:
`foto.jpg` → `foto.jpg.converted`

The script skips `.converted` files on re-run (idempotent).

| Type in `anexos/` | Action | Destination in `juntada/` | Tag in `anexos/` |
|---|---|---|---|
| `.jpg` `.jpeg` `.png` `.heic` | img2pdf → PDF | `NN-name.pdf` | `file.jpg.converted` |
| `.mp4` `.mov` `.avi` `.mkv` | video2forum → WebM | `NN-name.webm` | `file.mp4.converted` |
| `.pdf` | copy | `NN-name.pdf` | `file.pdf.converted` |
| `.webm` | copy | `NN-name.webm` | `file.webm.converted` |
| `.md` `.txt` `.doc` `.docx` | move to `docs/` | — not in juntada | (removed from anexos/) |
| External file (outside `$LAWDOG_CASES_DIR`) | copy only | converted in `juntada/` | original untouched |

**Name conflict resolution:** `file.pdf` → `file-1.pdf` → `file-2.pdf` (kebab-case, no spaces).

---

## System dependencies

| Tool | Used by | Check with |
|---|---|---|
| `ffmpeg` | video2forum | `command -v ffmpeg` |
| `convert` (ImageMagick) | img2pdf (HEIC pre-convert) | `command -v convert` |
| `pandoc` | doc2pdf, doc2docx | `command -v pandoc` |
| `pdflatex` | doc2pdf | `command -v pdflatex` |
| `libreoffice` | doc2pdf (.doc/.docx) | `command -v libreoffice` |
| `uv` | pdf-split (PEP 723) | `command -v uv` |
| `python3` | img2pdf, SKILL.md validator | `command -v python3` |
| `shellcheck` | bash script linting | `command -v shellcheck` |

pandoc 3.1+, LibreOffice 24.8+, pdflatex, ImageMagick, uv 0.10+ all confirmed on this system.

---

## Environment variables

| Variable | Default | Set by | Used by |
|---|---|---|---|
| `LAWDOG_CASES_DIR` | `~/lawdog-cases` | `setup.sh` | all case skills |
| `LAWDOG_PDF_SIZE` | `4194304` (4MB) | `setup.sh` | img2pdf, pdf-split, juntada |

`LAWDOG_PDF_SIZE` is the JEC file size limit in bytes. Change it in ONE place
(setup.sh re-run) and all scripts pick it up automatically via:
```bash
MAX="${LAWDOG_PDF_SIZE:-4194304}"
```
Python: `int(os.environ.get("LAWDOG_PDF_SIZE", 4 * 1024 * 1024))`

---

## Where documentation lives

| File | Content |
|---|---|
| `docs/BACKLOG.md` | **READ FIRST** — future improvements, pending decisions |
| `docs/README.md` | docs/ directory convention |
| `docs/superpowers/specs/` | Approved design specs |
| `docs/superpowers/plans/` | Executed implementation plans |

**Before any development session: read `docs/BACKLOG.md`.**

---

## Known bugs

- **planalto.gov.br + WebFetch**: socket reset. Documented in `fetch-law/SKILL.md` —
  uses WebSearch as automatic fallback. Correct behavior.
- **video2forum slow**: `-cpu-used 0` is slow for long videos. Fix in BACKLOG
  (change to `-cpu-used 5 -threads 4`).

---

## Recommended development workflow

```
1. Read docs/BACKLOG.md and this CLAUDE.md
2. /superpowers:brainstorming for new features
3. Approve spec → /superpowers:writing-plans
4. Execute → /superpowers:subagent-driven-development
5. make test before every commit
6. git push bare main after every commit (safety — never push to upstream/GitHub)
7. Update docs/BACKLOG.md with anything left pending
8. Update this CLAUDE.md if the architecture changed (MANDATORY — see rule below)
```

## Model selection guidance (for sub-agent dispatch)

| Model | Tasks |
|---|---|
| **Haiku** | File ops (img2pdf, video2forum, pdf-split), directory creation, juntada script, import script |
| **Sonnet** | Legal triage, adversarial simulation, evidence analysis, movimentacao interpretation, caso intake |
| **Opus** | Full petition drafting, complex case strategy, deep adversarial simulation, judgment calls |

The session-start hook injects this guidance at every session start.

---

## MANDATORY: Update CLAUDE.md after every feature

**This is a hard rule.** After adding any new skill, protocol, knowledge file,
or significant behavior change:

1. Update the `## Architecture` tree in this file to show the new skill/file
2. Update `## Case file structure` if directory conventions changed
3. Update `## Known bugs` if bugs were fixed or introduced
4. Update the version/branch line at the top

**Why:** CLAUDE.md is the AI's memory across sessions. If it is not updated,
the next session starts without knowing what was built. The specs in
`docs/superpowers/specs/` and plans in `docs/superpowers/plans/` are also
valuable context — reference them in CLAUDE.md when they describe
implemented features.

**Session end checklist:**
- [ ] CLAUDE.md architecture section reflects current skills
- [ ] BACKLOG.md updated with completed items and new pending items
- [ ] `make test` passes
- [ ] Committed and pushed to `bare`
