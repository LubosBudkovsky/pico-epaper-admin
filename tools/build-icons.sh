#!/usr/bin/env bash
# Generate Bootstrap Icon font modules from tools/icons.json.
#
# Usage:
#   ./tools/build-icons.sh
#
# To add/remove icons or change sizes, edit tools/icons.json and re-run.
# For a one-off explicit run: ./tools/build-icons.sh --icons alarm wifi --sizes 24

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

cd "$ROOT"

# Activate .venv if present (font_to_py installed there by convention)
if [[ -f ".venv/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source ".venv/bin/activate"
fi

python3 tools/lib/gen_icons.py "$@"
