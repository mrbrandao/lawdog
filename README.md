# lawdog

AI legal assistant plugin for Brazilian court workflows. Dr. Andre LawDog —
advogado e magistrado — helps Brazilians navigate JEC (Juizado Especial Cível)
cases without a lawyer. Evidence preparation, document handling, case lifecycle
management, and judicial ping-pong support.

Works with **Claude Code** and **OpenCode**. Skills are installed once and
available across all your cases.

---

## Install

### System dependencies

| Tool | Required for | Install |
|---|---|---|
| `ffmpeg` | video2forum | https://www.ffmpeg.org/download.html |
| `pandoc` + `pdflatex` | doc2pdf | `dnf install pandoc texlive` |
| `libreoffice` | doc2pdf (.docx) | https://www.libreoffice.org |
| `uv` | pdf-split, img2pdf, importar-caso | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `python3` | img2pdf, validators | system Python 3.10+ |

### 1. First-time setup

Run the bootstrap script to configure `LAWDOG_CASES_DIR` and install Python dependencies:

```bash
bash plugin/scripts/setup.sh
source ~/.bashrc  # or ~/.zshrc
```

### 2. Claude Code

Install via the plugin manager:

```bash
/plugin install https://github.com/mrbrandao/lawdog
```

Skills are available as `/lawdog:<skill-name>`.

> For hooks, WebSearch permissions, and dev-mode loading, see [docs/install.md](docs/install.md#claude-code).

### 3. OpenCode

**Option A — Direct install (no extra tools needed):**

```bash
git clone https://github.com/mrbrandao/lawdog.git ~/lawdog
bash ~/lawdog/plugin/scripts/setup.sh && source ~/.bashrc

# Create opencode.json in your lawdog-cases directory
# Note: must be an absolute path — use realpath to get it
PLUGIN_PATH="$(realpath ~/lawdog/plugin)"
mkdir -p ~/lawdog-cases
echo "{\"$schema\":\"https://opencode.ai/config.json\",\"plugin\":[\"$PLUGIN_PATH\"]}" \
  > ~/lawdog-cases/opencode.json

# Copy the workspace AGENTS.md
cp ~/lawdog/plugin/templates/lawdog-cases.AGENTS.md ~/lawdog-cases/AGENTS.md

cd ~/lawdog-cases && opencode
```

**Option B — Via lola:**

```bash
cd ~/lawdog-cases                           # must run from LAWDOG_CASES_DIR
lola mod add /path/to/lawdog/plugin
lola install lawdog -a opencode             # patches opencode.json + writes AGENTS.md
opencode                                    # restart to load plugin
```

> For step-by-step details, opencode.json reference, and what the plugin provides, see [docs/install.md](docs/install.md#opencode).

### 4. Via lola (Claude Code or OpenCode)

```bash
lola mod add /path/to/lawdog/plugin   # or git URL when published

# Claude Code:
lola install lawdog -a claude-code

# OpenCode (run from inside ~/lawdog-cases):
cd ~/lawdog-cases
lola install lawdog -a opencode
```

> For module source options and full lola reference, see [docs/install.md](docs/install.md#lola).

---

## Skills

| Skill | What it does | Trigger |
|---|---|---|
| `caso` | Open or resume a JEC case — full intake flow | `/lawdog:caso` |
| `movimentacao` | Register a PROJUDI court movement, update caso.md | `/lawdog:movimentacao <slug>` |
| `importar-caso` | Ingest an existing unorganized case into lawdog structure | `/lawdog:importar-caso` |
| `juntada` | Organize evidence from `anexos/` into numbered, JEC-ready `juntada/` | `/lawdog:juntada <slug>` |
| `peticao` | Draft a petition — rascunho → refinement → PDF | `/lawdog:peticao <slug>` |
| `fetch-law` | Fetch updated legal article text from official source | `/lawdog:fetch-law CDC Art. 42` |
| `video2forum` | Convert video evidence to PROJUDI-accepted format | `/lawdog:video2forum *.MOV` |
| `img2pdf` | Convert images (.jpg, .png, .heic) to PDF | `/lawdog:img2pdf` |
| `doc2pdf` | Convert documents (.md, .docx) to PDF | `/lawdog:doc2pdf` |
| `pdf-split` | Split document PDFs exceeding 4 MB into parts | `/lawdog:pdf-split` |
| `doc2docx` | Convert markdown to editable DOCX | `/lawdog:doc2docx` |

> For full skill descriptions and usage examples, see [docs/install.md](docs/install.md#skills-reference).

---

## Case file structure

```
~/lawdog-cases/
└── <case-slug>/
    ├── caso.md                        # Living case diary
    ├── journal.md                     # Narrative/strategy log (append-only)
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
