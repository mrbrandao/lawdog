# WebSearch Pre-Approval Design (Sub-project A)

**Date:** 2026-06-02
**Status:** approved
**Scope:** Eliminate per-call permission prompts for WebSearch and WebFetch in lawdog.
**Approach:** Two-layer solution — agentskills.io `allowed-tools` (portable) + `.claude/settings.json` (Claude Code specific).

---

## Problem

During real use, lawdog triggers WebSearch and WebFetch frequently for legal article lookups (fetch-law skill + inline lookups during case intake). Claude Code prompts the user for approval on every call, creating disruptive friction. The user wants lawdog to search without interruption.

## Solution Architecture

### Layer 1: `.claude/settings.json` (Claude Code)

New file at the repo root. Pre-approves WebSearch globally and WebFetch for specific legal domains only. No wildcard for all WebFetch — only the official sources lawdog uses.

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

If a new legal source needs to be added, it is added explicitly here.

### Layer 2: `allowed-tools` in SKILL.md (agentskills.io standard)

Each SKILL.md must declare exactly what it uses. This is the portable declaration that any agentskills.io-compliant assistant should honor.

| Skill | Correct `allowed-tools` | Change needed? |
|---|---|---|
| `video2forum` | `Bash` | No |
| `fetch-law` | `WebFetch WebSearch` | No (already correct) |
| `caso` | `Bash Read Write WebFetch WebSearch` | Yes — add WebSearch |
| `img2pdf` | `Bash` | No |
| `doc2pdf` | `Bash` | No |
| `pdf-split` | `Bash` | No |
| `doc2docx` | `Bash` | No |
| `juntada` | `Bash Read Write WebFetch WebSearch` | Yes — add WebSearch |

`caso` and `juntada` need `WebSearch` because they call `fetch-law` for article verification during intake and evidence analysis.

## What changes

| File | Change |
|---|---|
| `.claude/settings.json` | New file — project-level permission allowlist |
| `plugin/skills/caso/SKILL.md` | Add `WebSearch` to `allowed-tools` |
| `plugin/skills/juntada/SKILL.md` | Add `WebSearch` to `allowed-tools` |

## What does NOT change

- No scripts, protocols, or knowledge files touched.
- No changes to fetch-law, img2pdf, doc2pdf, pdf-split, doc2docx, video2forum.
- No global Claude Code settings modified.

## Fallback

If `.claude/settings.json` does not suppress prompts as expected, the fallback is to investigate the Claude Code version's permission model and add an equivalent mechanism (e.g., `~/.claude/settings.json` per-project path entry). The `allowed-tools` layer remains valid regardless.

## Testing

After implementation, test by invoking `/lawdog:caso` with a new case and observing whether WebSearch/WebFetch calls for article lookup proceed without approval prompts. If prompts still appear, escalate to fallback.
