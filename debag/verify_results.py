#!/usr/bin/env python3
"""Validate identical controls and publish the result in both debag READMEs."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_MEDIAN_SPREAD = 0.05
START = "<!-- measurement-results:start -->"
END = "<!-- measurement-results:end -->"


def analyze(path: Path) -> dict[str, float]:
    values = defaultdict(lambda: defaultdict(dict))
    with path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            n = int(row["N"])
            if n == 0:
                continue
            for metric in ("PrepareTime", "FindTime"):
                values[metric][n][row["Algorithm"]] = float(row[metric])

    results = {}
    for metric, by_n in values.items():
        spreads = []
        for controls in by_n.values():
            samples = list(controls.values())
            center = median(samples)
            if center > 0:
                spreads.append((max(samples) - min(samples)) / center)
        if not spreads:
            raise ValueError(f"Нет измерений для {metric}")
        results[metric] = median(spreads)
    return results


def result_block(results: dict[str, float], language: str) -> str:
    passed = all(value <= MAX_MEDIAN_SPREAD for value in results.values())
    if language == "ru":
        title, metric, spread, limit, status = (
            "Результат последней проверки",
            "Метрика",
            "Фактический разброс",
            "Порог",
            "Статус",
        )
        labels = {"PrepareTime": "Подготовка", "FindTime": "Поиск"}
        ok, failed = "пройдено", "не пройдено"
        total = "**Итог: проверка пройдена.**" if passed else "**Итог: проверка не пройдена.**"
    else:
        title, metric, spread, limit, status = (
            "Latest verification result",
            "Metric",
            "Measured spread",
            "Limit",
            "Status",
        )
        labels = {"PrepareTime": "Preparation", "FindTime": "Query"}
        ok, failed = "passed", "failed"
        total = "**Result: passed.**" if passed else "**Result: failed.**"

    rows = [
        START,
        f"## {title}",
        "",
        f"| {metric} | {spread} | {limit} | {status} |",
        "|---|---:|---:|---|",
    ]
    for name in ("PrepareTime", "FindTime"):
        value = results[name]
        rows.append(
            f"| {labels[name]} | {value:.1%} | {MAX_MEDIAN_SPREAD:.0%} | "
            f"{ok if value <= MAX_MEDIAN_SPREAD else failed} |"
        )
    rows.extend(("", total, END))
    return "\n".join(rows)


def update_readme(path: Path, block: str) -> None:
    content = path.read_text(encoding="utf-8")
    start = content.find(START)
    end = content.find(END)
    if start < 0 or end < start:
        raise ValueError(f"Маркеры результата не найдены: {path}")
    end += len(END)
    path.write_text(content[:start] + block + content[end:], encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args()

    results = analyze(args.csv)
    for metric, value in results.items():
        print(f"{metric}: медианный относительный разброс {value:.1%}")

    if args.update_readme:
        update_readme(PROJECT_ROOT / "debag" / "README.md", result_block(results, "ru"))
        update_readme(PROJECT_ROOT / "debag" / "README_EN.md", result_block(results, "en"))

    passed = all(value <= MAX_MEDIAN_SPREAD for value in results.values())
    print("Контрольные замеры стабильны." if passed else "Контрольные замеры нестабильны.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
