#!/bin/bash

set -e
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RUNNER_PATH="${RUNNER_PATH:-tests/run_test.py}"

usage() {
    cat <<'EOF'
Использование:
  ./scripts/run_tests.sh -h
  ./scripts/run_tests.sh -list
  ./scripts/run_tests.sh -run -all
  ./scripts/run_tests.sh -run

Опции:
  -h            Показать эту справку
  -list         Показать список найденных алгоритмов
  -run -all     Запустить бенчмарк всех алгоритмов и обновить отчет
  -run          Открыть меню выбора (1,2, 1-3, 1,3-n), затем обновить отчет

Примечание:
  Путь к Python-раннеру можно переопределить переменной RUNNER_PATH.
  По умолчанию: tests/run_test.py
EOF
}

ensure_env() {
    if [ -f /.dockerenv ]; then
        PYTHON="python3"
        return
    fi
    PYTHON=".venv/bin/python"
    if [ ! -x "$PYTHON" ]; then
        python3 -m venv .venv
    fi
    if ! "$PYTHON" -c 'import matplotlib, nbconvert, numpy, pandas' 2>/dev/null; then
        .venv/bin/pip install -r requirements.txt
    fi
}

require_runner() {
    if [ ! -f "$RUNNER_PATH" ]; then
        echo "Ошибка: Python-раннер не найден: $RUNNER_PATH" >&2
        exit 1
    fi
}

regenerate_test_data() {
    echo "Перегенерация тестовых данных..."
    "$PYTHON" tests/generate_data.py >/dev/null
}

