# Lawdog — Installation & Reference Guide

Complete reference for installing and configuring lawdog across Claude Code,
OpenCode, and lola. For a quick start, see the [README](../README.md).

---

## System dependencies

| Tool | Required for | How to install |
|---|---|---|
| `ffmpeg` | `video2forum` | https://www.ffmpeg.org/download.html — or `dnf/apt install ffmpeg` |
| `pandoc` | `doc2pdf`, `doc2docx` | `dnf install pandoc` / `apt install pandoc` |
| `pdflatex` | `doc2pdf` | `dnf install texlive` — requires `texlive-collection-fontsrecommended` for Charter font |
| `libreoffice` | `doc2pdf` (.doc/.docx input) | https://www.libreoffice.org |
| `uv` | `pdf-split`, `img2pdf`, `importar-caso` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `python3` | `img2pdf`, test suite | System Python 3.10+ |

> **Font note:** `doc2pdf` uses the Charter font (`\usepackage{charter}`). On minimal TeX
> installs this requires `texlive-collection-fontsrecommended`:
> ```bash
> sudo dnf install texlive-collection-fontsrecommended   # Fedora
> sudo apt install texlive-fonts-recommended              # Debian/Ubuntu
> ```
> Without it, `pdflatex` fails with `cannot open encoding file 8r.enc`.

---

## First-time setup

Run the bootstrap script once per machine:

```bash
bash plugin/scripts/setup.sh
source ~/.bashrc  # or ~/.zshrc
```

The script:
1. Prompts for your `LAWDOG_CASES_DIR` (default: `~/lawdog-cases`) and exports it to your shell profile
2. Sets `LAWDOG_PDF_SIZE=4194304` (4 MB JEC upload limit) in your shell profile
3. Installs Python dependencies (`img2pdf`, `pillow-heif`, `Pillow`, `pypdf`) via `uv` or `pip3`
4. Checks for `ffmpeg` and warns if missing

Environment variables set by setup:

| Variable | Default | Purpose |
|---|---|---|
| `LAWDOG_CASES_DIR` | `~/lawdog-cases` | Root directory for all case files |
| `LAWDOG_PDF_SIZE` | `4194304` | JEC upload limit in bytes (4 MB) |

---

## Claude Code

### Plugin install

Install from the Claude Code plugin manager:

```bash
/plugin install https://github.com/mrbrandao/lawdog
```

Skills are namespaced as `/lawdog:<skill-name>` and discovered automatically.

For development or local testing, load the plugin directly:

```bash
claude --plugin-dir ./plugin
```

### Session-start hook

The session-start hook injects Dr. LawDog's context, skill table, model
selection guidance, and active case status at the beginning of every Claude
Code session.

