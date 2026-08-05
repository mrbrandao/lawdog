# Protocol: File Structure

> **SINGLE SOURCE OF TRUTH** — Any skill that creates or reads case files MUST
> import this protocol. NEVER hardcode paths anywhere else. All path logic lives
> here and only here.

## Base Directory

The root for all case files is controlled by the environment variable
`LAWDOG_CASES_DIR`. If the variable is not set, the default is `~/lawdog-cases`.

Resolve it with:

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
```

Never assume the path. Always resolve via this pattern before any file operation.

## Directory Tree

```
$LAWDOG_CASES_DIR/
└── <case-slug>/
    ├── caso.md                          # living case diary — updated each movement
    ├── 00a-notificacao-extrajudicial/   # optional: pre-judicial step
    │   └── docs/
    ├── 00b-contranotificacao-reu/       # optional: other party extrajudicial response
    │   └── docs/
    ├── 01-peticao-inicial/              # first filing by requerente
    │   ├── docs/
    │   ├── anexos/
    │   └── juntada/
    ├── 02-decisao-juiz/                 # any judge act (despacho, sentença, decisão)
    │   └── docs/                        # PDFs downloaded from PROJUDI
    ├── 03-manifestacao-reu/             # defendant/third party filing
    │   └── docs/
    ├── 04-peticao/                      # subsequent requerente filing
    │   ├── docs/
    │   ├── anexos/
    │   └── juntada/
    └── 05-decisao-juiz/
        └── docs/
```

### Movement type reference

| Prefix | Type slug | Actor | Has juntada? |
|---|---|---|---|
| 00a | `notificacao-extrajudicial` | Requerente | No |
| 00b+ | `contranotificacao-reu` | Requerido | No |
| 01 | `peticao-inicial` | Requerente | Yes |
| NN | `peticao` | Requerente | Yes |
| NN | `decisao-juiz` | Juiz | No |
| NN | `manifestacao-reu` | Requerido/advogado | No |
| NN | `intimacao` | Cartório/secretaria | No |

`NN` mirrors the PROJUDI sequence number when known.
Prefix `00x` (letters) marks the pre-judicial phase. Numbers from `01` mark the judicial phase.

## Naming Rules

- **case-slug**: kebab-case, lowercase, no accents, maximum 40 characters.
  Example: `dano-moral-operadora-fone-2024`
- **peticao-inicial**: always the name of the first petition. Never use
  `peticao-01` for the first filing.
- **peticao-N**: subsequent petitions use zero-padded two-digit numbers starting
  from `02` (e.g., `peticao-02`, `peticao-03`, ...).
- **caso.md**: updated at each stage of the case as new information is added or
  status changes.
- **anexos/**: present inside each petition directory to hold supporting documents
  (receipts, photos, screenshots, contracts, etc.).
- **docs/**: editable originals produced by lawdog (.md, .docx). Never deleted.
  Converted to PDF via doc2pdf when going to juntada/.
- **anexos/**: staging area. Any file goes here. After processing, original is
  tagged `.converted` suffix (e.g., `foto.jpg` → `foto.jpg.converted`). Never deleted.
  Script skips `.converted` files on re-run (idempotent).
- **juntada/**: final destination. Files named with sequential prefix `NN` or
  `NN.N` for thematic groups. Name conflict → suffix -1, -2 (kebab-case, no spaces).
- **LAWDOG_PDF_SIZE**: JEC size limit in bytes (default 4194304 = 4MB). Set in
  shell profile by setup.sh. All conversion scripts read this env var.
  Single change point: `export LAWDOG_PDF_SIZE=<bytes>` in profile.

## caso.md Template

Every case directory must contain a `caso.md` file initialized from this template:

```markdown
# Caso: <case-slug>

- **Aberto em:** YYYY-MM-DD
- **Estado-Comarca:** <estado> — <comarca>
- **Vara-Juizado:** <nome da vara ou juizado>

## Partes

**Requerente:** <nome completo>, portador do CPF: <000.000.000-00>, residente no endereço: <logradouro, número, complemento, bairro, cidade/UF, CEP>[, Telefone: <(XX) XXXXX-XXXX>][, E-mail: <email@exemplo.com>]

**Requerido:** <nome completo ou razão social>[, CPF/CNPJ: <documento>], endereço: <logradouro, número, bairro, cidade/UF>

Rules:
- Requerente: name, CPF, and full address are always required in JEC petitions.
  Omit Telefone and E-mail entirely if not provided — do not leave placeholders.
- Requerido: address is important (server of process); CPF/CNPJ is optional but
  include if known. Omit any field that is unknown — do not leave placeholders.
- Write each party as a single line. Do not use sub-bullets or multi-line format.

## Resumo

<two to four sentences describing what happened and what is being claimed>

## Fundamento jurídico

<primary legal basis: CC, CDC, or both — cite specific articles>

## Timeline

| Data | Evento |
|------|--------|
| YYYY-MM-DD | <event> |

## Evidências disponíveis

- [ ] <document or evidence item>

## Pontos fracos identificados

- <weakness or gap in the case>

## Petições

| # | Arquivo | Data | Status |
|---|---------|------|--------|
| 1 | peticao-inicial/ | YYYY-MM-DD | rascunho |

## Estado atual

- **Fase:** [pré-judicial | judicial | encerrado]
- **Última movimentação:** [NN-tipo — YYYY-MM-DD]
- **Prazo em curso:** [descrição do prazo e data limite | nenhum]
- **Ação pendente:** [o que o usuário deve fazer a seguir]

## Movimentações

| Seq | Diretório | Data | Tipo | Ator | Prazo |
|-----|-----------|------|------|------|-------|
| 01 | 01-peticao-inicial/ | YYYY-MM-DD | Petição inicial | Requerente | — |
```
