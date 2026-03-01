"""Generate benchmark comparison plots from results.

Usage:
    cd backend
    uv run python -m benchmark.plots

Reads: benchmark/results/benchmark_results.json
Saves: benchmark/results/*.png
"""

import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "benchmark_results.json")

# Dark theme colors matching paper.tech brand
COLORS = {
    "GPT-4o-mini": "#10b981",              # emerald green
    "Gemini 2.5 Flash": "#3b82f6",         # blue
    "Qwen3-4B (no memory)": "#ef4444",     # red
    "Qwen3-4B (full history)": "#f59e0b",  # amber
    "Qwen3-4B + Supermemory": "#00d4db",   # cyan (our brand)
}

SETUP_ORDER = [
    "GPT-4o-mini",
    "Gemini 2.5 Flash",
    "Qwen3-4B (no memory)",
    "Qwen3-4B (full history)",
    "Qwen3-4B + Supermemory",
]


def _ordered_names(results: dict) -> list[str]:
    """Return setup names in a consistent display order."""
    return [n for n in SETUP_ORDER if n in results]


def _setup_dark_style():
    """Apply dark theme consistent with paper.tech branding."""
    plt.rcParams.update({
        "figure.facecolor": "#0a0f1e",
        "axes.facecolor": "#111827",
        "axes.edgecolor": "#374151",
        "axes.labelcolor": "#e5e7eb",
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.color": "#9ca3af",
        "ytick.color": "#9ca3af",
        "text.color": "#e5e7eb",
        "legend.facecolor": "#1a2235",
        "legend.edgecolor": "#374151",
        "legend.fontsize": 10,
        "grid.color": "#1f2937",
        "grid.alpha": 0.5,
        "font.family": "sans-serif",
        "font.size": 11,
        "figure.dpi": 150,
        "savefig.dpi": 200,
        "savefig.facecolor": "#0a0f1e",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.3,
    })


def _highlight_supermemory(bars, names):
    """Add cyan edge highlight to the Supermemory bar."""
    if "Qwen3-4B + Supermemory" in names:
        idx = names.index("Qwen3-4B + Supermemory")
        bars[idx].set_edgecolor("#00d4db")
        bars[idx].set_linewidth(2.5)


