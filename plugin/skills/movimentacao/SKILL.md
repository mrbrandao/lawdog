---
name: movimentacao
description: >-
  Registers a new case movement (judge decision, defendant response, court
  intimation, or any PROJUDI act) into the lawdog case structure. Reads the
  movement document, interprets it legally, updates caso.md Estado atual and
  Movimentações table, and orients the user on the next required action.
  TRIGGER when: user mentions a new court event, uploads a PROJUDI PDF, says
  the judge decided something, received a manifestação, or got an intimação.
  SKIP: do not trigger for case opening (use /lawdog:caso) or evidence filing
  (use /lawdog:juntada).
compatibility: >-
  Reads PDFs placed in <NN-tipo>/docs/ by the user or /lawdog:caso.
  Requires LAWDOG_CASES_DIR set (setup.sh configures it).
  Check: echo $LAWDOG_CASES_DIR
allowed-tools: Bash Read Write
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolos importados

- `protocols/case-lifecycle.md` — movement registration rules and orientation by type
- `protocols/file-structure.md` — directory naming (single source of truth)

## Trigger

Invoked by `/lawdog:caso` after detecting a new movement in conversation,
or directly by the user: `/lawdog:movimentacao <case-slug>`

## Fluxo

### Step 1 — Identify the movement

Read `caso.md` Estado atual to understand current case state.
If the user provided a PDF path: read the document.
Classify the movement type: `decisao-juiz`, `manifestacao-reu`, `intimacao`,
`peticao`, or `contranotificacao-reu`.

### Step 2 — Create the directory

Determine the next sequence number from `caso.md` Movimentações table:

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
# next number = last seq in Movimentações + 1, zero-padded to 2 digits
mkdir -p "$CASES_DIR/<case-slug>/<NN>-<type>/docs"
```

For `peticao` type, also create `anexos/` and `juntada/`:
```bash
mkdir -p "$CASES_DIR/<case-slug>/<NN>-peticao/docs"
mkdir -p "$CASES_DIR/<case-slug>/<NN>-peticao/anexos"
mkdir -p "$CASES_DIR/<case-slug>/<NN>-peticao/juntada"
```

### Step 3 — Copy the document

If user provided a path:
```bash
cp "<user-provided-path>" "$CASES_DIR/<case-slug>/<NN>-<type>/docs/"
```

### Step 4 — Interpret legally

Apply `protocols/case-lifecycle.md` → "Orientation by Movement Type" rules.
Identify: what is being requested, what is the legal deadline, what must happen next.

### Step 5 — Update caso.md

Add a row to the Movimentações table and update Estado atual with current phase,
last movement, running deadline, and pending action.

### Step 6 — Orient the user

State clearly in Portuguese: what the act means legally, the deadline (if any)
and whether it is improrrogável, what the user must prepare or do next.

## Gotchas

- **Deadline is the most critical information.** Missing a prazo in JEC is
  irrecoverable. Always state it first, in bold, with the exact date if calculable.
- **Never create `juntada/` for judge or defendant movements** — only `docs/`
  is needed. `juntada/` is only for user filings (petições).
- **If caso.md does not exist** for the given slug, instruct the user to open
  the case first with `/lawdog:caso` before registering movements.
- **Future agent note:** this skill is designed for manual PDF injection. When
  the automated PROJUDI agent is implemented, it will call this skill with the
  PDF path and PROJUDI sequence number. The protocol is the same.