clean_data_dir() {
    local data_dir="tests/data"
    mkdir -p "$data_dir"
    rm -f "$data_dir"/*.csv "$data_dir"/test_data.json
}

get_algorithms() {
    find algorithms -maxdepth 1 -type f -name 'algo_*.py' -printf '%f\n' | sort | sed 's/\.py$//'
}

run_python_benchmarks() {
    local selected_csv="$1"
    local args=()
    local algo
    IFS=',' read -r -a algos <<<"$selected_csv"
    for algo in "${algos[@]}"; do
        args+=("algorithms/${algo}.py")
    done
    timeout 1200 "$PYTHON" "$RUNNER_PATH" "${args[@]}" >/dev/null
}

print_algorithms() {
    mapfile -t algorithms < <(get_algorithms)

    if [ "${#algorithms[@]}" -eq 0 ]; then
        echo "Алгоритмы не найдены." >&2
        exit 1
    fi

    echo "Найденные алгоритмы:" >&2
    for i in "${!algorithms[@]}"; do
        idx=$((i + 1))
        echo "  -$idx  ${algorithms[$i]}" >&2
    done
}

parse_selection() {
    local input="$1"
    local max="$2"
    local token
    local start
    local end
    local start_raw
    local end_raw
    local n
    local ordered=()
    declare -A seen=()

    input="${input// /}"
    if [ -z "$input" ]; then
        echo "Ошибка: пустой ввод." >&2
        return 1
    fi

    IFS=',' read -r -a tokens <<<"$input"
    for token in "${tokens[@]}"; do
        if [[ "$token" =~ ^[0-9]+$ ]]; then
            n="$token"
            if [ "$n" -lt 1 ] || [ "$n" -gt "$max" ]; then
                echo "Ошибка: номер $n вне диапазона 1-$max." >&2
                return 1
            fi
            if [ -z "${seen[$n]:-}" ]; then
                seen[$n]=1
                ordered+=("$n")
            fi
        elif [[ "$token" =~ ^([0-9]+|[nN])-([0-9]+|[nN])$ ]]; then
            start_raw="${BASH_REMATCH[1]}"
            end_raw="${BASH_REMATCH[2]}"
            if [[ "$start_raw" =~ ^[nN]$ ]]; then
                start="$max"
            else
                start="$start_raw"
            fi
            if [[ "$end_raw" =~ ^[nN]$ ]]; then
                end="$max"
            else
                end="$end_raw"
            fi
            if [ "$start" -gt "$end" ]; then
                echo "Ошибка: диапазон $token задан в обратном порядке." >&2
                return 1
            fi
            if [ "$start" -lt 1 ] || [ "$end" -gt "$max" ]; then
                echo "Ошибка: диапазон $token вне 1-$max." >&2
                return 1
            fi
            for ((n=start; n<=end; n++)); do
                if [ -z "${seen[$n]:-}" ]; then
                    seen[$n]=1
                    ordered+=("$n")
                fi
            done
        else
            echo "Ошибка: неверный формат '$token'. Используйте 2 или 1-3 или 1,3-n." >&2
            return 1
        fi
    done

    printf "%s\n" "${ordered[@]}"
}

run_interactive() {
    mapfile -t algorithms < <(get_algorithms)

    if [ "${#algorithms[@]}" -eq 0 ]; then
        echo "Алгоритмы не найдены." >&2
        exit 1
    fi

    echo "Выберите алгоритм для запуска:" >&2
    for i in "${!algorithms[@]}"; do
        idx=$((i + 1))
        echo "  $idx) ${algorithms[$i]}" >&2
    done

    read -r -p "Введите выбор (пример: 2 или 1-3 или 1,3-n): " choice
    mapfile -t indices < <(parse_selection "$choice" "${#algorithms[@]}")

    if [ "${#indices[@]}" -eq 0 ]; then
        echo "Ошибка: не выбрано ни одного алгоритма." >&2
        exit 1
    fi

    selected_algorithms=()
    for idx in "${indices[@]}"; do
        selected_algorithms+=("${algorithms[$((idx - 1))]}")
    done

    printf "%s\n" "${selected_algorithms[@]}"
}

run_all() {
    mapfile -t algorithms < <(get_algorithms)
    printf "%s\n" "${algorithms[@]}"
}

join_by_comma() {
    local IFS=","
    echo "$*"
}

rebuild_results_csv() {
    local data_dir="tests/data"
    local first=1
    local file

    mkdir -p "$data_dir"

    # Создаём results.csv (единый CSV для отчета).
    # Берём ВСЕ CSV из tests/data, кроме самого results*.csv.
    local out_file="$data_dir/results.csv"
    : > "$out_file"

    mapfile -t files < <(
        find "$data_dir" -maxdepth 1 -type f -name '*.csv' \
          ! -name 'results*.csv' \
          -printf '%f\n' \
        | sort
    )

    if [ "${#files[@]}" -eq 0 ]; then
        echo "Ошибка: в $data_dir нет CSV-файлов с результатами (кроме results*.csv)." >&2
        exit 1
    fi

    first=1
    for file in "${files[@]}"; do
        file="$data_dir/$file"
        if [ "$first" -eq 1 ]; then
            cat "$file" >> "$out_file"
            first=0
        else
            tail -n +2 "$file" >> "$out_file"
        fi
    done
}

cleanup_generated_data() {
    rm -f tests/data/*.csv tests/data/test_data.json
}

if [ "$#" -eq 0 ]; then
    usage
    exit 1
fi

case "$1" in
    -h|--help)
        usage
        ;;
    -list)
        require_runner
        print_algorithms
        ;;
    -run)
        ensure_env
        require_runner
        trap cleanup_generated_data EXIT
        if [ "${2:-}" = "-all" ]; then
            clean_data_dir
            regenerate_test_data
            mapfile -t selected < <(run_all)
        elif [ -z "${2:-}" ]; then
            if [ ! -f tests/data/test_data.json ]; then
                regenerate_test_data
            fi
            mapfile -t selected < <(run_interactive)
        else
            echo "Неизвестный аргумент для -run: $2" >&2
            usage
            exit 1
        fi

        if [ "${#selected[@]}" -eq 0 ]; then
            echo "Ошибка: не выбрано ни одного алгоритма." >&2
            exit 1
        fi

        rm -f tests/data/results*.csv
        for algo in "${selected[@]}"; do
            short="${algo#algo_}"
            rm -f "tests/data/${short}.csv" "tests/data/${short}N.csv"
        done
        selected_csv="$(join_by_comma "${selected[@]}")"
        echo "Запуск алгоритмов: $selected_csv"
        run_python_benchmarks "$selected_csv" >/dev/null
        echo "Обновление графиков и README"
        rebuild_results_csv
        PYTHON="$PYTHON" ./scripts/build_reports.sh main
        echo "Готово"
        ;;
    *)
        echo "Неизвестная команда: $1" >&2
        usage
        exit 1
        ;;
esac
