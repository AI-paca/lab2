#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
    cat <<'EOF'
Использование:
  ./scripts/release.sh          Выполнить полный цикл релиза
  ./scripts/release.sh -h       Показать справку

Отдельные этапы:
  ./scripts/run_debag.sh       Проверить устойчивость замеров и обновить debag/README.md
  ./scripts/run_tests.sh -run -all
                              Запустить основные тесты и обновить README.md
  ./scripts/build_reports.sh   Собрать README и ресурсы отчётов из временных CSV
  ./scripts/create_archive.sh Создать release.zip
  ./scripts/build_docker.sh   Собрать локальный Docker-образ

Полный цикл дополнительно собирает локальный Docker-образ lab2:latest.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

if [ "$#" -ne 0 ]; then
    echo "Неизвестный аргумент: $1" >&2
    usage >&2
    exit 1
fi

./scripts/run_debag.sh
./scripts/run_tests.sh -run -all
./scripts/create_archive.sh
./scripts/build_docker.sh

echo "Полный цикл релиза завершён."
