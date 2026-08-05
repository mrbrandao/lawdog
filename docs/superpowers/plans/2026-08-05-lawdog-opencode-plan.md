# Lawdog OpenCode Support — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the lawdog plugin work natively in OpenCode via its npm-style plugin
system, while keeping full Claude Code plugin compatibility, and producing a
path-agnostic `AGENTS.md` template for the lawdog-cases workspace.

**Architecture:** OpenCode uses `package.json` + `.opencode/plugins/lawdog.js` (same
pattern as superpowers). The plugin JS registers skills and injects session context
via transform hook. Script paths in SKILL.md files use `LAWDOG_PLUGIN_DIR` as fallback
when `CLAUDE_SKILL_DIR` is not set. The lola post-install hook patches `opencode.json`
when installing for opencode.

**Tech Stack:** ESM JavaScript (Node.js built-ins only), Bash, Python 3 stdlib,
existing lola module system, OpenCode plugin API.

## Global Constraints

- Must not break existing Claude Code plugin install (`.claude-plugin/`)
- `make test` must pass after every commit
- Commits every ~150 lines of change; conventional commits format
- **No hardcoded personal paths** — no `/home/<user>`, no machine-specific absolute
  paths in any committed file (code, docs, plans). Use `~/`, `$HOME`, `<repo-root>`,
  env vars, or `$(git rev-parse --show-toplevel)`
- All new files under `plugin/` — no changes to repo root structure
- Bash fallback pattern: `${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/<name>}`

---

### Task 1: Design spec + plan docs

**Files:**
- Create: `docs/superpowers/specs/2026-08-05-lawdog-opencode-design.md`
- Create: `docs/superpowers/plans/2026-08-05-lawdog-opencode-plan.md` (this file)

- [x] Write design spec
- [x] Write this plan file

- [ ] **Commit**

```bash
git add docs/superpowers/specs/2026-08-05-lawdog-opencode-design.md \
        docs/superpowers/plans/2026-08-05-lawdog-opencode-plan.md
git commit -m "docs: add opencode support design spec and implementation plan"
```

---

### Task 2: OpenCode plugin package files

**Files:**
- Create: `plugin/package.json`
- Create: `plugin/.opencode/plugins/lawdog.js`

**Produces:** `LAWDOG_PLUGIN_DIR` env var, OpenCode `config` hook (skills
registration), `experimental.chat.messages.transform` hook (session context).

- [ ] **Step 1: Create `plugin/package.json`**

```json
{
  "name": "lawdog",
  "version": "0.5.0",
  "description": "Dr. Andre LawDog — AI legal assistant for Brazilian JEC court workflows.",
  "type": "module",
  "main": ".opencode/plugins/lawdog.js",
  "keywords": ["lawdog", "jec", "brasil", "legal", "skills"],
  "author": "mrbrandao",
  "license": "MIT"
}
```

- [ ] **Step 2: Create `plugin/.opencode/plugins/lawdog.js`**

See full file content in the spec (`2026-08-05-lawdog-opencode-design.md`).
Key structure:

```javascript
// .opencode/plugins/lawdog.js → up two levels → plugin/ root
const PLUGIN_DIR = path.resolve(__dirname, '../..');
process.env.LAWDOG_PLUGIN_DIR = PLUGIN_DIR;

export const LawdogPlugin = async ({ client, directory }) => ({
  config: async (config) => { /* add SKILLS_DIR to config.skills.paths */ },
  'experimental.chat.messages.transform': async (_input, output) => {
    /* inject Dr. LawDog context once per conversation */
  },
});
```

- [ ] **Step 3: Smoke test**

```bash
cd <repo-root>/plugin
node --input-type=module <<'EOF'
import { LawdogPlugin } from './.opencode/plugins/lawdog.js';
console.log('type:', typeof LawdogPlugin);
console.log('LAWDOG_PLUGIN_DIR set:', !!process.env.LAWDOG_PLUGIN_DIR);
EOF
```

Expected:
```
type: function
LAWDOG_PLUGIN_DIR set: true
```

- [ ] **Step 4: `make test`** — must pass

- [ ] **Step 5: Commit** (~160 lines: package.json + lawdog.js)

```bash
git add plugin/package.json plugin/.opencode/plugins/lawdog.js
git commit -m "feat(opencode): add native OpenCode plugin entry point"
```

---

### Task 3: Fix `${CLAUDE_SKILL_DIR}` script paths in SKILL.md files

