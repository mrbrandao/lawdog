# lawdog

AI legal assistant plugin for Brazilian court workflows. Dr. Andre LawDog —
advogado e magistrado — helps Brazilians navigate JEC (Juizado Especial Cível)
cases without a lawyer. Evidence preparation, document handling, case lifecycle
management, and judicial ping-pong support.

## Install

### 1. First-time setup

Run the bootstrap script to configure `LAWDOG_CASES_DIR` and install Python dependencies:

```bash
bash plugin/scripts/setup.sh
source ~/.bashrc  # or ~/.zshrc
```

### 2. Claude Code (plugin)

Install via the plugin manager:

```bash
/plugin install https://github.com/mrbrandao/lawdog
```

Or load directly for development:

```bash
claude --plugin-dir ./plugin
```

Skills are namespaced as `/lawdog:<skill-name>`.

#### Hooks (session-start context injection)

> **Note:** Lola does not yet support automatic hook installation (see [issue #176](https://github.com/LobsterTrap/lola/issues/176)).
> Set up hooks manually after installing the plugin.

The session-start hook injects Dr. LawDog's context, skill table, and model
selection guidance at the beginning of every Claude Code session. To enable it:

```bash
# Copy hooks to Claude Code's plugin hooks directory
PLUGIN_DIR="${CLAUDE_PLUGINS_DIR:-$HOME/.claude/plugins}/lawdog"
mkdir -p "$PLUGIN_DIR/hooks"
cp plugin/hooks/hooks.json "$PLUGIN_DIR/hooks/"
cp plugin/hooks/session-start "$PLUGIN_DIR/hooks/"
chmod +x "$PLUGIN_DIR/hooks/session-start"
```

Or if you installed via `/plugin install`, find the installed plugin path:

```bash
ls ~/.claude/plugins/
# Then copy hooks into the lawdog plugin directory there
```

#### WebSearch permissions (skip prompts)

The plugin ships a `.claude/settings.json` that pre-approves WebSearch and
legal domain WebFetch so you are not interrupted with permission prompts:

```bash
# Run the permission installer manually if needed
LOLA_ASSISTANT=claude-code LOLA_PROJECT_PATH="$PWD" bash plugin/scripts/install-permissions.sh
```

### 3. Lola (AI Context Module)

```bash
lola mod add ./lawdog --module-content plugin
lola install lawdog
```

> Lola installs skills automatically. Hooks and permissions require manual setup (see above).

### 4. System dependencies

| Tool | Required for | Install |
|---|---|---|
| `ffmpeg` | video2forum | https://www.ffmpeg.org/download.html |
| `pandoc` + `pdflatex` | doc2pdf | `dnf install pandoc texlive` |
| `libreoffice` | doc2pdf (.docx) | https://www.libreoffice.org |
| `uv` | pdf-split, importar-caso | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `python3` | img2pdf, validators | system Python 3.10+ |

---

## Skills

### `caso` — Case management

Opens a new case or resumes an existing one. Conducts intake (narrative → triage →
adversarial simulation), creates the case directory structure, and guides the user
through the full JEC lifecycle.

```
/lawdog:caso
```

### `movimentacao` — Register court movement

Registers a new PROJUDI movement (judge decision, defendant response, intimação),
reads the PDF, interprets it legally, updates `caso.md`, and orients next steps.

```
/lawdog:movimentacao obra-irregular
```

### `importar-caso` — Ingest existing case

Organizes an existing unstructured case into lawdog format. Analyzes files in
batches of 20, proposes classification table, user validates, then applies structure.

```
/lawdog:importar-caso
```

### `juntada` — Organize evidence

Organizes evidence from `anexos/` into a numbered, JEC-ready `juntada/`.
Batch naming in one table interaction, parallel conversions, enforces 4MB limit.

```
/lawdog:juntada obra-irregular
/lawdog:juntada obra-irregular peticao-02
```

### `fetch-law` — Fetch legal article

Fetches updated legal text from planalto.gov.br or relevant TJ.

```
/lawdog:fetch-law Lei 9.099/95 Art. 3
/lawdog:fetch-law CDC Art. 42
```

### `video2forum` — Convert video for PROJUDI

Converts video evidence to WebM format accepted by PROJUDI/TJPR.

```
/lawdog:video2forum ~/docs/case/*.MOV
```

### Conversion skills

| Skill | Input → Output | Notes |
|---|---|---|
| `img2pdf` | `.jpg` `.png` `.heic` → `.pdf` | Quality reduction if > `LAWDOG_PDF_SIZE` (4MB) |
| `doc2pdf` | `.md` `.txt` `.doc` `.docx` → `.pdf` | pandoc + pdflatex + `base-legal.latex` |
| `pdf-split` | `.pdf` >4MB → parts | Document PDFs only |
| `doc2docx` | `.md` `.txt` → `.docx` | Editable version via pandoc |

---

## Case file structure

```
~/lawdog-cases/
└── <case-slug>/
    ├── caso.md                        # Living case diary
    ├── 00a-notificacao-extrajudicial/ # Optional pre-judicial step
    ├── 01-peticao-inicial/
    │   ├── docs/      # Editable originals (.md, .docx)
    │   ├── anexos/    # Drop evidence here
    │   └── juntada/   # JEC-ready, numbered, for PROJUDI upload
    ├── 09-decisao-juiz/               # NN = PROJUDI sequence number
    ├── 12-peticao/
    └── 20-manifestacao-reu/
```

---

## License

MIT
