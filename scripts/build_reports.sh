#!/bin/bash

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
    cat <<'EOF'
Использование:
  ./scripts/build_reports.sh main
  ./scripts/build_reports.sh debag
  ./scripts/build_reports.sh all

Назначение:
  main   Собрать README.md, README_EN.md и tests/report/resources/*.png
  debag  Собрать debag/README.md, debag/README_EN.md и debag/reports/resources/*.png
  all    Собрать оба отчета
EOF
}

ensure_env() {
    if [ -f /.dockerenv ]; then
        PYTHON="${PYTHON:-python3}"
    else
        PYTHON="${PYTHON:-.venv/bin/python}"
        if [ ! -x "$PYTHON" ]; then
            python3 -m venv .venv
        fi
    fi

    if ! "$PYTHON" -c 'import matplotlib, nbconvert, numpy, pandas' 2>/dev/null; then
        "$PYTHON" -m pip install -r requirements.txt
    fi
}

build_main_report() {
    if [ ! -f tests/data/results.csv ]; then
        echo "Ошибка: нет tests/data/results.csv. Сначала запустите ./scripts/run_tests.sh -run -all" >&2
        exit 1
    fi

    "$PYTHON" scripts/render_charts.py main

    "$PYTHON" -m jupyter nbconvert --to markdown --no-input \
        --output report_ru.md --output-dir tests/report tests/report/report_ru.ipynb >/dev/null
    sed 's|(resources/|(tests/report/resources/|g' \
        tests/report/report_ru.md > README.md

    "$PYTHON" -m jupyter nbconvert --to markdown --no-input \
        --output report_en.md --output-dir tests/report tests/report/report_en.ipynb >/dev/null
    sed 's|(resources/|(tests/report/resources/|g' \
        tests/report/report_en.md > README_EN.md

    rm -f tests/report/report_ru.md tests/report/report_en.md
}

build_debag_report() {
    if [ ! -f debag/data/results_debag.csv ]; then
        echo "Ошибка: нет debag/data/results_debag.csv. Сначала запустите ./scripts/run_debag.sh" >&2
        exit 1
    fi

    "$PYTHON" scripts/render_charts.py debag

    "$PYTHON" -m jupyter nbconvert --to markdown --no-input \
        --output report_debag_ru.md --output-dir debag/reports \
        debag/reports/report_debag_ru.ipynb >/dev/null
    sed 's|(resources/|(reports/resources/|g' \
        debag/reports/report_debag_ru.md > debag/README.md

    "$PYTHON" -m jupyter nbconvert --to markdown --no-input \
        --output report_debag_en.md --output-dir debag/reports \
        debag/reports/report_debag_en.ipynb >/dev/null
    sed 's|(resources/|(reports/resources/|g' \
        debag/reports/report_debag_en.md > debag/README_EN.md

    rm -f debag/reports/report_debag_ru.md debag/reports/report_debag_en.md
    "$PYTHON" debag/verify_results.py --update-readme debag/data/results_debag.csv
}

if [ "$#" -ne 1 ]; then
    usage >&2
    exit 1
fi

ensure_env

case "$1" in
    main)
        build_main_report
        ;;
    debag)
        build_debag_report
        ;;
    all)
        build_main_report
        build_debag_report
        ;;
    -h|--help)
        usage
        ;;
    *)
        echo "Неизвестный отчет: $1" >&2
        usage >&2
        exit 1
        ;;
esac
