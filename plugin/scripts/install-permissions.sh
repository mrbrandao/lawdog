#!/usr/bin/env bash
# Post-install hook for lawdog plugin.
# Writes .claude/settings.json to the target project so Claude Code
# does not prompt for permission on every WebSearch/WebFetch call.
#
# Only runs when the target assistant is claude-code.
# Env vars provided by lola: LOLA_PROJECT_PATH, LOLA_ASSISTANT, LOLA_MODULE_NAME
set -euo pipefail

# Only configure Claude Code — other assistants use their own mechanisms
if [[ "${LOLA_ASSISTANT:-}" != "claude-code" ]]; then
    exit 0
fi

PROJECT_PATH="${LOLA_PROJECT_PATH:?LOLA_PROJECT_PATH not set}"
CLAUDE_DIR="$PROJECT_PATH/.claude"
SETTINGS="$CLAUDE_DIR/settings.json"

mkdir -p "$CLAUDE_DIR"

PERMISSIONS_JSON='{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(https://www.planalto.gov.br/*)",
      "WebFetch(https://www.tjpr.jus.br/*)",
      "WebFetch(https://projudi.tjpr.jus.br/*)",
      "WebFetch(https://legis.senado.leg.br/*)",
      "WebFetch(https://www2.camara.leg.br/*)"
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
