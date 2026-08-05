# Skill /lawdog:peticao — Design Spec

**Date:** 2026-06-04
**Status:** approved
**Scope:** Petition drafting skill — reads caso.md, applies adversarial lens,
verifies all legal articles, drafts in three states (draft → refinement → official),
converts to PDF only when user explicitly approves.

---

## 1. Context

After a case passes triage and the user confirms opening it, lawdog creates the
directory structure and `caso.md`. The next step — drafting the petition — has
no dedicated skill. The user must write the petition manually or rely on ad-hoc
conversation. This spec defines `/lawdog:peticao` to close that gap.

The petition is the most legally critical document in the case. It must read as
if written by an experienced lawyer — not AI-generated, not repetitive, not
padded. The judge should be able to read it quickly and understand exactly what
happened, what the legal basis is, and what is being requested.

---

## 2. Architecture

**Skill type:** Pure SKILL.md — no dedicated script.
Petition drafting is cognitive work, not mechanical operation. Scripts handle
file operations; the LLM handles legal reasoning.

**Sub-skills called internally:**
- `/lawdog:fetch-law` — verify any article not in the embedded knowledge base
- `/lawdog:doc2pdf` — convert approved petition to PDF (deferred until approval)
- `/lawdog:pdf-split` — if PDF exceeds LAWDOG_PDF_SIZE

**Protocols imported:**
- `protocols/document-standards.md` — mandatory quality rules (no AI slop)
- `protocols/file-structure.md` — where to save files
- `protocols/knowledge-sources.md` — article lookup order
- `protocols/case-lifecycle.md` — case state and movement context

---

## 3. Three-state workflow

```
DRAFT                  REFINEMENT             OFFICIAL
──────────────────     ──────────────────     ──────────────────
docs/<name>-rascunho.md  → (section edits) →  docs/<name>.md
                                               juntada/NN-<name>.pdf
```

The `-rascunho.md` suffix marks the file as not-yet-official. Only when the
user explicitly approves does the workflow proceed to rename + convert.

---

## 4. Full flow

### Phase 1 — Preparation (before writing a single word)

1. **Read `caso.md` completely** — partes, fatos, timeline, fundamento jurídico,
   evidências disponíveis, pontos fracos identificados.

2. **Apply Lente Tríplice internally** — simulate the best possible defense:
   - What will the defendant's lawyer argue against each fact?
   - Which evidence is weakest? Which is strongest?
   - Would a judge find the damages claim proportional and documented?
   - Adjust the petition structure to preemptively address the strongest defense points.

3. **Verify all legal articles** — for every article to be cited:
   - Check `knowledge/index.md` → `knowledge/codigo-civil-jec.md` first
   - If not embedded or if currency is uncertain: call `/lawdog:fetch-law`
   - Never cite from memory. If an article cannot be verified: do not cite it.

4. **Determine petition type** from case state:
   - No prior petitions: `peticao-inicial`
   - Responding to judge's request (emenda): `emenda-inicial`
   - Responding to defendant's filing: `replica`
   - General subsequent filing: `peticao-NN`

### Phase 2 — Complete draft

Write the full petition in high-quality Brazilian Portuguese. Standards from
`protocols/document-standards.md` apply strictly:

**Structure (mandatory order, no deviations):**

```markdown
# Petição [Inicial | Emenda à Inicial | Réplica]

**Ao Juízo do [Vara/Juizado] de [Comarca/UF]**

**Requerente:** [nome], portador do CPF [nnn.nnn.nnn-nn], residente em [endereço]
**Requerido:** [nome ou razão social], [CPF/CNPJ], [endereço se conhecido]

---

## Dos Fatos

[Chronological narrative, concrete, no adjectives. Every sentence adds
information. Active voice. Each paragraph = one idea.]

## Do Direito

[Legal basis: verified articles cited inline as (CC, Art. 927).
Argument flows naturally from facts. No repetition of facts here.]

## Dos Pedidos

Ante o exposto, requer:

1. [Specific request 1]
2. [Specific request 2]
3. A condenação em custas processuais.

[City], [date].

[Requerente name]
CPF: [nnn.nnn.nnn-nn]
```

**Quality rules (enforced — no exceptions):**
- No "Excelentíssimo Senhor Doutor" — courts accept direct addressing
- No filler opening ("Vem respeitosamente...")
- No "Ante o exposto" in the body — only before the Pedidos
- No restatement of facts in Do Direito
- No hollow affirmations ("É notório que...", "Está amplamente demonstrado...")
- Damages requested must be proportional and supported by documented evidence
- Each exhibit referenced in the text where it is relevant, not at the end as a list

