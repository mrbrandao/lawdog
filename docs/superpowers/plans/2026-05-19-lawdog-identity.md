# Lawdog Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish lawdog's initial identity layer: persona, protocol contracts, legal knowledge base, case management, and bootstrap script.

**Architecture:** Layered modularity — `AGENTS.md` defines who lawdog is (~80 lines); `protocols/` defines how lawdog acts (consumed selectively by skills); `knowledge/` provides verified legal content offline-first with fetch-on-demand fallback. Each skill is autonomous and declares only the protocols it needs — designed to map 1:1 to an autonomous agent when a multi-agent framework is chosen later.

**Tech Stack:** Bash (setup.sh, tests), Python 3 (SKILL.md validation), Make (test runner), Markdown (all content files), agentskills.io SKILL.md spec (skills), WebFetch (fetch-law).

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `Makefile` | `make test` entry point for all test suites |
| Create | `tests/validate_skill.py` | Validates SKILL.md frontmatter structure |
| Create | `tests/test_setup.sh` | Tests setup.sh behavior |
| Create | `plugin/scripts/setup.sh` | Bootstrap: LAWDOG_CASES_DIR + deps |
| Create | `plugin/protocols/case-intake.md` | Intake flow contract |
| Create | `plugin/protocols/file-structure.md` | Directory naming (single source of truth) |
| Create | `plugin/protocols/knowledge-sources.md` | Legal lookup order contract |
| Create | `plugin/knowledge/court-portals.md` | TJ/PROJUDI by state + navigation |
| Create | `plugin/knowledge/index.md` | Legal topic index |
| Create | `plugin/knowledge/codigo-civil-jec.md` | Verified article texts (CC + CDC + Lei 9.099) |
| Rewrite | `plugin/AGENTS.md` | Lawdog persona core |
| Create | `plugin/skills/fetch-law/SKILL.md` | Skill: fetch article from official source |
| Create | `plugin/skills/caso/SKILL.md` | Skill: full case intake + directory creation |
| Modify | `README.md` | Document new skills and structure |
| Modify | `plugin/.claude-plugin/plugin.json` | Version bump to 0.2.0 |

---

## Task 1: Test Infrastructure + Makefile

**Files:**
- Create: `Makefile`
- Create: `tests/validate_skill.py`
- Create: `tests/test_setup.sh`

- [ ] **Step 1.1: Create tests/ directory**

```bash
mkdir -p tests
```

- [ ] **Step 1.2: Write validate_skill.py**

Write `tests/validate_skill.py`:

```python
#!/usr/bin/env python3
"""Validate SKILL.md files against agentskills.io required structure.

Usage:
    python3 tests/validate_skill.py [path/to/SKILL.md ...]
    python3 tests/validate_skill.py --all          # validates all SKILL.md in plugin/
"""
import sys
import re
import os
from pathlib import Path

REQUIRED_FRONTMATTER_FIELDS = ['name', 'description', 'allowed-tools', 'metadata']
REQUIRED_METADATA_FIELDS = ['author', 'version']
REQUIRED_SECTIONS = ['## Trigger', '## Fluxo']

PASS = 0
FAIL = 1


def extract_frontmatter(content: str) -> str | None:
    """Return the raw YAML frontmatter block, or None if absent."""
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    return match.group(1) if match else None


def check_frontmatter_fields(frontmatter: str, filepath: str) -> list[str]:
    """Return list of error messages for missing frontmatter fields."""
    errors = []
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if f'{field}:' not in frontmatter:
            errors.append(f"Missing frontmatter field: '{field}'")
    for field in REQUIRED_METADATA_FIELDS:
        if f'  {field}:' not in frontmatter and f'\n{field}:' not in frontmatter:
            errors.append(f"Missing metadata sub-field: '{field}'")
    return errors


def check_required_sections(content: str) -> list[str]:
    """Return list of error messages for missing required markdown sections."""
    errors = []
    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing section: '{section}'")
    return errors


def validate_file(filepath: str) -> int:
    """Validate a single SKILL.md. Returns PASS (0) or FAIL (1)."""
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  FAIL [{filepath}]: file not found")
        return FAIL

    errors = []

    frontmatter = extract_frontmatter(content)
    if frontmatter is None:
        errors.append("No YAML frontmatter (--- ... ---) found")
    else:
        errors.extend(check_frontmatter_fields(frontmatter, filepath))

    errors.extend(check_required_sections(content))

    if errors:
        for err in errors:
            print(f"  FAIL [{filepath}]: {err}")
        return FAIL

    print(f"  PASS [{filepath}]")
    return PASS


def find_all_skill_files(root: str = 'plugin/skills') -> list[str]:
    """Recursively find all SKILL.md files under root."""
    return [str(p) for p in Path(root).rglob('SKILL.md')]


def run(paths: list[str]) -> int:
    """Validate all given paths. Returns exit code (0 = all pass)."""
    total = len(paths)
    failures = sum(validate_file(p) for p in paths)
    passed = total - failures
    print(f"\nResults: {passed}/{total} passed")
    return 0 if failures == 0 else 1


def main() -> None:
    args = sys.argv[1:]

    if '--all' in args:
        paths = find_all_skill_files()
        if not paths:
            print("No SKILL.md files found under plugin/skills/")
            sys.exit(1)
    elif args:
        paths = args
    else:
        print("Usage: validate_skill.py [path ...] | --all")
        sys.exit(1)

    print(f"Validating {len(paths)} SKILL.md file(s)...")
    sys.exit(run(paths))


if __name__ == '__main__':
    main()
```

- [ ] **Step 1.3: Write test_setup.sh**

Write `tests/test_setup.sh`:

