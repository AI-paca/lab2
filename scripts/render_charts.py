#!/usr/bin/env python3
"""Render the language-neutral chart set used by the report notebooks.

The script resolves every input and output path relative to the repository, so
it can be invoked from any working directory:

    python scripts/render_charts.py main
    python scripts/render_charts.py debag
    python scripts/render_charts.py all
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MAIN_RESULTS = PROJECT_ROOT / "tests" / "data" / "results.csv"
MAIN_OUTPUT = PROJECT_ROOT / "tests" / "report" / "resources"
DEBAG_RESULTS = PROJECT_ROOT / "debag" / "data" / "results_debag.csv"
DEBAG_OUTPUT = PROJECT_ROOT / "debag" / "reports" / "resources"

REQUIRED_COLUMNS = {"Algorithm", "N", "PrepareTime", "FindTime"}

MAIN_COLORS = {
    "algo_brute": "#1f77b4",
    "algo_map": "#ff7f0e",
    "algo_tree": "#2ca02c",
}
MAIN_LABELS = {
    "algo_brute": "brute",
    "algo_map": "map",
    "algo_tree": "tree",
}
DEBAG_COLORS = {
    "fake_ab": "#1f77b4",
    "fake_am": "#ff7f0e",
    "fake_at": "#2ca02c",
}
DEBAG_LABELS = {
    "fake_ab": "AB",
    "fake_am": "AM",
    "fake_at": "AT",
}

plt.rcParams.update(
    {
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "legend.framealpha": 0.9,
        "savefig.dpi": 150,
    }
)


def load_results(path: Path) -> pd.DataFrame:
    """Load and validate one benchmark result table."""
    if not path.is_file():
        raise FileNotFoundError(f"Results file does not exist: {path}")

    data = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        columns = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns in {path}: {columns}")
    if data.empty:
        raise ValueError(f"Results file is empty: {path}")

    data = data.copy()
    for column in ("N", "PrepareTime", "FindTime"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    if not np.isfinite(data[["N", "PrepareTime", "FindTime"]].to_numpy()).all():
        raise ValueError(f"Results contain non-finite numeric values: {path}")

    return data.sort_values(["Algorithm", "N"]).reset_index(drop=True)


def algorithm_label(name: str, labels: dict[str, str]) -> str:
    """Return the language-neutral label for an algorithm."""
    if name not in labels:
        raise ValueError(f"No language-neutral chart label for algorithm: {name}")
    return labels[name]


def save_figure(fig: plt.Figure, output_dir: Path, name: str) -> None:
    """Save and close a figure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_dir / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


def render_metric_chart(
    data: pd.DataFrame,
    output_dir: Path,
    *,
    metric: str,
    filename: str,
    title: str,
    colors: dict[str, str],
    labels: dict[str, str],
    marker: str,
    log_scale: bool = False,
    excluded: set[str] | None = None,
) -> None:
    """Render one preparation-time or query-time comparison."""
    fig, ax = plt.subplots(figsize=(10, 6))
    excluded = excluded or set()

    for algorithm in data["Algorithm"].unique():
        if algorithm in excluded:
            continue
        subset = data[data["Algorithm"] == algorithm]
        if log_scale:
            subset = subset[(subset["N"] > 0) & (subset[metric] > 0)]
        ax.plot(
            subset["N"],
            subset[metric],
            marker=marker,
            color=colors.get(algorithm, "#333333"),
            label=algorithm_label(algorithm, labels),
        )

    ax.set_xlabel("N")
    ax.set_ylabel("t, s")
    ax.set_title(title)
    if log_scale:
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.legend()
    save_figure(fig, output_dir, filename)


