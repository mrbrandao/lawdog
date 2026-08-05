# Protocol: Case Lifecycle

Import this protocol in `/lawdog:caso` and `/lawdog:movimentacao`.
Governs how case movements flow from pre-judicial through full JEC lifecycle.

## Extrajudicial Notification — When to Suggest

Suggest extrajudicial notification ONLY when ALL of the following apply:
- The relationship is still viable (recent issue, not already escalated)
- The defendant is identified and reachable (known address/contact)
- The dispute value justifies the cost (rule of thumb: cost < 20% of dispute value)
- There is a realistic chance of amicable resolution

**Never suggest** when: conflict is already irreconcilable, defendant is
unknown or unresponsive to informal contact, or value is too low relative to cost.

### What to inform the user before suggesting

Always state the following upfront — no surprises:

- **Cost:** R$180–250 at a Cartório de Títulos e Documentos (most legally solid,
  creates public record); or R$30–50 via Correios with Aviso de Recebimento (AR);
  or a certified digital platform with ICP-Brasil timestamp (lower cost, growing
  judicial acceptance)
- **Timeline:** 15–30 days is a reasonable response window. There is no fixed
  legal deadline — the notifying party sets the term.
- **Legal effects:**
  - Constitutes the party in mora (Art. 397, CC) — formal notice of default
  - Interrupts prescription (resets the statute of limitations clock)
  - Creates a formal record of good faith attempt
  - Does NOT compel response (silence is not legal default in itself)
  - Does NOT replace judicial process — it is a pre-step
- **JEC does not require prior notification.** It is a strategic choice that
  often strengthens the case and demonstrates good faith to the judge.
- **Legal basis:** Lei 6.015/73 (Art. 160), CC Art. 397, CPC Art. 726

### If the other party sends a contranotificação

Read the document. Evaluate whether it:
- **Resolves the issue:** the other party agrees and proposes remedy → advise user
  to assess the offer and whether it is satisfactory
- **Disputes the facts:** contains legal arguments → note as defense preview;
  advise proceeding to JEC with this as context
- **Is purely delaying:** formulaic rejection without substance → advise proceeding
  to JEC, noting the 15-business-day response window (CPC analogy)

## Movement Registration

When a new movement is received (PDF from PROJUDI or user description):

1. Determine the type from content: `decisao-juiz`, `manifestacao-reu`,
   `intimacao`, `peticao`, or `contranotificacao-reu`

2. **Determine the directory name — CRITICAL RULE:**
   - **ALWAYS use `{SEQ}-{tipo}/`** where SEQ is the PROJUDI sequence number
   - If the PROJUDI seq number is known (from the PDF header, user, or PROJUDI history): use it exactly
   - If unknown: use the next integer after the highest existing seq in `caso.md`
   - **NEVER use descriptive names** like `decisao-emenda/` or `habilitacao-requerida/`
   - Each PROJUDI movement gets its OWN directory — never group multiple seqs together
   - Type slugs: `decisao-juiz`, `peticao`, `manifestacao-reu`, `intimacao`
   - Example: seq 9 judge decision → `09-decisao-juiz/`, seq 20 defendant → `20-manifestacao-reu/`

3. Create the directory: `{SEQ}-{tipo}/docs/` (add `anexos/` and `juntada/` only
   for `peticao` type)
4. Copy or move the PDF to `{SEQ}-{tipo}/docs/`
5. Add a row to `caso.md` Movimentações table
6. Update `caso.md` Estado atual: fase, última movimentação, prazo, ação pendente

## Orientation by Movement Type

### `decisao-juiz`
1. Read the PDF
2. Identify what the judge is requesting or deciding:
   - **Emenda à inicial:** judge requests changes to the initial petition —
     user has the stated deadline to refile (typically 5-15 business days)
   - **Citação/intimação:** other party is being notified — await their response
   - **Decisão de mérito:** judge rules on the substance — evaluate and advise
     on appeal options if unfavorable
   - **Despacho de diligência:** judge requests additional documents —
     identify what is needed and how to obtain it
3. State the legal deadline clearly and what happens if missed
4. Draft the response strategy

### `manifestacao-reu`
1. Read the PDF — identify the defense arguments
2. Evaluate strength: are the facts disputed? Is there legal basis?
3. Identify the strongest defense points that need rebuttal in the next petition
4. Advise on whether a new petition is needed and what it should address

### `intimacao`
1. Read the PDF — identify whether it is a citation (citação) or intimation
2. State the mandatory deadline (improrrogável — cannot be extended)
3. State the exact next required action (appear at hearing, submit document, etc.)

### `contranotificacao-reu` (extrajudicial phase)
Apply the guidance in "If the other party sends a contranotificação" above.

## State Detection (for /lawdog:caso)

When the user describes a case event in natural conversation:

1. Read `caso.md` → confirm case exists → read `Estado atual`
2. Classify what the user described as a movement type
3. Create directory: `NN-tipo/docs/`
4. If user provides a file path: copy to `NN-tipo/docs/`
5. Call `/lawdog:movimentacao <case-slug>` internally
6. Update `caso.md`

**Graceful fallback** — if any step fails, tell the user explicitly:
> "Pode colocar o arquivo em `<full-path>/<NN-tipo>/docs/` e me avisar quando
> estiver lá? Depois é só me contar o que aconteceu ou chamar
> `/lawdog:movimentacao <case-slug>`."

Never leave the user without a clear next action.

## Resuming an Existing Case

When `/lawdog:caso` is invoked and `caso.md` already has content:
1. Read `Estado atual.Ação pendente`
2. Acknowledge the current state in Portuguese
3. Orient the pending action — do NOT restart intake
4. Only start a new intake flow if the case does not exist yet