```bash
#!/usr/bin/env bash
# Tests for plugin/scripts/setup.sh
# Usage: bash tests/test_setup.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETUP_SCRIPT="$SCRIPT_DIR/../plugin/scripts/setup.sh"
PASS_COUNT=0
FAIL_COUNT=0

# ── helpers ────────────────────────────────────────────────────────────────

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

run_setup() {
    # $1 = stdin input (empty string = Enter/default)
    local input="$1"
    echo "$input" | bash "$SETUP_SCRIPT" >/dev/null 2>&1
}

assert_dir_exists() {
    local dir="$1" label="$2"
    [ -d "$dir" ] && pass "$label" || fail "$label (dir not found: $dir)"
}

assert_file_contains() {
    local file="$1" pattern="$2" label="$3"
    grep -q "$pattern" "$file" 2>/dev/null && pass "$label" || fail "$label (pattern not in $file)"
}

assert_count_le() {
    local file="$1" pattern="$2" max="$3" label="$4"
    local count
    count=$(grep -c "$pattern" "$file" 2>/dev/null || echo 0)
    [ "$count" -le "$max" ] && pass "$label" || fail "$label (count=$count, max=$max)"
}

# ── setup ──────────────────────────────────────────────────────────────────

TMPDIR_TEST="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR_TEST"; }
trap cleanup EXIT
export HOME="$TMPDIR_TEST"

# ── tests ──────────────────────────────────────────────────────────────────

echo "Running setup.sh tests..."

# Test 1: Default (empty input) creates ~/lawdog-cases
run_setup ""
assert_dir_exists "$TMPDIR_TEST/lawdog-cases" "default input creates ~/lawdog-cases"

# Test 2: Custom absolute path is created
CUSTOM_DIR="$TMPDIR_TEST/my-legal-cases"
run_setup "$CUSTOM_DIR"
assert_dir_exists "$CUSTOM_DIR" "custom path is created"

# Test 3: LAWDOG_CASES_DIR is written to shell profile
run_setup ""
PROFILE=""
if [ -f "$TMPDIR_TEST/.zshrc" ]; then PROFILE="$TMPDIR_TEST/.zshrc"
elif [ -f "$TMPDIR_TEST/.bashrc" ]; then PROFILE="$TMPDIR_TEST/.bashrc"
fi
[ -n "$PROFILE" ] && assert_file_contains "$PROFILE" "LAWDOG_CASES_DIR" \
    "LAWDOG_CASES_DIR exported to shell profile" || \
    fail "No shell profile created"

# Test 4: Script is idempotent — no duplicate exports
run_setup ""
run_setup ""
PROFILE=""
if [ -f "$TMPDIR_TEST/.zshrc" ]; then PROFILE="$TMPDIR_TEST/.zshrc"
elif [ -f "$TMPDIR_TEST/.bashrc" ]; then PROFILE="$TMPDIR_TEST/.bashrc"
fi
[ -n "$PROFILE" ] && assert_count_le "$PROFILE" "LAWDOG_CASES_DIR" 1 \
    "idempotent: no duplicate LAWDOG_CASES_DIR in profile" || \
    fail "No shell profile found for idempotency check"

# Test 5: Tilde expansion — ~/custom becomes absolute path
run_setup "~/lawdog-alt"
assert_dir_exists "$TMPDIR_TEST/lawdog-alt" "tilde expansion works"

# ── summary ────────────────────────────────────────────────────────────────

echo ""
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
```

- [ ] **Step 1.4: Write Makefile**

Write `Makefile`:

```makefile
.PHONY: test test-skills test-setup

# Run all test suites
test: test-skills test-setup
	@echo ""
	@echo "All test suites passed."

# Validate all SKILL.md files against agentskills.io spec
test-skills:
	@echo "=== Validating SKILL.md files ==="
	@python3 tests/validate_skill.py --all

# Test bootstrap script behavior
test-setup:
	@echo "=== Testing setup.sh ==="
	@bash tests/test_setup.sh
```

- [ ] **Step 1.5: Run validator against existing video2forum skill (smoke test)**

```bash
python3 tests/validate_skill.py plugin/skills/video2forum/SKILL.md
```

Expected: `PASS [plugin/skills/video2forum/SKILL.md]`

- [ ] **Step 1.6: Run `make test-skills` (will include only video2forum for now)**

```bash
make test-skills
```

Expected: 1/1 passed.

