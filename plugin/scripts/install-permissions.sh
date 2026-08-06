#!/usr/bin/env bash
# Post-install hook for lawdog plugin.
# Handles assistant-specific setup after lola installs the module.
#
# Claude Code: writes .claude/settings.json with WebSearch/WebFetch permissions
# OpenCode:    patches opencode.json with "plugin" entry + writes AGENTS.md
#              template to LAWDOG_CASES_DIR if missing or containing stale paths
#
# Env vars provided by lola: LOLA_PROJECT_PATH, LOLA_ASSISTANT, LOLA_MODULE_NAME
set -euo pipefail

PROJECT_PATH="${LOLA_PROJECT_PATH:?LOLA_PROJECT_PATH not set}"

# ── Claude Code ────────────────────────────────────────────────────────────────
if [[ "${LOLA_ASSISTANT:-}" == "claude-code" ]]; then
    CLAUDE_DIR="$PROJECT_PATH/.claude"
    SETTINGS="$CLAUDE_DIR/settings.json"

    mkdir -p "$CLAUDE_DIR"

    # Use domain: format — NOT URL format (https://host/*) which Claude Code rejects
    PERMISSIONS_JSON='{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:www.planalto.gov.br)",
      "WebFetch(domain:www.tjpr.jus.br)",
      "WebFetch(domain:projudi.tjpr.jus.br)",
      "WebFetch(domain:legis.senado.leg.br)",
      "WebFetch(domain:www2.camara.leg.br)"
    ]
  }
}'

    if [[ ! -f "$SETTINGS" ]]; then
        printf '%s\n' "$PERMISSIONS_JSON" > "$SETTINGS"
        echo "lawdog: created $SETTINGS with WebSearch permissions"
    else
        python3 - <<PYEOF
import json, sys

new_entries = [
    "WebSearch",
    "WebFetch(domain:www.planalto.gov.br)",
    "WebFetch(domain:www.tjpr.jus.br)",
    "WebFetch(domain:projudi.tjpr.jus.br)",
    "WebFetch(domain:legis.senado.leg.br)",
    "WebFetch(domain:www2.camara.leg.br)",
]

# Also clean up any old URL-format entries that may have been installed previously
old_url_entries = [
    "WebFetch(https://www.planalto.gov.br/*)",
    "WebFetch(https://www.tjpr.jus.br/*)",
    "WebFetch(https://projudi.tjpr.jus.br/*)",
    "WebFetch(https://legis.senado.leg.br/*)",
    "WebFetch(https://www2.camara.leg.br/*)",
]

try:
    with open("$SETTINGS") as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    data = {}

perms = data.setdefault("permissions", {})
allow = perms.setdefault("allow", [])

# Remove old URL-format entries
allow[:] = [e for e in allow if e not in old_url_entries]

added = []
for entry in new_entries:
    if entry not in allow:
        allow.append(entry)
        added.append(entry)

with open("$SETTINGS", "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

if added:
    print(f"lawdog: merged {len(added)} permission(s) into $SETTINGS")
else:
    print("lawdog: permissions already present in $SETTINGS")
PYEOF
    fi
    exit 0
fi

# ── OpenCode ───────────────────────────────────────────────────────────────────
if [[ "${LOLA_ASSISTANT:-}" == "opencode" ]]; then
    MODULE_NAME="${LOLA_MODULE_NAME:-lawdog}"
    MODULE_DIR="${PROJECT_PATH}/.lola/modules/${MODULE_NAME}"
    OPENCODE_JSON="${PROJECT_PATH}/opencode.json"

    if [[ ! -d "$MODULE_DIR" ]]; then
        echo "lawdog: WARNING — module dir not found at .lola/modules/${MODULE_NAME}, skipping opencode.json patch"
        exit 0
    fi

    ABSOLUTE_MODULE="$(cd "$MODULE_DIR" && pwd)"

    # Patch opencode.json to register the plugin entry
    echo "lawdog: patching opencode.json with plugin entry..."
    python3 - <<PYEOF
import json, os

config_path = "$OPENCODE_JSON"
plugin_path = "$ABSOLUTE_MODULE"

if os.path.exists(config_path):
    try:
        with open(config_path) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = {}
else:
    data = {}

data.setdefault("\$schema", "https://opencode.ai/config.json")
plugins = data.setdefault("plugin", [])

if plugin_path not in plugins:
    plugins.append(plugin_path)
    print(f"lawdog: added plugin entry: {plugin_path}")
else:
    print(f"lawdog: plugin entry already present")

with open(config_path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF

    # Write AGENTS.md to LAWDOG_CASES_DIR if absent or contains stale hardcoded paths
    CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
    AGENTS_TARGET="${CASES_DIR}/AGENTS.md"
    AGENTS_TEMPLATE="${MODULE_DIR}/templates/lawdog-cases.AGENTS.md"

    if [[ ! -f "$AGENTS_TEMPLATE" ]]; then
        echo "lawdog: WARNING — template not found at ${MODULE_NAME}/templates/lawdog-cases.AGENTS.md"
        exit 0
    fi

    NEEDS_UPDATE=false
    if [[ ! -f "$AGENTS_TARGET" ]]; then
        NEEDS_UPDATE=true
        echo "lawdog: creating ${CASES_DIR}/AGENTS.md from template..."
    elif grep -qE '/home/[^/]+/dev/|/Users/[^/]+/dev/' "$AGENTS_TARGET" 2>/dev/null; then
        NEEDS_UPDATE=true
        echo "lawdog: ${CASES_DIR}/AGENTS.md has stale hardcoded path — replacing with template"
    fi

    if [[ "$NEEDS_UPDATE" == "true" ]]; then
        mkdir -p "$CASES_DIR"
        cp "$AGENTS_TEMPLATE" "$AGENTS_TARGET"
        echo "lawdog: wrote ${CASES_DIR}/AGENTS.md"
    else
        echo "lawdog: ${CASES_DIR}/AGENTS.md already up to date"
    fi

    exit 0
fi

# Unknown assistant — nothing to do
echo "lawdog: no post-install action for assistant '${LOLA_ASSISTANT:-unknown}'"
exit 0
