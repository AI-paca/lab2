#!/bin/bash

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATA_DIR="debag/data"

if [ -f /.dockerenv ]; then
    PYTHON="python3"
else
    PYTHON=".venv/bin/python"
    if [ ! -x "$PYTHON" ]; then
        python3 -m venv .venv
    fi
    if ! "$PYTHON" -c 'import matplotlib, nbconvert, numpy, pandas' 2>/dev/null; then
        .venv/bin/pip install -r requirements.txt
    fi
fi

cleanup_generated_data() {
    rm -f "$DATA_DIR"/*.csv tests/data/test_data.json
}
trap cleanup_generated_data EXIT

mkdir -p tests/data
"$PYTHON" tests/generate_data.py >/dev/null

mapfile -t algorithms < <(
    find debag/algorithms -maxdepth 1 -type f -name 'fake_*.py' -print | sort
)

if [ "${#algorithms[@]}" -eq 0 ]; then
    echo "Ошибка: контрольные алгоритмы debag не найдены." >&2
    exit 1
fi

mkdir -p "$DATA_DIR"
rm -f "$DATA_DIR"/results_fake_*.csv "$DATA_DIR/results_debag.csv"

echo "Запуск контрольных замеров debag..."
BENCHMARK_RESULTS_DIR="$DATA_DIR" timeout 1200 \
    "$PYTHON" tests/run_test.py "${algorithms[@]}" >/dev/null

first=1
for file in "$DATA_DIR"/results_fake_*.csv; do
    if [ "$first" -eq 1 ]; then
        cat "$file" > "$DATA_DIR/results_debag.csv"
        first=0
    else
        tail -n +2 "$file" >> "$DATA_DIR/results_debag.csv"
    fi
done

echo "Обновление графиков и README debag..."
PYTHON="$PYTHON" ./scripts/build_reports.sh debag