Save as `docs/<petition-type>-rascunho.md` in the current petition directory.

Present to user:

> "✏️ Rascunho pronto. Leia com atenção antes de aprovar — ainda não é a versão
> final, nenhum PDF foi gerado. Peça ajustes em qualquer seção quando quiser.
> Quando estiver satisfeito com o texto, diga **aprovar** para gerar o PDF oficial."

### Phase 3 — Refinement (on user request)

If the user requests changes to any section:
1. Identify which section(s) need revision
2. Re-draft only the requested section(s)
3. Apply the same quality standards — never relax them for "just a small change"
4. Present the revised section(s) clearly
5. Update the `-rascunho.md` file

The user may iterate as many times as needed. Each revision updates the draft.
Dr. LawDog never pushes back against user-requested changes on grounds of style,
but does flag if a requested change would weaken the legal argument or add filler.

### Phase 4 — Approval and conversion

Triggered only by explicit user approval ("aprovar", "está bom", "pode gerar o PDF"):

1. Determine the sequence number from `caso.md` Movimentações table for the
   current petition (e.g., `01` for petição inicial)

2. Rename draft to official name:
   ```bash
   mv "docs/<name>-rascunho.md" "docs/<name>.md"
   ```

3. Convert to PDF:
   ```bash
   uv run "${CLAUDE_SKILL_DIR}/../doc2pdf/scripts/doc2pdf.py" \
       -i "docs/<name>.md" \
       -o "juntada/NN-<name>.pdf" \
       -t "${CLAUDE_SKILL_DIR}/../../templates/base-legal.latex"
   ```

4. Check size against LAWDOG_PDF_SIZE. If exceeded:
   ```bash
   uv run "${CLAUDE_SKILL_DIR}/../pdf-split/scripts/pdf_split.py" \
       -i "juntada/NN-<name>.pdf" \
       -o "juntada/NN-<name>"
   ```

5. Update `caso.md` Movimentações table with the new petition entry.

6. Inform the user:
   > "✅ Petição oficial gerada em `juntada/NN-<name>.pdf`. Pronta para upload
   > no PROJUDI."

---

## 5. Subsequent petitions

For `peticao-02`, `emenda-inicial`, `replica`, etc.:

1. Read `caso.md` to understand current case state
2. Read the movement that prompted this petition:
   - If responding to judge: read `NN-decisao-juiz/docs/` PDFs
   - If responding to defendant: read `NN-manifestacao-reu/docs/` PDFs
3. Adapt the petition header and structure to the filing type:
   - **Emenda à inicial:** addresses judge's specific requests
   - **Réplica:** responds to defendant's arguments point by point
   - **Manifestação subsequente:** general case update/evidence addition
4. Same three-state flow: draft → refinement → approval

---

## 6. Petition file naming

| Petition type | Draft file | Official file | juntada/ |
|---|---|---|---|
| Petição inicial | `docs/peticao-inicial-rascunho.md` | `docs/peticao-inicial.md` | `juntada/01-peticao-inicial.pdf` |
| Emenda à inicial | `docs/emenda-inicial-rascunho.md` | `docs/emenda-inicial.md` | `juntada/NN-emenda-inicial.pdf` |
| Réplica | `docs/replica-rascunho.md` | `docs/replica.md` | `juntada/NN-replica.pdf` |

`NN` = PROJUDI sequence number from `caso.md` Movimentações table.

---

## 7. Design decisions

| Decision | Choice | Reason |
|---|---|---|
| No dedicated script | Pure SKILL.md | Drafting is cognitive, not mechanical |
| Draft suffix `-rascunho.md` | Explicit state marker | User never confuses draft with official |
| Conversion deferred | Only on explicit "aprovar" | Prevents generating PDFs of unreviewed drafts |
| Article verification | knowledge/ first, fetch-law always if uncertain | Never cites from memory — legal accuracy is non-negotiable |
| Lente Tríplice before writing | Pre-emptive adversarial analysis | Petition anticipates defense; stronger arguments |
| No filler phrases | Enforced by document-standards.md | Judge reads 50+ petitions/day; clarity = respect |
| Refinement is section-level | User specifies which section | Faster than full regeneration; preserves good sections |