> **Note:** Lola does not yet support automatic hook installation
> (see [issue #176](https://github.com/LobsterTrap/lola/issues/176)).
> Set up hooks manually after installing the plugin.

```bash
# Find the installed plugin directory
PLUGIN_DIR="${CLAUDE_PLUGINS_DIR:-$HOME/.claude/plugins}/lawdog"
mkdir -p "$PLUGIN_DIR/hooks"

# Copy the hook files
cp plugin/hooks/hooks.json "$PLUGIN_DIR/hooks/"
cp plugin/hooks/session-start "$PLUGIN_DIR/hooks/"
chmod +x "$PLUGIN_DIR/hooks/session-start"
```

If you installed via `/plugin install`, find the installed path first:

```bash
ls ~/.claude/plugins/
# Then copy hooks into the lawdog directory shown there
```

### WebSearch permissions

The plugin pre-approves WebSearch and legal domain WebFetch calls so Claude
Code does not prompt for permission on every lookup:

```bash
# Run manually if the plugin manager did not run it automatically
LOLA_ASSISTANT=claude-code LOLA_PROJECT_PATH="$PWD" \
  bash plugin/scripts/install-permissions.sh
```

This writes `.claude/settings.json` with `allow` entries for `WebSearch` and
`WebFetch` on `planalto.gov.br`, `tjpr.jus.br`, `projudi.tjpr.jus.br`,
`legis.senado.leg.br`, and `www2.camara.leg.br`.

### Via lola

```bash
lola mod add /path/to/lawdog/plugin
lola install lawdog -a claude-code
```

Lola installs skills to `.claude/skills/` and injects the Dr. LawDog persona
into `CLAUDE.md`. Run the hooks and permissions setup manually afterward
(see above).

---

## OpenCode

OpenCode uses a native npm-style plugin system. The lawdog plugin registers
via two hooks:

- **`config` hook** — adds `plugin/skills/` to OpenCode's skill discovery paths
- **`experimental.chat.messages.transform` hook** — injects Dr. LawDog context
  (persona, active cases, skill table, model guidance) into the first user
  message of every new conversation

This replaces the Claude Code `session-start` hook entirely for OpenCode sessions.

### What `LAWDOG_PLUGIN_DIR` does

The plugin sets `process.env.LAWDOG_PLUGIN_DIR` at load time to the absolute
path of the `plugin/` directory. Skills that run scripts use this as a fallback
when `CLAUDE_SKILL_DIR` (a Claude Code env var) is not set:

```bash
# Pattern in SKILL.md bash code blocks:
LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/juntada}"
uv run "${LAWDOG_SKILL}/scripts/juntada.py" ...
```

This means all script-based skills (`juntada`, `img2pdf`, `doc2pdf`,
`video2forum`, `pdf-split`) work identically in both Claude Code and OpenCode.

### Direct install (no lola)

**Step 1 — Clone the repository:**

```bash
git clone https://github.com/mrbrandao/lawdog.git ~/lawdog
```

**Step 2 — Run first-time setup:**

```bash
bash ~/lawdog/plugin/scripts/setup.sh
source ~/.bashrc  # or ~/.zshrc
```

**Step 3 — Get the absolute plugin path:**

The `"plugin"` key in `opencode.json` requires an **absolute path**. Tilde
(`~/`) is not reliably expanded by OpenCode's plugin loader.

```bash
realpath ~/lawdog/plugin
# Example output: /home/<user>/lawdog/plugin
```

**Step 4 — Create `opencode.json` in your `lawdog-cases` directory:**

```bash
mkdir -p ~/lawdog-cases
```

`~/lawdog-cases/opencode.json`:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["/absolute/path/to/lawdog/plugin"]
}
```

Replace `/absolute/path/to/lawdog/plugin` with the output of `realpath` from Step 3.

One-liner that fills the path automatically:

```bash
PLUGIN_PATH="$(realpath ~/lawdog/plugin)"
echo "{\"$schema\":\"https://opencode.ai/config.json\",\"plugin\":[\"$PLUGIN_PATH\"]}" \
  > ~/lawdog-cases/opencode.json
```

**Step 5 — Copy the workspace AGENTS.md:**

```bash
cp ~/lawdog/plugin/templates/lawdog-cases.AGENTS.md ~/lawdog-cases/AGENTS.md
```

This file teaches OpenCode (and Claude Code when started from `~/lawdog-cases`)
the lawdog directory rules, evidence pipeline, and available skills. It contains
no hardcoded paths and works on any machine.

**Step 6 — Start OpenCode:**

```bash
cd ~/lawdog-cases
opencode
```

OpenCode loads the plugin at startup. Dr. LawDog's context is injected
automatically into each new conversation.

### Via lola

The lola post-install hook handles `opencode.json` and `AGENTS.md` automatically.

> **Important:** run `lola install` from inside `$LAWDOG_CASES_DIR` (default:
> `~/lawdog-cases`). The hook writes `opencode.json` and `AGENTS.md` to that
> directory.

```bash
cd ~/lawdog-cases

# Register the module (once per machine)
lola mod add /path/to/lawdog/plugin

# Install for OpenCode
lola install lawdog -a opencode

# Restart OpenCode to load the plugin
opencode
```

The post-install hook:
1. Patches `opencode.json` — adds `"plugin": ["<absolute-module-path>"]`
2. Writes `AGENTS.md` from `plugin/templates/lawdog-cases.AGENTS.md` if the
   file is missing or contains a stale hardcoded path

### `opencode.json` reference

Minimal working configuration (project-scoped, placed at `~/lawdog-cases/opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["/absolute/path/to/lawdog/plugin"]
}
```

OpenCode also supports a global config at `~/.config/opencode/opencode.json`.
Use the global config if you want Dr. LawDog available in any directory, not
just inside `~/lawdog-cases`.

Configs are **merged** — the project config's `"plugin"` array adds to, not
replaces, the global one.

---

## Lola

[Lola](https://github.com/LobsterTrap/lola) is an AI context module manager
that installs skills and instructions to multiple AI assistants from a single
module definition.

### Adding the lawdog module

From a local clone:

```bash
lola mod add /path/to/lawdog/plugin
```

From a git URL (once published):

```bash
lola mod add https://github.com/mrbrandao/lawdog.git
```

> **Note:** The git URL install requires `package.json` at the repo root.
> Currently `package.json` is inside `plugin/`. Until the repo is restructured
> or published to npm, use the local path form.

### Installing for Claude Code

```bash
# Run from the project directory where you want skills installed
lola install lawdog -a claude-code
```

What this installs:
- Skills to `.claude/skills/<name>/SKILL.md`
- Dr. LawDog persona injected into `CLAUDE.md` (managed section)

Hooks and WebSearch permissions still require manual setup — see
[Session-start hook](#session-start-hook) and [WebSearch permissions](#websearch-permissions).

### Installing for OpenCode

```bash
# Run from inside ~/lawdog-cases (or $LAWDOG_CASES_DIR)
cd ~/lawdog-cases
lola install lawdog -a opencode
```

What the post-install hook does automatically:
1. Resolves the absolute path of the lola-installed module at `.lola/modules/lawdog/`
2. Patches `opencode.json` with `"plugin": ["<absolute-path>"]`
3. Writes `lawdog-cases.AGENTS.md` template to `$LAWDOG_CASES_DIR/AGENTS.md`
   (only if the file is missing or contains a stale hardcoded path)

After install, restart OpenCode for the plugin to be picked up.

---

## Skills reference

### `caso` — Case management

Opens a new case or resumes an existing one. Conducts full intake (narrative →
triage → adversarial simulation → decision), creates the case directory
structure, generates `caso.md`, and guides the user through the full JEC
lifecycle.

```
/lawdog:caso
```

### `movimentacao` — Register court movement

Registers a new PROJUDI movement (judge decision, defendant response,
intimação), reads the PDF, interprets it legally, updates `caso.md`, and
orients next steps.

```
/lawdog:movimentacao obra-irregular
```

### `peticao` — Draft petition

Drafts a petition in three phases: rascunho (draft applying the Triple Lens —
author's lawyer, defendant's lawyer, magistrate), refinement (iterative edits
until user approves), official PDF via `doc2pdf`. Only generates PDF after
explicit user approval.

```
/lawdog:peticao obra-irregular
/lawdog:peticao obra-irregular 04-peticao
```

### `importar-caso` — Ingest existing case

Organizes an existing unstructured case into lawdog format. Analyzes files in
batches of 20, proposes a classification table, user validates, then applies
the directory structure.

```
/lawdog:importar-caso
```

### `juntada` — Organize evidence

Organizes evidence from `anexos/` into a numbered, JEC-ready `juntada/`.
Batch naming in one table interaction, parallel conversions, enforces 4 MB
limit. Dispatches `img2pdf`, `video2forum`, `doc2pdf`, and `pdf-split` as
parallel sub-agents.

```
/lawdog:juntada obra-irregular
/lawdog:juntada obra-irregular peticao-02
```

### `fetch-law` — Fetch legal article

Fetches updated legal text from planalto.gov.br or the relevant TJ portal.
Falls back to WebSearch if the direct fetch is blocked.

```
/lawdog:fetch-law Lei 9.099/95 Art. 3
/lawdog:fetch-law CDC Art. 42
```

### `video2forum` — Convert video for PROJUDI

Converts video evidence to a format accepted by PROJUDI/TJPR. Default output
is MP4/H.264+AAC (PROJUDI-proven). Use `--webm` flag for VP8/Vorbis WebM
if the court system rejects MP4.

```
/lawdog:video2forum ~/docs/case/*.MOV
/lawdog:video2forum --webm evidence.mp4
```

### Conversion skills

| Skill | Input → Output | Notes |
|---|---|---|
| `img2pdf` | `.jpg` `.png` `.heic` → `.pdf` | Quality reduction if output > `LAWDOG_PDF_SIZE` (4 MB) |
| `doc2pdf` | `.md` `.txt` `.doc` `.docx` → `.pdf` | pandoc + pdflatex + `base-legal.latex` judicial template |
| `pdf-split` | `.pdf` > 4 MB → parts | Document PDFs only — never use on image PDFs |
| `doc2docx` | `.md` `.txt` → `.docx` | Editable version via pandoc; convert back with `doc2pdf` before PROJUDI upload |

---

## Troubleshooting

### Plugin not loading in OpenCode

1. Check `opencode.json` — path in `"plugin"` must be **absolute**. Tilde `~/`
   is not expanded. Run `realpath ~/lawdog/plugin` to get the correct path.
2. Restart OpenCode after any change to `opencode.json`.
3. Check logs: `opencode run --print-logs "hello" 2>&1 | grep -i lawdog`

### Skills not discovered

1. Verify `SKILL.md` files are in `plugin/skills/<name>/SKILL.md` (all caps).
2. Check that the plugin loaded (see above).
3. In OpenCode, list skills: ask the agent to "use the skill tool to list skills".

### `LAWDOG_PLUGIN_DIR` not set

Script-based skills (`juntada`, `img2pdf`, etc.) fail if neither `CLAUDE_SKILL_DIR`
nor `LAWDOG_PLUGIN_DIR` is set. This should not happen when using the plugin —
`LAWDOG_PLUGIN_DIR` is set by `lawdog.js` at plugin load time.

If running skills without the plugin (e.g., skills-only lola install), set it manually:

```bash
export LAWDOG_PLUGIN_DIR=/absolute/path/to/lawdog/plugin
```

### `LAWDOG_CASES_DIR` not found

Run `plugin/scripts/setup.sh` again and reload your shell:

```bash
bash plugin/scripts/setup.sh
source ~/.bashrc
```

### `AGENTS.md` still has stale hardcoded path

If `~/lawdog-cases/AGENTS.md` references a hardcoded machine path, replace it
with the portable template:

```bash
cp /path/to/lawdog/plugin/templates/lawdog-cases.AGENTS.md ~/lawdog-cases/AGENTS.md
```

Or run `lola install lawdog -a opencode` from `~/lawdog-cases` — the post-install
hook detects and replaces stale files automatically.