def render_main_overview(data: pd.DataFrame, output_dir: Path) -> None:
    """Render the combined main benchmark chart on logarithmic axes."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for algorithm in data["Algorithm"].unique():
        subset = data[(data["Algorithm"] == algorithm) & (data["N"] > 0)]
        preparation = subset[subset["PrepareTime"] > 0]
        query = subset[subset["FindTime"] > 0]
        color = MAIN_COLORS.get(algorithm, "#333333")
        label = algorithm_label(algorithm, MAIN_LABELS)
        ax.plot(
            preparation["N"],
            preparation["PrepareTime"],
            "--",
            marker="o",
            color=color,
            label=f"{label}: PrepareTime",
        )
        ax.plot(
            query["N"],
            query["FindTime"],
            "-",
            marker="s",
            color=color,
            label=f"{label}: FindTime",
        )

    ax.set_xlabel("N")
    ax.set_ylabel("t, s")
    ax.set_title("PrepareTime(N), FindTime(N)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend()
    save_figure(fig, output_dir, "log_log")


def evenly_spaced(values: list[float], count: int) -> list[float]:
    """Pick up to ``count`` representative values, including both ends."""
    if count <= 0 or not values:
        return []
    if len(values) <= count:
        return values
    indices = np.linspace(0, len(values) - 1, count).round().astype(int)
    return [values[index] for index in dict.fromkeys(indices)]


def render_time_by_n(data: pd.DataFrame, output_dir: Path, *, logarithmic: bool) -> None:
    """Render total time as a function of N for four fixed query counts."""
    query_counts = (10, 100, 1_000, 10_000)
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(14, 10),
        sharex=True,
        sharey=logarithmic,
    )

    for ax, query_count in zip(axes.ravel(), query_counts):
        for algorithm in data["Algorithm"].unique():
            subset = data[data["Algorithm"] == algorithm]
            if logarithmic:
                subset = subset[subset["N"] > 0]
            total = subset["PrepareTime"] + query_count * subset["FindTime"]
            valid = total > 0 if logarithmic else np.ones(len(total), dtype=bool)
            ax.plot(
                subset.loc[valid, "N"],
                total.loc[valid],
                marker="o",
                color=MAIN_COLORS.get(algorithm, "#333333"),
                label=algorithm_label(algorithm, MAIN_LABELS),
                linewidth=2,
                markersize=4,
            )

        ax.set_title(f"M = {query_count:,}")
        ax.set_xlabel("N")
        ax.set_ylabel("t, s")
        if logarithmic:
            ax.set_xscale("log")
            ax.set_yscale("log")

    axes.ravel()[0].legend(loc="upper left", fontsize=11)
    fig.suptitle(
        "t(N,M) = PrepareTime(N) + M × FindTime(N)",
        y=0.98,
        fontsize=16,
        fontweight="bold",
    )
    filename = "time_by_N_log" if logarithmic else "time_by_N"
    save_figure(fig, output_dir, filename)


def render_time_by_m(data: pd.DataFrame, output_dir: Path) -> None:
    """Render total time as a function of M for four fixed data sizes."""
    positive_n = sorted(data.loc[data["N"] > 0, "N"].unique().tolist())
    selected_n = evenly_spaced(positive_n, 4)
    query_counts = np.arange(0, 10_001, 100)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)

    for ax, n_value in zip(axes.ravel(), selected_n):
        for algorithm in data["Algorithm"].unique():
            row = data[(data["Algorithm"] == algorithm) & (data["N"] == n_value)]
            if row.empty:
                continue
            preparation = float(row.iloc[0]["PrepareTime"])
            query = float(row.iloc[0]["FindTime"])
            total = preparation + query_counts * query
            ax.plot(
                query_counts,
                total,
                marker="s",
                color=MAIN_COLORS.get(algorithm, "#333333"),
                label=algorithm_label(algorithm, MAIN_LABELS),
                linewidth=2,
                markersize=3,
            )

        ax.set_title(f"N = {n_value:g}")
        ax.set_xlabel("M")
        ax.set_ylabel("t, s")

    for ax in axes.ravel()[len(selected_n) :]:
        ax.set_visible(False)
    axes.ravel()[0].legend(loc="upper left", fontsize=11)
    fig.suptitle(
        "t(N,M) = PrepareTime(N) + M × FindTime(N)",
        y=0.98,
        fontsize=16,
        fontweight="bold",
    )
    save_figure(fig, output_dir, "time_by_M")


def prepare_region_data(
    data: pd.DataFrame,
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, float]:
    """Interpolate timings and calculate the useful M range for region plots."""
    averaged = (
        data.groupby(["Algorithm", "N"], as_index=False)[["PrepareTime", "FindTime"]]
        .mean()
        .sort_values(["Algorithm", "N"])
    )
    algorithms = sorted(averaged["Algorithm"].unique())
    n_values = sorted(float(n) for n in averaged["N"].unique() if n > 0)
    if not algorithms or not n_values:
        raise ValueError("Optimal-region charts require at least one positive N value")

    lookup = averaged.set_index(["Algorithm", "N"])[["PrepareTime", "FindTime"]]
    crossings = [10.0]
    for n_value in n_values:
        timings = []
        for algorithm in algorithms:
            key = (algorithm, n_value)
            if key in lookup.index:
                row = lookup.loc[key]
                timings.append((float(row["PrepareTime"]), float(row["FindTime"])))
        for left in range(len(timings)):
            for right in range(left + 1, len(timings)):
                query_delta = timings[left][1] - timings[right][1]
                if abs(query_delta) <= 1e-15:
                    continue
                crossing = (timings[right][0] - timings[left][0]) / query_delta
                if 0 < crossing < 1e8:
                    crossings.append(crossing)

    m_max = max(crossings) * 1.2
    n_grid = np.linspace(min(n_values), max(n_values) * 1.05, 800)
    algorithm_n: dict[str, np.ndarray] = {}
    algorithm_preparation: dict[str, np.ndarray] = {}
    algorithm_query: dict[str, np.ndarray] = {}
    for algorithm in algorithms:
        subset = averaged[(averaged["Algorithm"] == algorithm) & (averaged["N"] > 0)]
        algorithm_n[algorithm] = subset["N"].to_numpy(dtype=float)
        algorithm_preparation[algorithm] = subset["PrepareTime"].to_numpy(dtype=float)
        algorithm_query[algorithm] = subset["FindTime"].to_numpy(dtype=float)

    interpolated_preparation = np.vstack(
        [
            np.interp(n_grid, algorithm_n[a], algorithm_preparation[a])
            for a in algorithms
        ]
    )
    interpolated_query = np.vstack(
        [np.interp(n_grid, algorithm_n[a], algorithm_query[a]) for a in algorithms]
    )
    return algorithms, np.asarray(n_values), n_grid, np.stack(
        (interpolated_preparation, interpolated_query)
    ), m_max


def render_algorithm_regions(data: pd.DataFrame, output_dir: Path) -> None:
    """Render linear-M and logarithmic-M optimal-algorithm regions."""
    algorithms, measured_n, n_grid, timings, m_max = prepare_region_data(data)
    preparation, query = timings
    colors = [MAIN_COLORS.get(a, plt.cm.tab10(i)) for i, a in enumerate(algorithms)]
    color_map = ListedColormap(colors)

    for logarithmic in (False, True):
        if logarithmic:
            m_grid = np.geomspace(1, m_max, 800)
        else:
            m_grid = np.linspace(1, m_max, 800)

        total = preparation[:, np.newaxis, :] + (
            m_grid[np.newaxis, :, np.newaxis] * query[:, np.newaxis, :]
        )
        best = np.argmin(total, axis=0)

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.pcolormesh(
            m_grid,
            n_grid,
            best.T,
            cmap=color_map,
            shading="nearest",
            alpha=0.7,
        )
        present = sorted(set(best.flat))
        if len(present) > 1:
            levels = [
                (present[index] + present[index + 1]) / 2
                for index in range(len(present) - 1)
            ]
            ax.contour(
                m_grid,
                n_grid,
                best.T.astype(float),
                levels=levels,
                colors="black",
                linewidths=2,
            )
        for n_value in measured_n:
            ax.axhline(n_value, color="black", linestyle=":", alpha=0.4, linewidth=1)

        if logarithmic:
            ax.set_xscale("log")
        ax.set_xlim(1, m_max)
        ax.set_ylim(float(measured_n.min()), float(measured_n.max()) * 1.05)
        ax.set_xlabel("M", fontsize=12)
        ax.set_ylabel("N", fontsize=12)
        ax.set_title(r"$\arg\min_a\ t_a(N,M)$", fontsize=14, fontweight="bold")
        legend = [
            Patch(
                facecolor=colors[index],
                edgecolor="black",
                label=algorithm_label(algorithm, MAIN_LABELS),
            )
            for index, algorithm in enumerate(algorithms)
        ]
        ax.legend(handles=legend, fontsize=11, loc="upper left")
        filename = "algo_regions_log" if logarithmic else "algo_regions_linear"
        save_figure(fig, output_dir, filename)


def render_main() -> None:
    """Render every language-neutral chart for the main benchmark."""
    data = load_results(MAIN_RESULTS)

    render_metric_chart(
        data,
        MAIN_OUTPUT,
        metric="PrepareTime",
        filename="prepare_time",
        title="PrepareTime(N)",
        colors=MAIN_COLORS,
        labels=MAIN_LABELS,
        marker="o",
    )
    render_metric_chart(
        data,
        MAIN_OUTPUT,
        metric="PrepareTime",
        filename="prepare_linear_no_map",
        title="PrepareTime(N): brute, tree",
        colors=MAIN_COLORS,
        labels=MAIN_LABELS,
        marker="o",
        excluded={"algo_map"},
    )
    render_metric_chart(
        data,
        MAIN_OUTPUT,
        metric="PrepareTime",
        filename="prepare_log",
        title="PrepareTime(N)",
        colors=MAIN_COLORS,
        labels=MAIN_LABELS,
        marker="o",
        log_scale=True,
    )
    render_metric_chart(
        data,
        MAIN_OUTPUT,
        metric="FindTime",
        filename="find_time",
        title="FindTime(N)",
        colors=MAIN_COLORS,
        labels=MAIN_LABELS,
        marker="s",
    )
    render_metric_chart(
        data,
        MAIN_OUTPUT,
        metric="FindTime",
        filename="find_log",
        title="FindTime(N)",
        colors=MAIN_COLORS,
        labels=MAIN_LABELS,
        marker="s",
        log_scale=True,
    )
    render_metric_chart(
        data,
        MAIN_OUTPUT,
        metric="FindTime",
        filename="find_linear_no_brute",
        title="FindTime(N): map, tree",
        colors=MAIN_COLORS,
        labels=MAIN_LABELS,
        marker="s",
        excluded={"algo_brute"},
    )
    render_main_overview(data, MAIN_OUTPUT)
    render_time_by_n(data, MAIN_OUTPUT, logarithmic=False)
    render_time_by_n(data, MAIN_OUTPUT, logarithmic=True)
    render_time_by_m(data, MAIN_OUTPUT)
    render_algorithm_regions(data, MAIN_OUTPUT)


def render_debag_overview(data: pd.DataFrame, output_dir: Path) -> None:
    """Render the combined control-benchmark chart on logarithmic axes."""
    fig, ax = plt.subplots(figsize=(10, 6))
    for algorithm in data["Algorithm"].unique():
        subset = data[(data["Algorithm"] == algorithm) & (data["N"] > 0)]
        preparation = subset[subset["PrepareTime"] > 0]
        query = subset[subset["FindTime"] > 0]
        color = DEBAG_COLORS.get(algorithm, "#333333")
        label = algorithm_label(algorithm, DEBAG_LABELS)
        ax.plot(
            preparation["N"],
            preparation["PrepareTime"],
            "--",
            marker="o",
            color=color,
            label=f"{label}: PrepareTime",
        )
        ax.plot(
            query["N"],
            query["FindTime"],
            "-",
            marker="s",
            color=color,
            label=f"{label}: FindTime",
        )
    ax.set_xlabel("N")
    ax.set_ylabel("t, s")
    ax.set_title("PrepareTime(N), FindTime(N)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend()
    save_figure(fig, output_dir, "debag_log_log")


def render_debag() -> None:
    """Render every language-neutral chart for the control benchmark."""
    data = load_results(DEBAG_RESULTS)
    render_debag_overview(data, DEBAG_OUTPUT)
    render_metric_chart(
        data,
        DEBAG_OUTPUT,
        metric="PrepareTime",
        filename="debag_prepare_log",
        title="PrepareTime(N)",
        colors=DEBAG_COLORS,
        labels=DEBAG_LABELS,
        marker="o",
        log_scale=True,
    )
    render_metric_chart(
        data,
        DEBAG_OUTPUT,
        metric="FindTime",
        filename="debag_query_log",
        title="FindTime(N)",
        colors=DEBAG_COLORS,
        labels=DEBAG_LABELS,
        marker="s",
        log_scale=True,
    )
    render_metric_chart(
        data,
        DEBAG_OUTPUT,
        metric="PrepareTime",
        filename="debag_prepare_time",
        title="PrepareTime(N)",
        colors=DEBAG_COLORS,
        labels=DEBAG_LABELS,
        marker="o",
    )
    render_metric_chart(
        data,
        DEBAG_OUTPUT,
        metric="FindTime",
        filename="debag_query_time",
        title="FindTime(N)",
        colors=DEBAG_COLORS,
        labels=DEBAG_LABELS,
        marker="s",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render language-neutral benchmark charts for the report notebooks."
    )
    parser.add_argument(
        "mode",
        choices=("main", "debag", "all"),
        help="chart set to render",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode in ("main", "all"):
        render_main()
    if args.mode in ("debag", "all"):
        render_debag()


if __name__ == "__main__":
    main()
