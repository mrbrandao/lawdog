# Case Lifecycle Design (Sub-project B)

**Date:** 2026-06-02
**Status:** implemented
**Note:** Full spec was lost in a git filter-repo accident on 2026-06-04.
Implementation is complete. See the implemented files:

- `plugin/protocols/case-lifecycle.md` — full lifecycle behavioral contract
- `plugin/protocols/file-structure.md` — NN-tipo/ directory structure
- `plugin/protocols/case-intake.md` — Step 0 resumption + extrajudicial assessment
- `plugin/skills/movimentacao/SKILL.md` — register court movements

Key design decisions implemented:
- Directory naming: `NN-tipo/` mirrors PROJUDI sequence numbers
- Pre-judicial phase: `00a-notificacao-extrajudicial/`, `00b-contranotificacao-reu/`
- `caso.md` has `Estado atual` (phase, last movement, deadline, pending action)
  and `Movimentações` table (seq, dir, date, type, actor, deadline)
- `/lawdog:caso` checks `caso.md` before intake (Step 0) — resumes if active
- `/lawdog:movimentacao` registers any PROJUDI act, updates `caso.md`
- Deadline is the most critical info — always stated first, in bold
