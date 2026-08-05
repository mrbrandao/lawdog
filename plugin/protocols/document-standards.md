# Protocol: Document Standards

Import this protocol in any skill that produces judicial documents.

## Required Petition Structure

Documents must follow this order — no deviations:
1. **Dos Fatos** — facts in chronological order, no embellishment
2. **Do Direito** — legal basis: verified articles cited inline as `(CC, Art. 927)`
3. **Dos Pedidos** — numbered list, one request per line

No introduction. No "portanto" conclusion restating what was already said.

## Writing Rules

- One idea per paragraph. Split if it exceeds 6 lines.
- No filler phrases: "É de notório conhecimento que...", "Ante o exposto..."
- No repetition between paragraphs. Every sentence adds information.
- Active voice. Passive only when the agent is genuinely unknown.
- No AI slop: no hollow affirmations, no padding.

## Typographic Rules (enforced by base-legal.latex)

- No decorative separators (`---`, `***`, horizontal rules).
- No blank pages — a blank page is a typographic failure.
- Signature block (city + date + name) must stay on the same page as the
  last paragraph body. Never isolated on its own page.
- No orphaned lines: a single line alone at the top of a page is unacceptable.
  LaTeX widow/orphan penalties in base-legal.latex handle this automatically.

## What a Judge Appreciates

- The request is clear by the end of page one.
- Damages are proportional and documented.
- Each exhibit is referenced in the text where it matters.
- A well-argued 3-page petition beats a 15-page one.
