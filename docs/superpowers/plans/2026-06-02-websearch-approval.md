# WebSearch Pre-Approval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate per-call WebSearch/WebFetch permission prompts in lawdog by adding project-level permissions and aligning SKILL.md `allowed-tools` with agentskills.io standards.

**Architecture:** Two-layer approach — `.claude/settings.json` for Claude Code project-level approval (committed to repo, not session-specific like `settings.local.json`), plus accurate `allowed-tools` in SKILL.md as the portable agentskills.io declaration. Only 3 files change.

**Tech Stack:** JSON (settings), YAML frontmatter (SKILL.md). No scripts, no Python, no tests — pure configuration.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `.claude/settings.json` | Project-level Claude Code permission allowlist |
| Modify | `plugin/skills/caso/SKILL.md` | Add `WebSearch` to `allowed-tools` |
| Modify | `plugin/skills/juntada/SKILL.md` | Add `WebSearch` to `allowed-tools` |

Note: `.claude/settings.local.json` already exists for session-specific permissions and must NOT be touched — it is not committed to git.

---

## Task 1: Create `.claude/settings.json`

**Files:**
- Create: `.claude/settings.json`

- [ ] **Step 1.1: Verify `.claude/` directory exists**

```bash
ls .claude/
```

Expected: `settings.local.json  skills/` (directory already exists from previous sessions)

- [ ] **Step 1.2: Write `.claude/settings.json`**

Write `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(https://www.planalto.gov.br/*)",
      "WebFetch(https://www.tjpr.jus.br/*)",
      "WebFetch(https://projudi.tjpr.jus.br/*)",
      "WebFetch(https://legis.senado.leg.br/*)",
      "WebFetch(https://www2.camara.leg.br/*)"
    ]
  }
}
```

- [ ] **Step 1.3: Verify the file is valid JSON**

```bash
python3 -c "import json; json.load(open('.claude/settings.json')); print('PASS: valid JSON')"
```

Expected: `PASS: valid JSON`

- [ ] **Step 1.4: Confirm settings.local.json is untouched**

```bash
python3 -c "import json; d=json.load(open('.claude/settings.local.json')); print('PASS: local settings intact, entries:', len(d['permissions']['allow']))"
```

Expected: `PASS: local settings intact, entries: 31`

- [ ] **Step 1.5: Commit**

```bash
git add .claude/settings.json
git commit -m "feat(permissions): add Claude Code project-level WebSearch approval"
```

---

## Task 2: Align SKILL.md `allowed-tools` (agentskills.io standard)

**Files:**
- Modify: `plugin/skills/caso/SKILL.md` (line with `allowed-tools`)
- Modify: `plugin/skills/juntada/SKILL.md` (line with `allowed-tools`)

- [ ] **Step 2.1: Verify current allowed-tools in both files**

```bash
grep "allowed-tools" plugin/skills/caso/SKILL.md plugin/skills/juntada/SKILL.md
```

Expected:
```
plugin/skills/caso/SKILL.md:allowed-tools: Bash, Read, Write, WebFetch
plugin/skills/juntada/SKILL.md:allowed-tools: Bash, Read, Write, WebFetch
```

- [ ] **Step 2.2: Update caso/SKILL.md**

In `plugin/skills/caso/SKILL.md`, change:
```yaml
allowed-tools: Bash, Read, Write, WebFetch
```
to:
```yaml
allowed-tools: Bash Read Write WebFetch WebSearch
```

Note: agentskills.io spec uses space-separated values, not comma-separated.

- [ ] **Step 2.3: Update juntada/SKILL.md**

In `plugin/skills/juntada/SKILL.md`, change:
```yaml
allowed-tools: Bash, Read, Write, WebFetch
```
to:
```yaml
allowed-tools: Bash Read Write WebFetch WebSearch
```

- [ ] **Step 2.4: Verify all 8 SKILL.md files pass validation**

```bash
make test-skills
```

Expected: `Results: 8/8 passed`

- [ ] **Step 2.5: Run full test suite**

```bash
make test
```

Expected: all suites pass.

- [ ] **Step 2.6: Commit**

```bash
git add plugin/skills/caso/SKILL.md plugin/skills/juntada/SKILL.md
git commit -m "feat(skills): align allowed-tools with agentskills.io spec — add WebSearch to caso and juntada"
```

---

## Task 3: Verification

- [ ] **Step 3.1: Confirm settings.json is committed**

```bash
git show --name-only HEAD~1 | grep settings.json && echo "PASS: settings.json committed"
```

- [ ] **Step 3.2: Confirm allowed-tools are correct in all 3 changed files**

```bash
grep "allowed-tools" .claude/settings.json 2>/dev/null || echo "n/a (json)"
grep "allowed-tools" plugin/skills/caso/SKILL.md
grep "allowed-tools" plugin/skills/juntada/SKILL.md
```

Expected:
```
allowed-tools: Bash Read Write WebFetch WebSearch
allowed-tools: Bash Read Write WebFetch WebSearch
```

- [ ] **Step 3.3: Manual smoke test (after reloading the plugin)**

Invoke `/lawdog:caso` or `/lawdog:fetch-law CDC Art. 42` and observe whether
WebSearch/WebFetch calls proceed without permission prompts.

If prompts still appear: check Claude Code version and consult the fallback
described in the spec (`docs/superpowers/specs/2026-06-02-websearch-approval-design.md`).
