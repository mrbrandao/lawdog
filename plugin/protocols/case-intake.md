# Protocol: Case Intake

Import this protocol in `/lawdog:caso`. Defines the full intake flow.

## Step 0 — Check Existing Case State

Before starting any intake, check whether the case already exists.

If `caso.md` exists for the requested case slug AND has an `Estado atual` section:
1. Read `Estado atual.Ação pendente`
2. Acknowledge the current state to the user in Portuguese
3. Orient the pending action directly — do NOT restart the intake flow
4. Return — Steps 1–5 below only apply to NEW cases

If the user describes a new movement (judge decision, defendant response, etc.):
- Do not start intake
- Apply `protocols/case-lifecycle.md` → State Detection rules
- Dispatch `/lawdog:movimentacao <case-slug>` to register the movement

If the user describes an existing case that was NOT opened through lawdog
("já tenho um processo em andamento", "tenho documentos do PROJUDI", wants
to organize ongoing case, etc.):
- Do NOT start intake
- Redirect to `/lawdog:importar-caso` to organize the existing case
- Say in Portuguese: "Parece que você já tem um processo em andamento. Vou
  te ajudar a organizar tudo. Use `/lawdog:importar-caso` ou me diga o que tem."

Only proceed to Step 1 if no `caso.md` exists or the user explicitly wants
to open a completely new case.

## Step 1 — Free Narrative

Invite the user to describe the problem in their own words. Do not interrupt or
present forms or questions. Let them finish their full account before responding.

## Step 2 — Triage

Research legal articles internally (knowledge/ or fetch-law) BEFORE responding.
Do NOT print article texts to the user during triage — that is internal work.

After the narrative, identify all of the following:

**2a. Case type** — classify as one of:
- Relação de consumo (consumidor vs. fornecedor)
- Inadimplemento contratual (breach of contract)
- Dano material (material damage)
- Dano moral (moral damage)
- Cobrança indevida (improper charges / harassment collection)
- Direito de vizinhança (neighbor disputes)
- Outro (describe)

**2b. User's state (estado)** — ask directly if not known from context.
This determines TJ URL, tracking portal, and local procedural rules.
Consult `knowledge/court-portals.md` for the state-to-portal mapping.

**2c. JEC eligibility** — determine if the case fits within JEC scope:
- Consult `knowledge/codigo-civil-jec.md` for Art. 3° of Lei 9.099/95
- If the minimum wage value may have changed: use `/lawdog:fetch-law Lei 9.099/95 Art. 3`
- NEVER hardcode the salário mínimo value (it changes annually)
- Also check Art. 9°: cases above 20 SM require a lawyer (advogado obrigatório)
- If case does NOT fit JEC: communicate clearly and orient alternatives
  (vara cível comum, PROCON, advogado particular)

**2d. Applicable code** — identify the primary legal basis:
- CC (Código Civil): general civil matters, contracts, torts, neighbor disputes
- CDC (Código de Defesa do Consumidor): any consumer/supplier relation
- Both CC and CDC when applicable (e.g., consumer contract breach)

**2e. Extrajudicial notification assessment** — before recommending to open a JEC case,
evaluate whether extrajudicial notification is appropriate. Read
`protocols/case-lifecycle.md` → "Extrajudicial Notification — When to Suggest"
for the criteria. If appropriate, present the option with full cost and timeline
information — but never impose it. The user decides.

**Triage output format** — present a concise analysis that:
- States the case type and applicable legal basis
- Cites relevant articles inline by number only (e.g., "Art. 1.277 CC")
- Highlights any critical nuances or weaknesses found during research
- States whether JEC applies (or why not), pending any missing info
- Does NOT print full article texts — offer them on request only:
  "Posso mostrar o texto completo dos artigos se quiser."
- Then immediately asks the first gap-filling question (Step 3)
- Ends with a **Referências** table listing every source consulted

**References table format** — always at the very end of the triage response:

```
**Referências**
| Artigo / Fonte | URL |
|---|---|
| Art. 1.277 — Código Civil | https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm |
| Art. 3° — Lei 9.099/95 (JEC) | https://www.planalto.gov.br/ccivil_03/leis/l9099.htm |
```

Rules for the references table:
- Include ONLY sources actually consulted for this triage (not all known articles)
- Always show the full URL — never a shortened or markdown-linked form, because
  in Claude Code (terminal) markdown links are not clickable; the raw URL is
- If the source came from WebSearch, use the URL of the result page, not the
  search query
- If the source is `knowledge/codigo-civil-jec.md` (embedded), use the
  corresponding planalto.gov.br URL listed at the top of that file

## Step 3 — Gap Filling

Identify what information is missing to evaluate the case. Ask ONE question
at a time and wait for the answer before deciding what to ask next.

Typical gaps to fill:
- **Requerente** (obrigatório pelo JEC): nome completo, CPF, endereço completo
  (logradouro, número, bairro, cidade, estado, CEP). Telefone e e-mail são
  opcionais — coletar se o usuário tiver, mas nunca bloquear por falta deles.
- **Requerido**: endereço é importante para citação judicial — oriente o usuário
  a levantar o endereço (site da empresa, nota fiscal, contrato, CNPJ na Receita).
  CPF/CNPJ do requerido é opcional mas inclua se disponível.
  Se o usuário não tiver o endereço do requerido: oriente como obtê-lo antes
  de distribuir, pois o juízo precisará citar a parte.
- Dates: when the problem started and key events in chronological order
- Values: damage amount, amounts paid, amounts owed
- Evidence: what the user has (receipts, NFs, photos, messages, contracts)

Lawdog knows JEC procedure — orient the user proactively about what is required,
what is optional, and what may block distribution if missing. Do not wait for the
user to ask.

Do not present a checklist. Converse naturally, one question at a time.

## Step 4 — Adversarial Simulation

Before recommending to proceed, mentally simulate the defendant's best defense:
- What arguments would a competent defense lawyer raise?
- What gaps or weaknesses in evidence does the case have?
- Would a judge consider this a strong and well-documented claim?

Present the honest assessment to the user. If the case is weak, say so and explain
specifically what would need to change for it to become viable. Never encourage a
weak case to avoid disappointing the user — that would waste the user's time and
the court's.

## Step 5 — Decision

Ask: "Com base no que analisamos, você deseja prosseguir e abrir o caso?"

**If yes:** trigger case directory creation per `protocols/file-structure.md`.

**If no:** summarize what would need to change for the case to become viable.
Leave the door open — the user can return with more evidence or a stronger claim.
