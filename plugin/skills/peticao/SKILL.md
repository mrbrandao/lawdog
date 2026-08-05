---
name: peticao
description: >-
  Drafts JEC petitions as Dr. Andre LawDog — experienced lawyer, not AI template.
  Reads caso.md completely, applies adversarial Lente Tríplice before writing,
  verifies every cited article via knowledge/ then fetch-law, drafts complete
  petition, saves as -rascunho.md. PDF generated only on explicit user approval.
  Works for initial petition and subsequent filings (emenda, réplica, manifestação).
  TRIGGER when: user asks to write/draft the petition, says the case is approved
  and wants to start the petition, says "redigir petição", "escrever a petição",
  "gerar a petição inicial", "montar a petição".
  SKIP: do not trigger for case intake (use /lawdog:caso), for registering court
  movements (use /lawdog:movimentacao), or for organizing evidence (use /lawdog:juntada).
compatibility: >-
  Requires LAWDOG_CASES_DIR set (setup.sh configures it).
  Sub-skills used: fetch-law (article verification), doc2pdf (PDF generation),
  pdf-split (if PDF > LAWDOG_PDF_SIZE).
  Check: echo $LAWDOG_CASES_DIR
allowed-tools: Bash Read Write WebFetch WebSearch
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolos importados

Read before drafting — all four are mandatory:
- `protocols/document-standards.md` — quality rules (enforced strictly)
- `protocols/file-structure.md` — where to save files
- `protocols/knowledge-sources.md` — article lookup order
- `protocols/case-lifecycle.md` — case state and movement context

## Trigger

Invoked after `/lawdog:caso` opens a case and the user confirms proceeding.
Also invoked for subsequent petitions when responding to court movements.

Direct invocation: `/lawdog:peticao <case-slug> [petition-type]`
- `petition-type` defaults to `peticao-inicial` if not specified
- Other types: `emenda-inicial`, `replica`, `peticao` (for numbered subsequent)

## Fluxo

### Phase 0 — Determine petition type and context

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
PETITION_DIR="$CASES_DIR/<case-slug>/<petition-type>"
```

Read `caso.md` to determine:
- If writing `peticao-inicial`: use all data from caso.md
- If writing subsequent petition: also read the movement that prompted it
  (e.g., `09-decisao-juiz/docs/` for emenda, `20-manifestacao-reu/docs/` for réplica)

### Phase 1 — Preparation (internal, not shown to user)

Before writing a single word:

**1. Read `caso.md` completely:**
- Partes (requerente + requerido)
- Fatos (timeline from ## Timeline)
- Fundamento jurídico (from ## Fundamento jurídico)
- Evidências disponíveis
- Pontos fracos identificados

**2. Apply Lente Tríplice internally:**
- As advogado do réu: what are the strongest defense arguments?
- As magistrado: is the damages claim proportional? Is evidence sufficient?
- Adapt the petition to preemptively address the strongest defense points
- If a weakness is fatal to the case, warn the user before drafting

**3. Verify every legal article to be cited:**
- Follow `protocols/knowledge-sources.md` strictly
- Check `knowledge/index.md` → `knowledge/codigo-civil-jec.md` first
- For any article not embedded, or where currency is uncertain: call `/lawdog:fetch-law`
- Never cite from memory. If an article cannot be verified: do not cite it.
  Instead, note to the user which article needs manual verification.

### Phase 2 — Draft complete petition

Write the full petition in high-quality Brazilian Portuguese.
Apply all rules from `protocols/document-standards.md` without exception.

**Required structure:**

```markdown
# [Petição Inicial | Emenda à Petição Inicial | Réplica | Petição]

**Ao Juízo do [vara/juizado] — [Comarca/UF]**

**Requerente:** [nome completo], portador do CPF [nnn.nnn.nnn-nn],
residente em [endereço completo, city/UF, CEP]

**Requerido:** [nome ou razão social], [CPF/CNPJ se conhecido],
[endereço se conhecido]

## Dos Fatos

[Chronological, concrete, no adjectives beyond factual description.
Each paragraph = one idea. Active voice. No filler.]

## Do Direito

[Legal basis. Each article cited as (CC, Art. 927) inline.
Argument flows from facts. No repetition of facts here.]

## Dos Pedidos

Ante o exposto, requer:

1. [Specific, measurable request]
2. [Additional request if any]
3. A condenação ao pagamento das custas processuais.

Termos em que pede deferimento.

