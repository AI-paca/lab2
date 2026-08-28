#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

archive_name="${1:-release.zip}"
rm -f "$archive_name"

zip -r "$archive_name" . \
    -x ".venv" ".venv/*" \
    -x ".git" ".git/*" \
    -x ".env" \
    -x ".vscode" ".vscode/*" \
    -x "tests/data" "tests/data/*" \
    -x "debag/data" "debag/data/*" \
    -x "tests/report/*_files" "tests/report/*_files/*" \
    -x "debag/reports/*_files" "debag/reports/*_files/*" \
    -x "*.pyc" \
    -x "__pycache__/*" \
    -x "*/__pycache__/*" \
    -x ".pytest_cache/*" \
    -x "*.egg-info/*" \
    -x "*.zip" \
    -x "*.docx" \
    -x "*.tar.gz" \
    -x "*.pdf"

echo "Архив создан: $archive_name"
