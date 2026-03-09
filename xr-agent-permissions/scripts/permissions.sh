#!/bin/sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/permissions.py" "$@"
elif command -v python >/dev/null 2>&1; then
  python "$SCRIPT_DIR/permissions.py" "$@"
else
  echo "Error: python3 or python is required" >&2
  exit 1
fi