def plot_recall_accuracy(results: dict):
    """Bar chart: Context Recall Accuracy (CRA) per setup."""
    _setup_dark_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    names = _ordered_names(results)
    scores = [results[n]["context_recall_accuracy"] for n in names]
    colors = [COLORS.get(n, "#6b7280") for n in names]

    bars = ax.bar(range(len(names)), scores, color=colors, width=0.6,
                  edgecolor="#1f2937", linewidth=1.5, zorder=3)

    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{score:.1%}", ha="center", va="bottom", fontweight="bold",
                fontsize=12, color="#e5e7eb")

    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha="right", fontsize=10)
    ax.set_ylabel("Context Recall Accuracy")
    ax.set_title("Multi-Turn Context Recall Accuracy", fontsize=16,
                 fontweight="bold", pad=15)
    ax.set_ylim(0, 1.15)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.grid(axis="y", linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    _highlight_supermemory(bars, names)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "recall_accuracy.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_latency_by_turn(results: dict):
    """Line chart: latency across turns 1, 4, 7, 10 per setup."""
    _setup_dark_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    turn_labels = ["Turn 1", "Turn 4", "Turn 7", "Turn 10"]
    turn_keys = ["turn_1", "turn_4", "turn_7", "turn_10"]
    x = np.arange(len(turn_labels))

    for name in _ordered_names(results):
        data = results[name]
        latencies = [data["avg_latencies_ms"].get(k) for k in turn_keys]
        if all(l is None for l in latencies):
            continue
        latencies = [l if l is not None else 0 for l in latencies]
        color = COLORS.get(name, "#6b7280")
        is_ours = name == "Qwen3-4B + Supermemory"
        ax.plot(x, latencies,
                marker="D" if is_ours else "o",
                markersize=8, linewidth=3 if is_ours else 2,
                color=color, label=name, zorder=4 if is_ours else 3)

    ax.set_xticks(x)
    ax.set_xticklabels(turn_labels, fontsize=11)
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Response Latency Across Conversation Turns", fontsize=16,
                 fontweight="bold", pad=15)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "latency_by_turn.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_avg_latency_bar(results: dict):
    """Horizontal bar chart: average latency per setup."""
    _setup_dark_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    names = _ordered_names(results)
    avg_lats = []
    for n in names:
        lats = [v for v in results[n]["avg_latencies_ms"].values() if v is not None]
        avg_lats.append(sum(lats) / len(lats) if lats else 0)

    colors = [COLORS.get(n, "#6b7280") for n in names]
    bars = ax.barh(range(len(names)), avg_lats, color=colors, height=0.5,
                   edgecolor="#1f2937", linewidth=1.5, zorder=3)

    max_lat = max(avg_lats) if avg_lats else 1
    for bar, lat in zip(bars, avg_lats):
        ax.text(bar.get_width() + max_lat * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{lat:.0f} ms", ha="left", va="center", fontweight="bold",
                fontsize=11, color="#e5e7eb")

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("Average Latency (ms)")
    ax.set_title("Average Response Latency", fontsize=16, fontweight="bold", pad=15)
    ax.grid(axis="x", linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    _highlight_supermemory(bars, names)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "avg_latency.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_recall_per_probe(results: dict):
    """Grouped bar chart: recall accuracy broken down by probe (Turn 4, 7, 10)."""
    _setup_dark_style()
    fig, ax = plt.subplots(figsize=(12, 6))

    probe_labels = ["Probe 1\n(Turn 4)", "Probe 2\n(Turn 7)", "Probe 3\n(Turn 10)"]
    names = _ordered_names(results)
    n_setups = len(names)
    n_probes = len(probe_labels)
    bar_width = 0.15
    x = np.arange(n_probes)

    for i, name in enumerate(names):
        probe_scores = results[name].get("per_probe_recall", [0, 0, 0])
        offset = (i - n_setups / 2 + 0.5) * bar_width
        color = COLORS.get(name, "#6b7280")
        ax.bar(x + offset, probe_scores, bar_width, color=color,
               label=name, edgecolor="#1f2937", linewidth=1, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(probe_labels, fontsize=11)
    ax.set_ylabel("Recall Accuracy")
    ax.set_title("Context Recall by Probe Position", fontsize=16,
                 fontweight="bold", pad=15)
    ax.set_ylim(0, 1.2)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "recall_per_probe.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_combined_dashboard(results: dict):
    """2x2 dashboard combining all metrics."""
    _setup_dark_style()
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    names = _ordered_names(results)
    colors = [COLORS.get(n, "#6b7280") for n in names]

    # ── Top-left: CRA bar chart ──
    ax = axes[0, 0]
    scores = [results[n]["context_recall_accuracy"] for n in names]
    bars = ax.bar(range(len(names)), scores, color=colors, width=0.6,
                  edgecolor="#1f2937", linewidth=1.5, zorder=3)
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{score:.0%}", ha="center", va="bottom", fontweight="bold",
                fontsize=10, color="#e5e7eb")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace(" (", "\n(") for n in names], fontsize=8,
                       rotation=0, ha="center")
    ax.set_ylabel("Recall Accuracy")
    ax.set_title("Context Recall Accuracy", fontweight="bold")
    ax.set_ylim(0, 1.15)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.grid(axis="y", linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # ── Top-right: Latency line chart ──
    ax = axes[0, 1]
    turn_keys = ["turn_1", "turn_4", "turn_7", "turn_10"]
    turn_labels = ["T1", "T4", "T7", "T10"]
    x = np.arange(len(turn_labels))
    for name in names:
        lats = [results[name]["avg_latencies_ms"].get(k) or 0 for k in turn_keys]
        color = COLORS.get(name, "#6b7280")
        lw = 2.5 if "Supermemory" in name else 1.5
        ax.plot(x, lats, marker="o", markersize=6, linewidth=lw,
                color=color, label=name, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(turn_labels)
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Latency Across Turns", fontweight="bold")
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # ── Bottom-left: Avg latency horizontal bars ──
    ax = axes[1, 0]
    avg_lats = []
    for n in names:
        lats = [v for v in results[n]["avg_latencies_ms"].values() if v]
        avg_lats.append(sum(lats) / len(lats) if lats else 0)
    bars = ax.barh(range(len(names)), avg_lats, color=colors, height=0.5,
                   edgecolor="#1f2937", linewidth=1.5, zorder=3)
    max_lat = max(avg_lats) if avg_lats else 1
    for bar, lat in zip(bars, avg_lats):
        ax.text(bar.get_width() + max_lat * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{lat:.0f}ms", ha="left", va="center", fontsize=10,
                color="#e5e7eb")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Average Latency (ms)")
    ax.set_title("Average Response Latency", fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    ax.invert_yaxis()

    # ── Bottom-right: Per-probe recall grouped bars ──
    ax = axes[1, 1]
    probe_labels = ["Probe 1\n(Turn 4)", "Probe 2\n(Turn 7)", "Probe 3\n(Turn 10)"]
    n_setups = len(names)
    n_probes = len(probe_labels)
    bar_width = 0.14
    xp = np.arange(n_probes)
    for i, name in enumerate(names):
        probe_scores = results[name].get("per_probe_recall", [0, 0, 0])
        offset = (i - n_setups / 2 + 0.5) * bar_width
        ax.bar(xp + offset, probe_scores, bar_width,
               color=COLORS.get(name, "#6b7280"), label=name,
               edgecolor="#1f2937", linewidth=1, zorder=3)
    ax.set_xticks(xp)
    ax.set_xticklabels(probe_labels, fontsize=10)
    ax.set_ylabel("Recall Accuracy")
    ax.set_title("Recall by Probe Position", fontweight="bold")
    ax.set_ylim(0, 1.25)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.legend(fontsize=7, loc="upper right", framealpha=0.9, ncol=2)
    ax.grid(axis="y", linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    fig.suptitle("paper.tech — Multi-Turn Conversation Benchmark",
                 fontsize=18, fontweight="bold", color="#00d4db", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    path = os.path.join(RESULTS_DIR, "dashboard.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def generate_plots(results: dict | None = None):
    """Generate all benchmark plots. If results not passed, loads from file."""
    if results is None:
        if not os.path.exists(RESULTS_FILE):
            print(f"No results found at {RESULTS_FILE}")
            print("Run the benchmark first: uv run python -m benchmark.benchmark")
            return
        with open(RESULTS_FILE) as f:
            results = json.load(f)

    print(f"Generating plots for {len(results)} setups...")
    plot_recall_accuracy(results)
    plot_latency_by_turn(results)
    plot_avg_latency_bar(results)
    plot_recall_per_probe(results)
    plot_combined_dashboard(results)
    print(f"All plots saved to {RESULTS_DIR}/")


if __name__ == "__main__":
    generate_plots()