Five skills use `${CLAUDE_SKILL_DIR}` in bash commands (OpenCode doesn't set it).
Pattern: prepend `LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/<name>}"`
before each `uv run` / `bash` call, then reference `${LAWDOG_SKILL}` instead.

**Files:**
- Modify: `plugin/skills/juntada/SKILL.md` (3 occurrences, Step 1 in code block)
- Modify: `plugin/skills/img2pdf/SKILL.md` (1 occurrence)
- Modify: `plugin/skills/doc2pdf/SKILL.md` (2 occurrences incl. template path)
- Modify: `plugin/skills/video2forum/SKILL.md` (2 occurrences)
- Modify: `plugin/skills/pdf-split/SKILL.md` (1 occurrence)

- [ ] **Step 1: juntada** — add resolver before first code block, update all 3 calls

```bash
LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/juntada}"
uv run "${LAWDOG_SKILL}/scripts/juntada.py" list-pending "$ANEXOS"
```

Resolve-conflict and tag calls become `"${LAWDOG_SKILL}/scripts/juntada.py"`.

- [ ] **Step 2: img2pdf**

```bash
LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/img2pdf}"
uv run "${LAWDOG_SKILL}/scripts/image_to_pdf.py" -i "<input>" -o "<output>"
```

- [ ] **Step 3: doc2pdf**

```bash
LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/doc2pdf}"
uv run "${LAWDOG_SKILL}/scripts/doc2pdf.py" \
    -i "<input>" -o "<output>" \
    -t "${LAWDOG_SKILL}/../../templates/base-legal.latex"
```

Note: `${LAWDOG_SKILL}/../../` resolves to `plugin/` in both runtimes.

- [ ] **Step 4: video2forum** — 2 occurrences (default MP4 + WebM fallback)

```bash
LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/video2forum}"
FFMPEG="${FFMPEG:-$HOME/bin/ffmpeg}" \
bash "${LAWDOG_SKILL}/scripts/video2forum.sh" -i "<input>" -o "<output>.mp4"
```

- [ ] **Step 5: pdf-split**

```bash
LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/pdf-split}"
uv run "${LAWDOG_SKILL}/scripts/pdf_split.py" -i "<input.pdf>" -o "<output-prefix>"
```

- [ ] **Step 6: `make test-skills && make test`** — must pass

- [ ] **Step 7: Commit** (~25 lines across 5 files)

```bash
git add plugin/skills/juntada/SKILL.md \
        plugin/skills/img2pdf/SKILL.md \
        plugin/skills/doc2pdf/SKILL.md \
        plugin/skills/video2forum/SKILL.md \
        plugin/skills/pdf-split/SKILL.md
git commit -m "fix(skills): support LAWDOG_PLUGIN_DIR fallback for OpenCode script paths"
```

---

### Task 4: `lawdog-cases` AGENTS.md template + OpenCode post-install support

**Files:**
- Create: `plugin/templates/lawdog-cases.AGENTS.md`
- Modify: `plugin/scripts/install-permissions.sh`

**Produces:**
- `$LAWDOG_CASES_DIR/AGENTS.md` — written by post-install, path-agnostic
- `opencode.json` — patched with `"plugin"` entry pointing to module

- [ ] **Step 1: Create `plugin/templates/lawdog-cases.AGENTS.md`**

Self-contained, no external file references, no hardcoded paths.
Key sections: what lawdog is, directory structure rules (embedded directly),
evidence pipeline rules, docs pipeline, env vars, skill names.

- [ ] **Step 2: Rewrite `plugin/scripts/install-permissions.sh`**

Structure:
```
if claude-code → write .claude/settings.json (existing logic)
if opencode   → patch opencode.json + write lawdog-cases/AGENTS.md from template
else          → echo no-op and exit
```

Module path for opencode branch: `"${LOLA_PROJECT_PATH}/.lola/modules/${LOLA_MODULE_NAME:-lawdog}"`

Detect stale AGENTS.md: `grep -q 'dev/gen/lawdog\|/home/' "$AGENTS_TARGET"`

- [ ] **Step 3: `chmod +x` + syntax check**

```bash
chmod +x plugin/scripts/install-permissions.sh
bash -n plugin/scripts/install-permissions.sh
```

- [ ] **Step 4: `make test`**

- [ ] **Step 5: Commit** (~90 lines: template + updated script)

```bash
git add plugin/templates/lawdog-cases.AGENTS.md \
        plugin/scripts/install-permissions.sh
git commit -m "feat(opencode): add lawdog-cases AGENTS.md template and lola OpenCode post-install"
```

---

### Task 5: Fix `~/lawdog-cases/AGENTS.md`

**Files:**
- Modify: `~/lawdog-cases/AGENTS.md`

Not a git-tracked file (data dir, not source repo). No commit needed.

- [ ] **Step 1: Check for hardcoded paths**

```bash
grep -En '/home/[^/]+/dev/|/Users/[^/]+/dev/' ~/lawdog-cases/AGENTS.md
```

- [ ] **Step 2: Replace with template**

```bash
cp <repo-root>/plugin/templates/lawdog-cases.AGENTS.md ~/lawdog-cases/AGENTS.md
```

- [ ] **Step 3: Verify clean**

```bash
grep -En '/home/[^/]+/dev/|/Users/[^/]+/dev/' ~/lawdog-cases/AGENTS.md
# Expected: no output
```

---

### Task 6: Update documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Update `CLAUDE.md`**

Changes:
1. Architecture tree — add `package.json`, `.opencode/plugins/lawdog.js`,
   `templates/lawdog-cases.AGENTS.md`
2. Add `## Path hygiene` section with the convention table
3. Add OpenCode install note to `## Plugin versioning` section
4. Update `## Known bugs` — nothing new
5. Update version/branch line if needed

- [ ] **Step 2: Update `docs/BACKLOG.md`**

Mark completed: OpenCode native plugin, CLAUDE_SKILL_DIR fix, AGENTS.md template,
lola post-install. Add future lola improvement item.

- [ ] **Step 3: `make test`**

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/BACKLOG.md
git commit -m "docs: update architecture, add path hygiene convention, update backlog"
```

---

## Self-Review

**Spec coverage:** All 6 design requirements have corresponding tasks.

**Path hygiene:** No `/home/<user>` or machine-specific paths. Expected outputs use
`<repo-root>/plugin` placeholders.

**Type consistency:** `LawdogPlugin` (export), `buildContext` (function),
`detectActiveCases` (function), `readAgents` (function) — consistent across plan
and implementation.
