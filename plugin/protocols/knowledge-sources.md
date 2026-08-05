# Protocol: Knowledge Sources

Defines how lawdog accesses and cites legal knowledge.
Import this in any skill that needs to reference law.

## Mandatory Lookup Order

1. Check `knowledge/index.md` for the topic
2. Read the article in `knowledge/codigo-civil-jec.md` if present
3. If text is outdated or article is not embedded: invoke `/lawdog:fetch-law <artigo>`
4. If nothing found anywhere: state "preciso verificar esse artigo antes de citar"

NEVER skip to step 3 before checking steps 1 and 2.
NEVER cite from memory — always verify, even for well-known articles.

## Citation Format

When citing a verified article, always include the source:

```
Art. [N] do [Código ou Lei] — [texto do artigo]
(Fonte: [URL], verificado em [YYYY-MM-DD])
```

## When to Use fetch-law

- The embedded knowledge file does not have the article
- The case involves an area not covered by `knowledge/codigo-civil-jec.md`
- You need to verify a value that may have changed (salário mínimo, JEC thresholds)
- The user explicitly requests the current official text

## Never Do This

- Cite an article number without verifying its text first
- Assume a value limit (JEC threshold, salário mínimo) is current without checking
- Invent article content because it "seems right"
- Say "approximately" when citing article text — cite exactly or not at all