[City], [date].

[Requerente full name]
CPF: [nnn.nnn.nnn-nn]
```

**Quality enforcement — absolute prohibitions:**
- No "Excelentíssimo Senhor Doutor Juiz" — direct addressing only
- No "Vem respeitosamente..." opening
- No "Ante o exposto" anywhere except immediately before Pedidos
- No restatement of facts in Do Direito
- No "É notório que...", "Está amplamente demonstrado..."
- No padding, repetition, or hollow affirmations
- Damages must be proportional to documented evidence — never speculative
- Each exhibit referenced where it is factually relevant, not in a separate list

Save as `$PETITION_DIR/docs/<petition-type>-rascunho.md`:

```bash
mkdir -p "$PETITION_DIR/docs"
```

Then use the Write tool to save the drafted petition markdown.

Present to user in Portuguese:

> "✏️ Rascunho pronto. Leia com atenção — ainda não é a versão final, nenhum
> PDF foi gerado. Peça ajustes em qualquer seção. Quando estiver satisfeito
> com o texto, diga **aprovar** para gerar o PDF oficial."

### Phase 3 — Refinement (on user request)

If the user requests changes:
1. Identify which section needs revision
2. Re-draft only that section with the same quality standards
3. Update the `-rascunho.md` file
4. Present the change clearly
5. Return to waiting state — do not auto-proceed to Phase 4

The user may iterate as many times as needed.
Dr. LawDog may flag if a requested change weakens the legal argument,
but must implement what the user asks.

### Phase 4 — Approval and conversion

Triggered ONLY by explicit user approval:
- "aprovar", "está bom", "pode gerar o PDF", "gerar oficial", "confirmar"

**Step 4a — Rename draft to official:**
```bash
DRAFT="$PETITION_DIR/docs/<petition-type>-rascunho.md"
OFFICIAL="$PETITION_DIR/docs/<petition-type>.md"
mv "$DRAFT" "$OFFICIAL"
```

**Step 4b — Determine sequence number from caso.md Movimentações table**

For peticao-inicial: seq = `01`
For subsequent petitions: next seq after the movement that prompted this filing

**Step 4c — Convert to PDF:**
```bash
uv run "${CLAUDE_SKILL_DIR}/../doc2pdf/scripts/doc2pdf.py" \
    -i "$OFFICIAL" \
    -o "$PETITION_DIR/juntada/<NN>-<petition-type>.pdf" \
    -t "${CLAUDE_SKILL_DIR}/../../templates/base-legal.latex"
```

**Step 4d — Check size and split if needed:**
```bash
MAX="${LAWDOG_PDF_SIZE:-4194304}"
SIZE=$(stat -c%s "$PETITION_DIR/juntada/<NN>-<petition-type>.pdf" 2>/dev/null || \
       stat -f%z "$PETITION_DIR/juntada/<NN>-<petition-type>.pdf")
```

If SIZE > MAX:
```bash
uv run "${CLAUDE_SKILL_DIR}/../pdf-split/scripts/pdf_split.py" \
    -i "$PETITION_DIR/juntada/<NN>-<petition-type>.pdf" \
    -o "$PETITION_DIR/juntada/<NN>-<petition-type>"
```

**Step 4e — Update caso.md Movimentações table:**

Add row for this petition with date, type, and actor (Requerente).

**Step 4f — Confirm to user:**

> "✅ Petição oficial gerada em `juntada/<NN>-<petition-type>.pdf`.
> Pronta para upload no PROJUDI."

## Gotchas

- **Never generate PDF before explicit approval.** The `-rascunho.md` suffix is
  the safety marker. No PDF until the user says "aprovar" or equivalent.
- **Verify every article — no exceptions.** A wrong article number in a filed
  petition cannot be corrected without a formal amendment. Always check
  knowledge/ first, then fetch-law for anything uncertain.
- **Do NOT start drafting until Lente Tríplice analysis is complete.** The
  adversarial simulation must inform the structure and emphasis of the petition.
  A petition that ignores the likely defense is weaker than one that addresses it.
- **Quality standards do not relax during refinement.** If the user asks to
  add filler text or redundant sections, implement the change but note the concern.
- **`-rascunho.md` file belongs in `docs/`** — never in `juntada/`. Only
  converted PDFs go in `juntada/`.
- **Subsequent petitions must read the movement context.** Réplica without
  reading the defendant's manifestação is guesswork. Always read the source.