- [ ] **Step 1.7: Run `make test-setup` (will fail — setup.sh doesn't exist yet)**

```bash
make test-setup 2>&1 | head -5
```

Expected: error. This is correct — confirms TDD baseline before implementation.

- [ ] **Step 1.8: Commit**

```bash
git add Makefile tests/
git commit -m "test: add Makefile + SKILL.md validator + setup.sh test suite"
```

---

## Task 2: Bootstrap Script

**Files:**
- Create: `plugin/scripts/setup.sh`

- [ ] **Step 2.1: Create scripts directory**

```bash
mkdir -p plugin/scripts
```

- [ ] **Step 2.2: Write setup.sh**

Write `plugin/scripts/setup.sh`:

```bash
#!/usr/bin/env bash
# Lawdog plugin bootstrap — configures LAWDOG_CASES_DIR and validates dependencies
set -euo pipefail

DEFAULT_DIR="$HOME/lawdog-cases"

# ── helpers ────────────────────────────────────────────────────────────────

print_header() { echo "=== $* ==="; }
print_ok()     { echo "✓ $*"; }
print_warn()   { echo "⚠  $*"; }

detect_profile() {
    if [ -f "$HOME/.zshrc" ]; then echo "$HOME/.zshrc"
    else echo "$HOME/.bashrc"
    fi
}

expand_tilde() {
    # Replace leading ~ with $HOME (handles cases where read gives literal ~)
    echo "${1/#\~/$HOME}"
}

read_cases_dir() {
    echo "Onde o lawdog deve salvar os arquivos dos casos?"
    echo "Pressione Enter para usar o padrão: $DEFAULT_DIR"
    printf "> "
    read -r INPUT
    if [ -z "$INPUT" ]; then
        echo "$DEFAULT_DIR"
    else
        expand_tilde "$INPUT"
    fi
}

write_to_profile() {
    local profile="$1"
    local cases_dir="$2"

    # Remove existing line (idempotent)
    if grep -q "LAWDOG_CASES_DIR" "$profile" 2>/dev/null; then
        sed -i '/LAWDOG_CASES_DIR/d' "$profile"
    fi

    echo "export LAWDOG_CASES_DIR=\"$cases_dir\"" >> "$profile"
}

check_ffmpeg() {
    if command -v ffmpeg >/dev/null 2>&1 || [ -n "${FFMPEG:-}" ]; then
        print_ok "ffmpeg encontrado"
    else
        print_warn "ffmpeg não encontrado. /lawdog:video2forum não funcionará."
        print_warn "Instale em: https://www.ffmpeg.org/download.html"
    fi
}

# ── main ───────────────────────────────────────────────────────────────────

print_header "Lawdog Plugin Setup"
echo ""

CASES_DIR="$(read_cases_dir)"

echo ""
echo "Criando $CASES_DIR..."
mkdir -p "$CASES_DIR"

PROFILE="$(detect_profile)"
write_to_profile "$PROFILE" "$CASES_DIR"

check_ffmpeg

echo ""
print_header "Setup concluído"
echo "LAWDOG_CASES_DIR=$CASES_DIR"
echo "Perfil atualizado: $PROFILE"
echo ""
echo "Recarregue o shell ou execute: source $PROFILE"
```

- [ ] **Step 2.3: Make executable and lint with shellcheck**

```bash
chmod +x plugin/scripts/setup.sh
shellcheck plugin/scripts/setup.sh
```

Expected: no output (no errors).

If shellcheck is not installed:
```bash
# Fedora/RHEL
sudo dnf install ShellCheck
# Ubuntu/Debian
sudo apt-get install shellcheck
# macOS
brew install shellcheck
```

- [ ] **Step 2.4: Run `make test-setup`**

```bash
make test-setup
```

Expected:
```
=== Testing setup.sh ===
Running setup.sh tests...
  PASS: default input creates ~/lawdog-cases
  PASS: custom path is created
  PASS: LAWDOG_CASES_DIR exported to shell profile
  PASS: idempotent: no duplicate LAWDOG_CASES_DIR in profile
  PASS: tilde expansion works

Results: 5 passed, 0 failed
```

- [ ] **Step 2.5: Run full `make test`**

```bash
make test
```

Expected: all pass.

- [ ] **Step 2.6: Commit**

```bash
git add plugin/scripts/setup.sh
git commit -m "feat(setup): add bootstrap script with LAWDOG_CASES_DIR config"
```

---

## Task 3: Protocol — Case Intake

**Files:**
- Create: `plugin/protocols/case-intake.md`

- [ ] **Step 3.1: Create protocols directory**

```bash
mkdir -p plugin/protocols
```

- [ ] **Step 3.2: Write case-intake.md**

Write `plugin/protocols/case-intake.md`:

```markdown
# Protocol: Case Intake

Import this protocol in `/lawdog:caso`. Defines the full intake flow.

## Step 1 — Free Narrative

Invite the user to describe the problem in their own words. Do not interrupt or
present forms or questions. Let them finish their full account before responding.

## Step 2 — Triage

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

## Step 3 — Gap Filling

Identify what information is missing to evaluate the case. Ask ONE question
at a time and wait for the answer before deciding what to ask next.

Typical gaps to fill:
- Parties: full name and CPF/CNPJ of the defendant
- Dates: when the problem started and key events in chronological order
- Values: damage amount, amounts paid, amounts owed
- Evidence: what the user has (receipts, NFs, photos, messages, contracts)

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
```

- [ ] **Step 3.3: Verify required steps present**

```bash
for step in "Step 1" "Step 2" "Step 3" "Step 4" "Step 5"; do
    grep -q "## $step" plugin/protocols/case-intake.md && \
        echo "  PASS: $step" || echo "  FAIL: $step missing"
done
grep -q "NEVER hardcode" plugin/protocols/case-intake.md && \
    echo "  PASS: value limit constraint" || echo "  FAIL: value limit constraint missing"
```

Expected: 6 PASS lines.

- [ ] **Step 3.4: Commit**

```bash
git add plugin/protocols/case-intake.md
git commit -m "feat(protocols): add case-intake protocol"
```

---

## Task 4: Protocol — File Structure

**Files:**
- Create: `plugin/protocols/file-structure.md`

- [ ] **Step 4.1: Write file-structure.md**

Write `plugin/protocols/file-structure.md`:

````markdown
# Protocol: File Structure

SINGLE SOURCE OF TRUTH for lawdog case directory and file naming conventions.

Any skill that creates or reads case files MUST import this protocol.
Never hardcode paths or filenames — always derive from this document.

## Environment Variable

```
LAWDOG_CASES_DIR    # Root directory for all cases
                    # Default: ~/lawdog-cases
                    # Set by scripts/setup.sh on plugin install
```

## Resolving LAWDOG_CASES_DIR

Always use this pattern in any shell command that references the cases root:

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
```

## Directory Tree

```
$LAWDOG_CASES_DIR/
└── <case-slug>/
    ├── caso.md
    ├── peticao-inicial/
    │   ├── peticao-inicial.pdf
    │   └── anexos/
    ├── peticao-02/
    │   ├── peticao-02.pdf
    │   └── anexos/
    └── peticao-N/
        ├── peticao-N.pdf
        └── anexos/
```

## Naming Rules

**`<case-slug>`**: kebab-case derived from the case subject.
- Lowercase only. No accents (transliterate: ã→a, ç→c, é→e, ó→o, etc.).
- Spaces → hyphens. Max 40 characters.
- Examples: `obra-irregular`, `atraso-entrega-produto`, `cobranca-indevida-telefone`

**`peticao-inicial/`**: always the first petition directory. Never `peticao-01`.

**`peticao-N/`**: N is zero-padded two digits starting at 02.
- Examples: `peticao-02`, `peticao-03`, `peticao-10`

**`caso.md`**: summary file at the case root. Updated by lawdog at each case stage.

**`anexos/`**: evidence and attachments directory inside each petition directory.

## caso.md Template

```markdown
# Caso: <case-slug>

**Aberto em:** YYYY-MM-DD
**Estado/Comarca:** [estado] / [comarca]
**Vara/Juizado:** [when known, else: a definir]

## Partes

- **Requerente:** [nome completo, CPF]
- **Requerido:** [nome completo ou razão social, CPF/CNPJ]

## Resumo

[2-3 sentences describing the problem and what the user is seeking]

## Fundamento jurídico

- [Applicable: CC Art. N — description]
- [Applicable: CDC Art. N — description]
- [Applicable: Lei 9.099/95 Art. N — description]

## Timeline

- YYYY-MM-DD: [event]
- YYYY-MM-DD: [event]

## Evidências disponíveis

- [list of confirmed evidence the user has]

## Pontos fracos identificados

[Specific weaknesses surfaced during adversarial simulation]

## Petições

| Petição | Data | Descrição |
|---|---|---|
| peticao-inicial | YYYY-MM-DD | Petição inicial |
```
````

- [ ] **Step 4.2: Verify key constraints present**

```bash
grep -q "SINGLE SOURCE OF TRUTH" plugin/protocols/file-structure.md && \
    echo "  PASS: source constraint"
grep -q 'LAWDOG_CASES_DIR:-' plugin/protocols/file-structure.md && \
    echo "  PASS: fallback pattern"
grep -q "peticao-inicial" plugin/protocols/file-structure.md && \
    echo "  PASS: naming convention"
grep -q "caso.md Template" plugin/protocols/file-structure.md && \
    echo "  PASS: template present"
```

Expected: 4 PASS lines.

- [ ] **Step 4.3: Commit**

```bash
git add plugin/protocols/file-structure.md
git commit -m "feat(protocols): add file-structure protocol (single source of truth)"
```

---

## Task 5: Protocol — Knowledge Sources

**Files:**
- Create: `plugin/protocols/knowledge-sources.md`

- [ ] **Step 5.1: Write knowledge-sources.md**

Write `plugin/protocols/knowledge-sources.md`:

```markdown
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
```

- [ ] **Step 5.2: Verify file**

```bash
grep -q "Mandatory Lookup Order" plugin/protocols/knowledge-sources.md && \
    echo "  PASS: lookup order"
grep -q "NEVER" plugin/protocols/knowledge-sources.md && \
    echo "  PASS: constraints"
grep -q "Citation Format" plugin/protocols/knowledge-sources.md && \
    echo "  PASS: citation format"
```

Expected: 3 PASS lines.

- [ ] **Step 5.3: Commit**

```bash
git add plugin/protocols/knowledge-sources.md
git commit -m "feat(protocols): add knowledge-sources protocol"
```

---

## Task 6: Knowledge — Court Portals

**Files:**
- Create: `plugin/knowledge/court-portals.md`

- [ ] **Step 6.1: Create knowledge directory**

```bash
mkdir -p plugin/knowledge
```

- [ ] **Step 6.2: Write court-portals.md**

Write `plugin/knowledge/court-portals.md`:

```markdown
# Court Portals by State

Maps each state to its TJ, case tracking portal, and JEC access flow.
Read this file during case intake (Step 2b) to orient the user on their
specific court system.

## Paraná (PR)

**Tribunal de Justiça:** https://www.tjpr.jus.br/
**Acompanhamento de processos (PROJUDI):** https://projudi.tjpr.jus.br/projudi/
**Formulário JEC (distribuição):** https://www.tjpr.jus.br/formulario-virtual-juizados-especiais

### Como orientar o usuário (PR)

1. Acesse o formulário virtual do JEC no link acima
2. Selecione a **Comarca** (ex: Curitiba, Londrina, Maringá, Ponta Grossa)
3. Selecione a **Vara ou Juizado Especial** da comarca
4. Preencha e distribua a petição inicial pelo sistema online

Para acompanhar um processo já distribuído:
- Acesse o PROJUDI: https://projudi.tjpr.jus.br/projudi/
- Faça login com usuário e senha cadastrados, ou consulte por número do processo
  (consulta pública, sem login)

### Notas (PR)

- PROJUDI é o sistema eletrônico do TJPR — todos os atos processuais passam por ele
- Petições, anexos e intimações são enviados e recebidos pelo PROJUDI
- Vídeos de evidência devem estar em formato WebM — use `/lawdog:video2forum`
- Cada nova juntada gera um novo protocolo sequencial no PROJUDI

---

## Como adicionar outros estados

Para adicionar um estado, use o seguinte template:

```markdown
## [Estado por extenso] ([UF])

**Tribunal de Justiça:** [URL do TJ]
**Acompanhamento de processos:** [URL do portal]
**Formulário JEC:** [URL do formulário, se disponível online]

### Como orientar o usuário ([UF])

[passo a passo de distribuição e acompanhamento específico do estado]

### Notas ([UF])

[sistema usado, prazos específicos, observações relevantes]
```

Estados prioritários para implementação futura (por volume de causas JEC):
SP (e-SAJ/ESAJ), RJ (e-proc TJRJ), MG (SIMBA TJMG), RS (Themis/SAJ TJRS).
```

- [ ] **Step 6.3: Verify**

```bash
grep -q "projudi.tjpr.jus.br" plugin/knowledge/court-portals.md && \
    echo "  PASS: PROJUDI URL"
grep -q "tjpr.jus.br/formulario" plugin/knowledge/court-portals.md && \
    echo "  PASS: JEC form URL"
grep -q "Como adicionar outros estados" plugin/knowledge/court-portals.md && \
    echo "  PASS: extensibility template"
```

Expected: 3 PASS lines.

- [ ] **Step 6.4: Commit**

```bash
git add plugin/knowledge/court-portals.md
git commit -m "feat(knowledge): add court-portals with TJPR/PROJUDI navigation"
```

---

## Task 7: Knowledge — Legal Articles + Index

**Files:**
- Create: `plugin/knowledge/codigo-civil-jec.md`
- Create: `plugin/knowledge/index.md`

- [ ] **Step 7.1: Write codigo-civil-jec.md**

Texts verified via planalto.gov.br on 2026-05-19.

Write `plugin/knowledge/codigo-civil-jec.md`:

```markdown
# Artigos Críticos para JEC

Textos verificados via planalto.gov.br. Data de verificação: 2026-05-19.
Quando houver dúvida de atualização, use `/lawdog:fetch-law` para reconfirmar.

Fonte CC:  https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm
Fonte CDC: https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm
Fonte JEC: https://www.planalto.gov.br/ccivil_03/leis/l9099.htm

---

## Código Civil (Lei nº 10.406/2002)

### Responsabilidade Civil Extracontratual

**Art. 186.**
Aquele que, por ação ou omissão voluntária, negligência ou imprudência, violar
direito e causar dano a outrem, ainda que exclusivamente moral, comete ato ilícito.

**Art. 187.**
Também comete ato ilícito o titular de um direito que, ao exercê-lo, excede
manifestamente os limites impostos pelo seu fim econômico ou social, pela boa-fé
ou pelos bons costumes.

**Art. 927.**
Aquele que, por ato ilícito (arts. 186 e 187), causar dano a outrem, fica obrigado
a repará-lo.

Parágrafo único. Haverá obrigação de reparar o dano, independentemente de culpa,
nos casos especificados em lei, ou quando a atividade normalmente desenvolvida pelo
autor do dano implicar, por sua natureza, risco para os direitos de outrem.

**Art. 944.**
A indenização mede-se pela extensão do dano.

Parágrafo único. Se houver excessiva desproporção entre a gravidade da culpa e o
dano, poderá o juiz reduzir, equitativamente, a indenização.

### Responsabilidade Contratual

**Art. 389.**
Não cumprida a obrigação, responde o devedor por perdas e danos, mais juros e
atualização monetária segundo índices oficiais regularmente estabelecidos, e
honorários de advogado.

**Art. 421.**
A liberdade contratual será exercida nos limites da função social do contrato.
*(Redação dada pela Lei nº 13.874/2019)*

Parágrafo único. Nas relações contratuais privadas, prevalecerão o princípio da
intervenção mínima e a excepcionalidade da revisão contratual.

**Art. 422.**
Os contratantes são obrigados a guardar, assim na conclusão do contrato, como em
sua execução, os princípios de probidade e boa-fé.

**Art. 475.**
A parte lesada pelo inadimplemento pode pedir a resolução do contrato, se não
preferir exigir-lhe o cumprimento, cabendo, em qualquer dos casos, indenização por
perdas e danos.

---

## Código de Defesa do Consumidor (Lei nº 8.078/1990)

**Art. 2°.**
Consumidor é toda pessoa física ou jurídica que adquire ou utiliza produto ou
serviço como destinatário final.

Parágrafo único. Equipara-se a consumidor a coletividade de pessoas, ainda que
indetermináveis, que haja intervindo nas relações de consumo.

**Art. 3°.**
Fornecedor é toda pessoa física ou jurídica, pública ou privada, nacional ou
estrangeira, bem como os entes despersonalizados, que desenvolvem atividade de
produção, montagem, criação, construção, transformação, importação, exportação,
distribuição ou comercialização de produtos ou prestação de serviços.

**Art. 6°.** São direitos básicos do consumidor:
- I – a proteção da vida, saúde e segurança contra riscos de produtos e serviços
  perigosos ou nocivos;
- II – a educação e divulgação sobre o consumo adequado dos produtos e serviços;
- III – a informação adequada e clara sobre os diferentes produtos e serviços,
  com especificação correta de quantidade, características, composição, qualidade
  e preço, bem como sobre os riscos que apresentem;
- IV – a proteção contra publicidade enganosa e abusiva, métodos comerciais
  coercitivos ou desleais, bem como contra práticas e cláusulas abusivas ou
  impostas no fornecimento de produtos e serviços;
- V – a modificação das cláusulas contratuais que estabeleçam prestações
  desproporcionais ou sua revisão em razão de fatos supervenientes que as tornem
  excessivamente onerosas;
- VI – a efetiva prevenção e reparação de danos patrimoniais e morais,
  individuais, coletivos e difusos;
- VII – o acesso aos órgãos judiciários e administrativos com vistas à prevenção
  ou reparação de danos patrimoniais e morais, individuais, coletivos ou difusos,
  assegurada a proteção jurídica, administrativa e técnica aos necessitados;
- VIII – a facilitação da defesa de seus direitos, inclusive com a inversão do
  ônus da prova, a seu favor, no processo civil, quando, a critério do juiz, for
  verossímil a alegação ou quando for ele hipossuficiente, segundo as regras
  ordinárias de experiências.

**Art. 42.**
Na cobrança de débitos, o consumidor inadimplente não será exposto a ridículo,
nem será submetido a qualquer tipo de constrangimento ou ameaça.

Parágrafo único. O consumidor cobrado em quantia indevida tem direito à repetição
do indébito, por valor igual ao dobro do que pagou em excesso, acrescido de
correção monetária e juros legais, salvo hipótese de engano justificável.

---

## Lei nº 9.099, de 26 de setembro de 1995 (JEC)

**Art. 3°.**
O Juizado Especial Cível tem competência para conciliação, processo e julgamento
das causas cíveis de menor complexidade, assim consideradas:
- I – as causas cujo valor não exceda a quarenta vezes o salário mínimo;
- II – as enumeradas no art. 275, inciso II, do Código de Processo Civil;
- IV – as ações possessórias sobre bens imóveis de valor não excedente ao fixado
  no inciso I deste artigo.

§ 1° Compete ao Juizado Especial promover a execução dos títulos executivos
extrajudiciais, no valor de até quarenta vezes o salário mínimo, observado o
disposto no § 1° do art. 8° desta Lei.

§ 2° Ficam excluídas da competência do Juizado Especial as causas de natureza
alimentar, falimentar, fiscal e de interesse da Fazenda Pública, e também as
relativas a acidentes de trabalho, resíduos e ao estado e capacidade das pessoas,
ainda que de cunho patrimonial.

§ 3° A opção pelo procedimento previsto nesta Lei importará em renúncia ao crédito
excedente ao limite estabelecido neste artigo, excetuada a hipótese de conciliação.

> ⚠️ "Quarenta vezes o salário mínimo" muda a cada reajuste do SM.
> Para o valor atual em reais: use `/lawdog:fetch-law Lei 9.099/95 Art. 3`
> ou multiplique o SM vigente por 40. Nunca hardcode o valor em reais.

**Art. 9°.**
Nas causas de valor até vinte salários mínimos, as partes comparecerão
pessoalmente, podendo ser assistidas por advogado; nas de valor superior, a
assistência é obrigatória.

§ 1° Sendo facultativa a assistência, se uma das partes comparecer assistida por
advogado, ou se o réu for pessoa jurídica ou firma individual, terá a outra parte,
se quiser, assistência judiciária prestada por órgão instituído junto ao Juizado
Especial, na forma da lei local.

§ 2° O Juizado Especial, a requerimento do interessado, poderá designar advogado
na hipótese prevista no § 1° deste artigo.
```

- [ ] **Step 7.2: Write index.md**

Write `plugin/knowledge/index.md`:

```markdown
# Knowledge Base Index

Indexed by legal topic. Check this index FIRST before reading any article file.
Articles marked `fetch-law` are not embedded — use `/lawdog:fetch-law` to retrieve them.

## Responsabilidade Civil (Extracontratual)

| Tema | Lei | Artigo | Arquivo |
|---|---|---|---|
| Ato ilícito (culpa/dolo) | CC | Art. 186 | codigo-civil-jec.md |
| Abuso de direito | CC | Art. 187 | codigo-civil-jec.md |
| Obrigação de indenizar | CC | Art. 927 | codigo-civil-jec.md |
| Extensão da indenização | CC | Art. 944 | codigo-civil-jec.md |

## Responsabilidade Contratual

| Tema | Lei | Artigo | Arquivo |
|---|---|---|---|
| Perdas e danos por inadimplemento | CC | Art. 389 | codigo-civil-jec.md |
| Função social do contrato | CC | Art. 421 | codigo-civil-jec.md |
| Boa-fé objetiva | CC | Art. 422 | codigo-civil-jec.md |
| Resolução por inadimplemento | CC | Art. 475 | codigo-civil-jec.md |

## Relações de Consumo (CDC)

| Tema | Lei | Artigo | Arquivo |
|---|---|---|---|
| Conceito de consumidor | CDC | Art. 2° | codigo-civil-jec.md |
| Conceito de fornecedor | CDC | Art. 3° | codigo-civil-jec.md |
| Direitos básicos do consumidor | CDC | Art. 6° | codigo-civil-jec.md |
| Vícios de qualidade dos produtos | CDC | Art. 18 | fetch-law |
| Vícios de qualidade dos serviços | CDC | Art. 20 | fetch-law |
| Cobrança indevida / repetição indébito | CDC | Art. 42 | codigo-civil-jec.md |
| Cláusulas abusivas | CDC | Art. 51 | fetch-law |

## JEC — Competência e Procedimento

| Tema | Lei | Artigo | Arquivo |
|---|---|---|---|
| Competência / valor limite (40 SM) | Lei 9.099/95 | Art. 3° | codigo-civil-jec.md |
| Partes que podem propor ação | Lei 9.099/95 | Art. 8° | fetch-law |
| Advogado obrigatório acima de 20 SM | Lei 9.099/95 | Art. 9° | codigo-civil-jec.md |
```

- [ ] **Step 7.3: Verify key articles present**

```bash
for art in "Art. 186" "Art. 927" "Art. 389" "Art. 422" "Art. 42" "Art. 3°"; do
    grep -q "$art" plugin/knowledge/codigo-civil-jec.md && \
        echo "  PASS: $art" || echo "  FAIL: $art missing"
done
grep -q "⚠️" plugin/knowledge/codigo-civil-jec.md && \
    echo "  PASS: SM warning" || echo "  FAIL: SM warning missing"
grep -q "fetch-law" plugin/knowledge/index.md && \
    echo "  PASS: index references fetch-law" || echo "  FAIL: fetch-law ref missing"
```

Expected: 8 PASS lines.

- [ ] **Step 7.4: Commit**

```bash
git add plugin/knowledge/
git commit -m "feat(knowledge): add verified legal articles (CC, CDC, Lei 9.099) + index"
```

---

## Task 8: Rewrite AGENTS.md

**Files:**
- Rewrite: `plugin/AGENTS.md`

- [ ] **Step 8.1: Check current line count**

```bash
wc -l plugin/AGENTS.md
```

Note current count. The new version must stay ≤ 80 lines.

- [ ] **Step 8.2: Rewrite AGENTS.md**

Write `plugin/AGENTS.md` (complete replacement):

```markdown
# Lawdog — Advogado Especialista em Direito Civil Brasileiro

## Identidade

Você é o Lawdog: advogado especializado no Código Civil brasileiro com histórico
como juiz substituto. Conhece como magistrados pensam, avaliam provas e decidem —
especialmente no JEC (Juizado Especial Cível).

## Postura

- Educado, direto, realista. Nunca condescendente.
- Nunca cita artigo ou precedente de memória — verifica primeiro via `knowledge/`
  ou `/lawdog:fetch-law`. Se não encontrar: diz que precisa verificar antes de afirmar.
- Se o caso não tem fundamento jurídico sólido, diz claramente. Não existe para
  lotar varas com causas sem mérito: existe para criar processos que valem a pena.

## Raciocínio Adversarial

Antes de declarar um caso viável, simula internamente a defesa da parte contrária.
Apresenta os pontos fracos que um juiz provavelmente notará. Só recomenda avançar
se o caso resiste ao contraditório.

## Limites

- Não garante resultado.
- Não substitui advogado em casos que excedem o JEC ou envolvem complexidade fora
  do seu escopo — quando isso ocorre, orienta o usuário a buscar um advogado e
  explica por quê.

## Idioma

Responde em português por padrão. Segue o idioma do usuário se diferente.

## Conhecimento Jurídico

Cobre: Código Civil (CC), CPC no que tange ao JEC, CDC quando relevante.
Para qualquer artigo ou regra, segue a ordem em `protocols/knowledge-sources.md`:

1. Consulta `knowledge/index.md` pelo tema
2. Lê o artigo em `knowledge/codigo-civil-jec.md` se presente
3. Se precisar de texto atualizado ou artigo não embarcado: aciona `/lawdog:fetch-law`
4. Nunca cita de memória sem verificar

## Protocolo de Atendimento

Ao receber um problema jurídico, segue o fluxo em `protocols/case-intake.md`:
narrativa livre → triagem (tipo, estado, JEC eligibility) → lacunas (uma por vez)
→ simulação adversarial → decisão do usuário → abertura do caso.

## Estrutura de Arquivos

Ao abrir um caso: segue `protocols/file-structure.md`.
Raiz dos casos: `$LAWDOG_CASES_DIR` (default `~/lawdog-cases`, configurado via
`plugin/scripts/setup.sh`).

## Skills Disponíveis

- `/lawdog:caso` — intake completo e abertura de caso
- `/lawdog:fetch-law` — busca artigo atualizado em fonte oficial
- `/lawdog:video2forum` — converte vídeos para WebM (PROJUDI/TJPR)
```

- [ ] **Step 8.3: Verify line count and required sections**

```bash
echo "Line count: $(wc -l < plugin/AGENTS.md)"
for section in "Identidade" "Postura" "Raciocínio Adversarial" "Limites" \
               "Conhecimento Jurídico" "Protocolo de Atendimento"; do
    grep -q "$section" plugin/AGENTS.md && \
        echo "  PASS: $section" || echo "  FAIL: $section missing"
done
grep -q "protocols/case-intake.md" plugin/AGENTS.md && \
    echo "  PASS: protocol ref" || echo "  FAIL: protocol ref missing"
grep -q "Nunca cita" plugin/AGENTS.md && \
    echo "  PASS: no-hallucination rule" || echo "  FAIL: no-hallucination rule missing"
```

Expected: line count ≤ 80; 8 PASS lines.

- [ ] **Step 8.4: Commit**

```bash
git add plugin/AGENTS.md
git commit -m "feat(identity): rewrite AGENTS.md with full lawdog persona"
```

---

## Task 9: Skill — fetch-law

**Files:**
- Create: `plugin/skills/fetch-law/SKILL.md`

- [ ] **Step 9.1: Create skill directory**

```bash
mkdir -p plugin/skills/fetch-law
```

- [ ] **Step 9.2: Confirm validator fails on missing file**

```bash
python3 tests/validate_skill.py plugin/skills/fetch-law/SKILL.md 2>&1 | head -2
```

Expected: FAIL (file not found). TDD baseline confirmed.

- [ ] **Step 9.3: Write fetch-law SKILL.md**

Write `plugin/skills/fetch-law/SKILL.md`:

```markdown
---
name: fetch-law
description: >-
  Busca texto atualizado de artigos jurídicos em fontes oficiais
  (planalto.gov.br, TJ do estado). Usada internamente por outras skills
  quando knowledge/ não tem o artigo ou pode estar desatualizado.
  Ativar em: /lawdog:fetch-law, buscar artigo, verificar lei atualizada,
  texto oficial da lei.
compatibility: >-
  Requer conexão com internet. Fontes federais: planalto.gov.br.
  Fontes estaduais: TJ do estado identificado no caso.
allowed-tools: WebFetch
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolo importado

- `protocols/knowledge-sources.md`

## Trigger

Acionada por `/lawdog:caso` ou outra skill quando precisam de texto atualizado.
Usuário pode invocar diretamente: `/lawdog:fetch-law <norma> <artigo>`

Exemplos:
- `/lawdog:fetch-law Lei 9.099/95 Art. 3`
- `/lawdog:fetch-law CDC Art. 42`
- `/lawdog:fetch-law Código Civil Art. 927`

## Fluxo

1. Identifique a norma e o artigo solicitado
2. Selecione a URL na tabela de fontes abaixo
3. Faça WebFetch na URL
4. Extraia o texto do artigo específico (número exato, com parágrafos e incisos)
5. Retorne no formato de output abaixo

Se o artigo não for encontrado na URL principal:
- Tente https://www.planalto.gov.br/legislacao buscando pela lei
- Se ainda não encontrar: informe o usuário e sugira busca manual
- Nunca invente o conteúdo do artigo

## Fontes por norma

| Norma | URL |
|---|---|
| Código Civil (Lei 10.406/2002) | https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm |
| CDC (Lei 8.078/1990) | https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm |
| Lei 9.099/1995 (JEC) | https://www.planalto.gov.br/ccivil_03/leis/l9099.htm |
| Legislação federal geral | https://www.planalto.gov.br/legislacao |

## Output

```
**Art. [N] — [Nome da Lei]**

[texto completo do artigo, incluindo parágrafos e incisos]

Fonte: [URL]
Verificado em: [YYYY-MM-DD]
```
```

- [ ] **Step 9.4: Validate**

```bash
python3 tests/validate_skill.py plugin/skills/fetch-law/SKILL.md
```

Expected: `PASS [plugin/skills/fetch-law/SKILL.md]`

- [ ] **Step 9.5: Commit**

```bash
git add plugin/skills/fetch-law/
git commit -m "feat(skills): add fetch-law skill for official legal text retrieval"
```

---

## Task 10: Skill — caso

**Files:**
- Create: `plugin/skills/caso/SKILL.md`

- [ ] **Step 10.1: Create skill directory**

```bash
mkdir -p plugin/skills/caso
```

- [ ] **Step 10.2: Confirm validator fails on missing file**

```bash
python3 tests/validate_skill.py plugin/skills/caso/SKILL.md 2>&1 | head -2
```

Expected: FAIL. TDD baseline confirmed.

- [ ] **Step 10.3: Write caso SKILL.md**

Write `plugin/skills/caso/SKILL.md`:

```markdown
---
name: caso
description: >-
  Inicia e gerencia um caso no JEC. Conduz o intake completo do usuário
  (narrativa livre → triagem → lacunas → simulação adversarial → abertura),
  cria a estrutura de diretórios do caso e gera caso.md com o resumo inicial.
  Ativar em: /lawdog:caso, abrir caso, iniciar processo, tenho um problema
  jurídico, quero processar alguém, preciso entrar com uma ação.
compatibility: >-
  Usa LAWDOG_CASES_DIR se definido; fallback: ~/lawdog-cases.
  Configurar com plugin/scripts/setup.sh.
allowed-tools: Bash, Read, Write, WebFetch
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolos importados

- `protocols/case-intake.md` — fluxo completo de atendimento
- `protocols/file-structure.md` — convenção de diretórios (fonte única)
- `protocols/knowledge-sources.md` — como acessar artigos jurídicos
- `knowledge/court-portals.md` — TJ/PROJUDI por estado

## Trigger

Usuário descreve um problema jurídico ou invoca `/lawdog:caso`.

## Fluxo

Siga cada etapa de `protocols/case-intake.md` na ordem:

### Etapa 1 — Narrativa livre

Convide o usuário a descrever o problema com suas próprias palavras.
Não interrompa com formulários ou perguntas. Deixe terminar.

### Etapa 2 — Triagem

Identifique: tipo do caso, estado do usuário (consulte `knowledge/court-portals.md`),
se cabe no JEC (consulte `knowledge/codigo-civil-jec.md` → Art. 3° Lei 9.099/95;
nunca hardcode o valor em reais), código aplicável (CC, CDC, ou ambos).

Se o caso não couber no JEC: comunique claramente e oriente alternativas.
Encerre a skill — não abra estrutura de diretórios para casos fora do escopo.

### Etapa 3 — Lacunas

Pergunte o que falta para avaliar o caso: partes, datas, valores, evidências.
UMA pergunta por vez. Aguarde a resposta antes de perguntar a próxima.

### Etapa 4 — Simulação adversarial

Simule internamente a defesa da parte contrária. Apresente os pontos fracos
ao usuário com honestidade. Se o caso for fraco, diga e explique o que mudaria.

### Etapa 5 — Decisão e abertura

Pergunte: "Com base no que analisamos, você deseja prosseguir e abrir o caso?"

**Se sim:**

1. Resolva LAWDOG_CASES_DIR:

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
```

2. Gere o `<case-slug>` em kebab-case a partir do tema (ex: `obra-irregular`).
   Regras completas em `protocols/file-structure.md`: lowercase, sem acentos, max 40 chars.

3. Crie a estrutura de diretórios:

```bash
mkdir -p "$CASES_DIR/<case-slug>/peticao-inicial/anexos"
```

4. Gere `caso.md` usando o template em `protocols/file-structure.md`.
   Preencha: partes, estado/comarca, fundamento jurídico (artigos verificados),
   timeline, evidências disponíveis, pontos fracos da simulação adversarial.

5. Escreva o arquivo em `$CASES_DIR/<case-slug>/caso.md`.

6. Informe o path completo ao usuário e oriente o próximo passo:
   - Consulte `knowledge/court-portals.md` para acesso ao JEC do estado
   - Se tiver vídeos como evidência: use `/lawdog:video2forum` para converter

**Se não:** resuma o que precisaria mudar para o caso se tornar viável.

## Orientação ao portal

Após abrir o caso, consulte `knowledge/court-portals.md` para o estado do usuário
e oriente passo a passo: como acessar o JEC, selecionar comarca e vara, e
distribuir a petição inicial quando chegar esse momento.
```

- [ ] **Step 10.4: Validate**

```bash
python3 tests/validate_skill.py plugin/skills/caso/SKILL.md
```

Expected: `PASS [plugin/skills/caso/SKILL.md]`

- [ ] **Step 10.5: Run make test-skills (all three skills)**

```bash
make test-skills
```

Expected:
```
Validating 3 SKILL.md file(s)...
  PASS [plugin/skills/caso/SKILL.md]
  PASS [plugin/skills/fetch-law/SKILL.md]
  PASS [plugin/skills/video2forum/SKILL.md]

Results: 3/3 passed
```

- [ ] **Step 10.6: Commit**

```bash
git add plugin/skills/caso/
git commit -m "feat(skills): add caso skill for JEC case intake and management"
```

---

## Task 11: Update README and plugin.json

**Files:**
- Modify: `README.md`
- Modify: `plugin/.claude-plugin/plugin.json`

- [ ] **Step 11.1: Bump version in plugin.json**

In `plugin/.claude-plugin/plugin.json`, change `"version": "0.1.0"` to `"version": "0.2.0"`.

- [ ] **Step 11.2: Replace ## Skills section in README.md**

Replace the existing `## Skills` section with:

```markdown
## Skills

### `caso`

Opens and manages a JEC case. Conducts the full intake flow (free narrative →
triage → gap filling → adversarial simulation), creates the case directory
structure, and generates `caso.md` with the initial case summary.

```
/lawdog:caso
```

**Requires:** `LAWDOG_CASES_DIR` set. Run `bash plugin/scripts/setup.sh` on first install.

---

### `fetch-law`

Fetches the current official text of a legal article from planalto.gov.br or
the relevant TJ. Used internally by other skills; can also be invoked directly.

```
/lawdog:fetch-law Lei 9.099/95 Art. 3
/lawdog:fetch-law CDC Art. 42
/lawdog:fetch-law Código Civil Art. 927
```

---

### `video2forum`

Converts video evidence (.MOV, .MP4, .AVI, .MKV, etc.) to WebM — the format
accepted by PROJUDI/TJPR for evidence uploads.

```
/lawdog:video2forum ~/docs/case/*.MOV
```

**Requirements:** `ffmpeg` in PATH, or set `FFMPEG=/path/to/ffmpeg`.
```

- [ ] **Step 11.3: Replace ## Plugin structure section in README.md**

Replace the existing `## Plugin structure` section with:

```markdown
## Plugin structure

```
lawdog/
├── plugin/
│   ├── .claude-plugin/
│   │   └── plugin.json             # Claude Code plugin manifest
│   ├── AGENTS.md                   # Lawdog persona core
│   ├── protocols/
│   │   ├── case-intake.md          # Intake flow contract
│   │   ├── file-structure.md       # Directory naming (single source of truth)
│   │   └── knowledge-sources.md    # Legal lookup order contract
│   ├── knowledge/
│   │   ├── index.md                # Legal topic index
│   │   ├── codigo-civil-jec.md     # Verified articles (CC + CDC + Lei 9.099/95)
│   │   └── court-portals.md        # TJ/PROJUDI by state + navigation
│   ├── skills/
│   │   ├── caso/
│   │   │   └── SKILL.md
│   │   ├── fetch-law/
│   │   │   └── SKILL.md
│   │   └── video2forum/
│   │       ├── SKILL.md
│   │       └── scripts/
│   │           └── video2forum.sh
│   └── scripts/
│       └── setup.sh                # Bootstrap: LAWDOG_CASES_DIR + deps
├── tests/
│   ├── validate_skill.py           # SKILL.md structure validator
│   └── test_setup.sh               # setup.sh behavior tests
├── Makefile                        # make test entry point
└── README.md
```
```

- [ ] **Step 11.4: Verify version bump**

```bash
grep '"version"' plugin/.claude-plugin/plugin.json
```

Expected: `"version": "0.2.0"`

- [ ] **Step 11.5: Commit**

```bash
git add README.md plugin/.claude-plugin/plugin.json
git commit -m "docs: update README and bump version to 0.2.0"
```

---

## Task 12: Final Verification

- [ ] **Step 12.1: Run full test suite**

```bash
make test
```

Expected:
```
=== Validating SKILL.md files ===
Validating 3 SKILL.md file(s)...
  PASS [plugin/skills/caso/SKILL.md]
  PASS [plugin/skills/fetch-law/SKILL.md]
  PASS [plugin/skills/video2forum/SKILL.md]

Results: 3/3 passed
=== Testing setup.sh ===
Running setup.sh tests...
  PASS: default input creates ~/lawdog-cases
  PASS: custom path is created
  PASS: LAWDOG_CASES_DIR exported to shell profile
  PASS: idempotent: no duplicate LAWDOG_CASES_DIR in profile
  PASS: tilde expansion works

Results: 5 passed, 0 failed

All test suites passed.
```

- [ ] **Step 12.2: Verify all required files exist**

```bash
FILES=(
    plugin/AGENTS.md
    plugin/protocols/case-intake.md
    plugin/protocols/file-structure.md
    plugin/protocols/knowledge-sources.md
    plugin/knowledge/index.md
    plugin/knowledge/codigo-civil-jec.md
    plugin/knowledge/court-portals.md
    plugin/skills/caso/SKILL.md
    plugin/skills/fetch-law/SKILL.md
    plugin/scripts/setup.sh
    Makefile
    tests/validate_skill.py
    tests/test_setup.sh
)
for f in "${FILES[@]}"; do
    [ -f "$f" ] && echo "  PASS: $f" || echo "  FAIL: $f missing"
done
```

Expected: 13 PASS lines.

- [ ] **Step 12.3: Verify no hardcoded salário mínimo values in skills or protocols**

```bash
grep -r "60\.720\|60720\|1\.518\|1518\|1\.412\|1412" \
    plugin/skills/ plugin/protocols/ && \
    echo "FAIL: hardcoded SM value found" || \
    echo "  PASS: no hardcoded SM values"
```

Expected: `PASS: no hardcoded SM values`

- [ ] **Step 12.4: Verify AGENTS.md line count**

```bash
COUNT=$(wc -l < plugin/AGENTS.md)
[ "$COUNT" -le 80 ] && echo "  PASS: AGENTS.md is $COUNT lines (≤80)" || \
    echo "  FAIL: AGENTS.md is $COUNT lines (>80)"
```

Expected: PASS.

- [ ] **Step 12.5: Final commit if any loose files**

```bash
git status --short
```

If output is empty: all done. If any modified/untracked files remain, add and commit them with an appropriate message.
