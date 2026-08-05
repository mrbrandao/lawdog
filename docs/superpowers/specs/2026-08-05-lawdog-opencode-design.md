# Lawdog OpenCode Support — Design Spec

**Date:** 2026-08-05
**Status:** Approved
**Author:** mrbrandao

---

## Problem

The lawdog plugin runs in Claude Code via `.claude-plugin/` manifest. OpenCode is a
separate AI coding assistant with a fundamentally different plugin system — it uses
npm-style packages registered in `opencode.json`. Skills, session context injection,
and script execution all work differently.

**Gaps that prevent lawdog from working in OpenCode:**

1. `${CLAUDE_SKILL_DIR}` env var (set by Claude Code) is not set by OpenCode — bash
   script calls in SKILL.md files fail silently
2. Shared files (`protocols/`, `knowledge/`) are not co-installed by lola alongside skills
3. Session-start hook (`hooks/hooks.json`) is Claude Code-specific; OpenCode has no
   equivalent hook mechanism
4. `~/lawdog-cases/AGENTS.md` contains a hardcoded personal machine path
   (`~/dev/gen/lawdog`) that leaks the developer's local filesystem layout

---

## Key Finding: Two Incompatible Plugin Systems

| Aspect | Claude Code | OpenCode |
|---|---|---|
| Plugin manifest | `.claude-plugin/plugin.json` | `package.json` + `"plugin": [...]` in `opencode.json` |
| Skill registration | lola installs to `.claude/skills/` | Plugin JS registers via `config` hook |
| Session context | `hooks/hooks.json` `SessionStart` hook | `experimental.chat.messages.transform` hook |
| Skill dir env var | `CLAUDE_SKILL_DIR` (per-skill), `CLAUDE_PLUGIN_ROOT` | Not set |
| Reference model | superpowers Claude Code install | superpowers OpenCode install |

The superpowers project (github.com/obra/superpowers) demonstrates the correct
OpenCode pattern: a `package.json` + `.opencode/plugins/superpowers.js` entry
point that hooks into OpenCode's config and transform APIs.

---

## Architecture

Both install modes share a single `plugin/` directory. No duplication.

```
plugin/
├── .claude-plugin/              ← Claude Code plugin manifest (unchanged)
├── package.json                 ← NEW: OpenCode npm-style package descriptor
├── .opencode/
│   └── plugins/
│       └── lawdog.js            ← NEW: OpenCode plugin entry point
├── AGENTS.md                    ← Dr. LawDog persona (unchanged)
├── hooks/                       ← Claude Code SessionStart hooks (unchanged)
├── skills/                      ← Shared: all skills work in both runtimes
├── protocols/                   ← Shared: referenced via LAWDOG_PLUGIN_DIR
├── knowledge/                   ← Shared: referenced via LAWDOG_PLUGIN_DIR
├── templates/
│   ├── base-legal.latex         ← Existing
│   └── lawdog-cases.AGENTS.md  ← NEW: path-agnostic workspace template
└── scripts/
    ├── install-permissions.sh   ← UPDATED: adds opencode branch
    └── setup.sh                 ← Unchanged
```

---

## Design Decisions

### 1. OpenCode plugin JS (`plugin/.opencode/plugins/lawdog.js`)

Mirrors `superpowers/.opencode/plugins/superpowers.js`. Three responsibilities:

**a) `config` hook** — registers `plugin/skills/` in `config.skills.paths` so
OpenCode discovers all lawdog skills without symlinks or manual config.

**b) `experimental.chat.messages.transform` hook** — injects Dr. LawDog persona +
active case detection + skill table into the first user message of each conversation.
Replaces the Claude Code `session-start` hook entirely for OpenCode sessions.
Guard: skips if `lawdog-session-context` marker already present (prevents
re-injection on subsequent agent steps within the same conversation).

**c) `process.env.LAWDOG_PLUGIN_DIR`** — set to the absolute `plugin/` path at
plugin load time, so bash commands in SKILL.md files can find scripts regardless
of how the plugin was installed.

### 2. Script path fix — `LAWDOG_PLUGIN_DIR` fallback

Skills that run scripts currently use `${CLAUDE_SKILL_DIR}` (Claude Code env var).
Pattern after fix:

```bash
# Before (Claude Code only):
uv run "${CLAUDE_SKILL_DIR}/scripts/foo.py"

# After (both runtimes):
LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/<name>}"
uv run "${LAWDOG_SKILL}/scripts/foo.py"
```

Affected skills: `juntada`, `img2pdf`, `doc2pdf`, `video2forum`, `pdf-split`.
`doc2docx` uses `pandoc` directly — no change needed.

### 3. Protocol/knowledge path resolution

Skills reference `protocols/case-intake.md` etc. as instructions to the AI (not
bash commands). The OpenCode plugin's transform hook injects the absolute
`LAWDOG_PLUGIN_DIR` path into session context, telling the AI where to find all
protocol and knowledge files. No changes to individual SKILL.md protocol sections
needed.

### 4. `lawdog-cases/AGENTS.md` template

A path-agnostic template at `plugin/templates/lawdog-cases.AGENTS.md` that:
- Embeds file-structure rules directly (no external protocol file references)
- References skills by trigger name, not by path
- Uses `LAWDOG_CASES_DIR` and `LAWDOG_PDF_SIZE` env vars
- Contains zero hardcoded personal machine paths

The lola post-install hook (via `install-permissions.sh`) writes this template to
`$LAWDOG_CASES_DIR/AGENTS.md` when installing for OpenCode.

### 5. Lola post-install bridge for OpenCode

`install-permissions.sh` is extended with an `opencode` branch that:
1. Finds the lola-copied module path (`.lola/modules/lawdog/`)
2. Patches `opencode.json` to add `"plugin": ["<absolute-module-path>"]`
3. Writes `lawdog-cases.AGENTS.md` template to `$LAWDOG_CASES_DIR/AGENTS.md`

This bridges lola's file-based install into OpenCode's native plugin system.

---

## Install Paths

| User intent | Command / action |
|---|---|
| Claude Code plugin | Claude Code plugin install from `plugin/` |
| Claude Code via lola | `lola install lawdog -a claude-code` |
| OpenCode native (recommended) | Add `"plugin": ["<path>/lawdog/plugin"]` to `opencode.json` |
| OpenCode via lola | `lola install lawdog -a opencode` in `~/lawdog-cases` |

---

## Path Hygiene Convention

All committed files (code, docs, plans) must use generic references:

| Avoid | Use instead |
|---|---|
| `/home/<username>/` | `~/` or `$HOME/` in bash; `<your-home>` in docs |
| `/home/<username>/dev/lawdog` | `<repo-root>` or `$(git rev-parse --show-toplevel)` |
| Hardcoded username in grep | `grep -E '/home/[^/]+/dev/'` |
| Absolute path in expected output | `<repo-root>/plugin` |

---

## Future: Lola OpenCode Plugin Support

Currently the post-install hook manually patches `opencode.json`. A proper lola
enhancement would:
- Support `"plugin"` key natively in `lola.yaml` module config
- `lola install lawdog -a opencode` adds the plugin entry automatically
- `lola uninstall lawdog -a opencode` removes it

Tracked as: future lola improvement (see `docs/BACKLOG.md`).
