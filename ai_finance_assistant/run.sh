#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/.venv/bin/streamlit" run "$SCRIPT_DIR/src/web_app/app.py" "$@"
