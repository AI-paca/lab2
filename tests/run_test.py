#!/usr/bin/env python3

import csv
import gc
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from statistics import median

################################################################################
MEASURE_RUNS_PREPARE = 7  # нечётное число прогонов для устойчивой медианы
MEASURE_RUNS_FIND = 15
MIN_PREPARE_SAMPLE_TIME = 0.1
################################################################################

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATA_FILE = PROJECT_ROOT / "tests" / "data" / "test_data.json"
RESULTS_DIR = Path(os.getenv("BENCHMARK_RESULTS_DIR", PROJECT_ROOT / "tests" / "data"))
if not RESULTS_DIR.is_absolute():
    RESULTS_DIR = (PROJECT_ROOT / RESULTS_DIR).resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def load_algorithm(path):
    path = path if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(getattr(mod, "prepare", None)), f"{path.name}: нет prepare()"
    assert callable(getattr(mod, "find", None)), f"{path.name}: нет find()"
    return path.stem, mod

def validate_results(algorithms, prepared_data, dots, n):
    if len(algorithms) <= 1:
        return

    base_name, base_algo = algorithms[0]
    base_prep = prepared_data[base_name]

    for dot in dots:
        expected = base_algo.find(base_prep, dot)
        for name, algo in algorithms[1:]:
            actual = algo.find(prepared_data[name], dot)
            if actual != expected:
                sys.stderr.write(f"\nРасхождение результатов\n")
                sys.stderr.write(f"N = {n}, точка: {dot}\n")
                sys.stderr.write(f"Эталон ({base_name}): {expected}\n")
                sys.stderr.write(f"Алгоритм ({name}): {actual}\n")
                sys.exit(1)

################################################################################

def measure_prepare(algo, rectangles):
    start = time.perf_counter()
    prepared = algo.prepare(rectangles)
    elapsed = time.perf_counter() - start
    calls = 1

    while elapsed < MIN_PREPARE_SAMPLE_TIME:
        prepared = algo.prepare(rectangles)
        calls += 1
        elapsed = time.perf_counter() - start

    return elapsed / calls, prepared

def measure_find(algo, prepared, dots):
    if not dots:
        return 0.0

    num_dots = len(dots)

    # прогрев (иначе первый алгоритм всегда дольше)
    for _ in range(3):
        for dot in dots:
            algo.find(prepared, dot)

    gc.collect() # сборщик мусора 
    times = []
    gc.disable() # отключаем сборщик мусора 

    try:
        for _ in range(MEASURE_RUNS_FIND):
            start = time.perf_counter()
            for dot in dots:
                algo.find(prepared, dot)
            elapsed = time.perf_counter() - start

            times.append(elapsed / num_dots)
    finally:
        gc.enable() # включаем 

    times.sort()
    # рассматриваем только значения в середине (от 20% до 80%)
    trimmed_times = times[int(len(times) * 0.2):int(len(times) * 0.8)] if int(len(times) * 0.2) < int(len(times) * 0.8) else times 

    return median(trimmed_times)




def run_benchmarks(algorithms):
    with open(TEST_DATA_FILE, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    n_keys = sorted(test_data.keys(), key=int)
    results = {name: [] for name, _ in algorithms}

    # прогрев
    first = test_data[n_keys[0]]
    for _, algo in algorithms:
        p = algo.prepare(first["rectangles"])
        for dot in first["dots"]:
            algo.find(p, dot)

    total = len(n_keys)
    for step, n_str in enumerate(n_keys):
        n = int(n_str)
        rects = test_data[n_str]["rectangles"]
        dots = test_data[n_str]["dots"]

        sys.stderr.write(f"\r  [{step}/{total}] N={n} ({100 * step // total}%)")
        sys.stderr.flush()

        prepared_data = {}
        prep_times = {name: [] for name, _ in algorithms}

        # Меняем первого участника между повторами: прогрев кэшей и краткие
        # фоновые пики не должны систематически доставаться одному алгоритму.
        for run in range(MEASURE_RUNS_PREPARE):
            offset = (step + run) % len(algorithms)
            ordered = algorithms[offset:] + algorithms[:offset]
            for name, algo in ordered:
                gc.collect()
                pt, prepared = measure_prepare(algo, rects)
                prep_times[name].append(pt)
                prepared_data[name] = prepared

        # проверка алгоритмов
        validate_results(algorithms, prepared_data, dots, n)

        for name, algo in algorithms:
            ft = measure_find(algo, prepared_data[name], dots)

            results[name].append({
                "Algorithm": name,
                "N": n,
                "PrepareTime": median(prep_times[name]),
                "FindTime": ft,
            })

    sys.stderr.write(f"\r  [{total}/{total}] Готово!          \n")
    sys.stderr.flush()
    return results


def main():
    args = sys.argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print("Использование: python tests/run_test.py algorithms/algo_brute.py algorithms/algo_map.py ...")
        return 1

    algorithms = [load_algorithm(Path(a)) for a in args]
    results = run_benchmarks(algorithms)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    names = []
    for name, _ in algorithms:
        short_name = name.split('_', 1)[1] if '_' in name else name
        # Для debag алгоритмов (fake_*) используем формат results_fake_*.csv
        # Для основных алгоритмов (algo_*) используем формат *.csv
        if name.startswith('fake_'):
            path = RESULTS_DIR / f"results_{name}.csv"
        else:
            path = RESULTS_DIR / f"{short_name}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, ["Algorithm", "N", "PrepareTime", "FindTime"])
            w.writeheader()
            w.writerows(results[name])
        names.append(name)

    print(",".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
