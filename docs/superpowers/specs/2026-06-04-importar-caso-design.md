# Case Ingestion Design (Sub-project D)

**Date:** 2026-06-04
**Status:** implemented
**Note:** Full spec was lost in a git filter-repo accident on 2026-06-04.
Implementation is complete. See the implemented files:

- `plugin/skills/importar-caso/SKILL.md` — skill definition
- `plugin/skills/importar-caso/scripts/importar_caso.py` — file ops script
- `plugin/skills/importar-caso/tests/test_importar_caso.py` — 8 pytest tests
- `plugin/AGENTS.md` — Dr. Andre LawDog identity (lawyer + magistrate)

Key design decisions implemented:
- Dr. Andre LawDog: lawyer AND magistrate, three-perspective lens
  (advogado do autor / advogado do réu / magistrado)
- `/lawdog:importar-caso` ingests existing unorganized cases
- Batch analysis: max 20 files per round (context window preservation)
- Iterative table UX: read → propose → user validates → refine → confirm
- ⚠️ emoji mandatory before confirmation question
- Phase 4 via `importar_caso.py` (stdlib, no deps, PEP 723 compatible)
- External files: COPIED (original preserved)
- Internal files (inside LAWDOG_CASES_DIR): MOVED (no duplicates)
- Name conflict: `file.pdf` → `file-1.pdf` (kebab-case, no spaces)
- `caso.md` generated on first run, never overwritten
