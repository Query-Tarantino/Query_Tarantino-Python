"""
Benchmark plotting script â€” generates academic-quality charts for the report.

Produces 3 types of charts per component:
  1. Execution Time (from pytest-benchmark JSON)
  2. RAM Usage (from pytest stdout capture)
  3. Disk Usage (from pytest stdout capture)

Usage:
    python -m services.utils.plot_benchmarks

Charts are saved to the benchmarks/ directory.
"""
import json
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Parse pytest-benchmark JSON results (time data)
# ---------------------------------------------------------------------------

def parse_time_benchmarks():
    """Parse the latest pytest-benchmark JSON file for timing data."""
    files = glob.glob(".benchmarks/*/*.json")
    if not files:
        return pd.DataFrame()
    latest = max(files, key=os.path.getctime)
    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for b in data["benchmarks"]:
        name = b["name"]
        test_group = name.split("[")[0] if "[" in name else name
        adapter = name.split("[")[1].split("]")[0] if "[" in name else "Unknown"
        # Clean adapter names
        for suffix in ("DatalakeAdapter", "IndexAdapter", "MetadataAdapter",
                       "IndexReader", "DatalakeReader"):
            adapter = adapter.replace(suffix, "")
        records.append({
            "Test": test_group,
            "Adapter": adapter,
            "Mean Time (ms)": b["stats"]["mean"] * 1000,
            "StdDev (ms)": b["stats"]["stddev"] * 1000,
            "OPS": b["stats"]["ops"],
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 2. Run RAM & Disk tests and capture stdout
# ---------------------------------------------------------------------------

def run_resource_tests():
    """Run the RAM and disk tests and parse their printed output."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "services/", "-v", "-s",
         "-k", "ram_usage or disk_usage",
         "--no-header", "-q"],
        capture_output=True, text=True, cwd="."
    )
    output = result.stdout + result.stderr

    ram_records = []
    disk_records = []

    # Parse lines like: [RAM] TimeBasedDatalakeAdapter: 0.1234 MB peak
    for m in re.finditer(r"\[RAM\]\s+(\w+):\s+([\d.]+)\s+MB", output):
        adapter = m.group(1)
        for suffix in ("DatalakeAdapter", "IndexAdapter", "MetadataAdapter",
                       "IndexReader", "DatalakeReader", "Adapter"):
            adapter = adapter.replace(suffix, "")
        ram_records.append({
            "Adapter": adapter,
            "Peak RAM (MB)": float(m.group(2)),
        })

    # Parse lines like: [DISK] TimeBasedDatalakeAdapter: 123.45 KB
    for m in re.finditer(r"\[DISK\]\s+(\w+):\s+([\d.]+)\s+KB", output):
        adapter = m.group(1)
        for suffix in ("DatalakeAdapter", "IndexAdapter", "MetadataAdapter",
                       "IndexReader", "DatalakeReader", "Adapter"):
            adapter = adapter.replace(suffix, "")
        disk_records.append({
            "Adapter": adapter,
            "Disk Usage (KB)": float(m.group(2)),
        })

    return pd.DataFrame(ram_records), pd.DataFrame(disk_records)


# ---------------------------------------------------------------------------
# 3. Plotting helpers
# ---------------------------------------------------------------------------

def setup_style():
    plt.style.use("seaborn-v0_8-paper")
    sns.set_theme(style="ticks", context="paper", font_scale=1.3)
    plt.rcParams.update({
        "font.family": "serif",
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "axes.grid": True,
        "grid.linestyle": "--",
        "grid.alpha": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def bar_chart(df, x, y, title, ylabel, filename, yerr=None,
              palette="Blues_d", log_scale=False, lower_is_better=True):
    """Create a single academic-quality bar chart."""
    if df.empty:
        return
    df = df.sort_values(y, ascending=not lower_is_better).copy()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = sns.color_palette(palette, len(df))

    kwargs = {"capsize": 5} if yerr else {}
    bars = ax.bar(df[x], df[y], yerr=df[yerr] if yerr else None,
                  color=colors, edgecolor="black", linewidth=0.8, **kwargs)

    if log_scale:
        ax.set_yscale("log")

    ax.set_title(title, pad=15, fontweight="bold", fontsize=13)
    ax.set_ylabel(ylabel, fontweight="bold")
    ax.set_xlabel("Implementation Strategy", fontweight="bold")

    # Value labels
    for bar in bars:
        yval = bar.get_height()
        offset = yval * 0.15 if log_scale else ax.get_ylim()[1] * 0.02
        label_y = yval + offset
        fmt = f"{yval:.4f}" if yval < 1 else f"{yval:.2f}"
        ax.text(bar.get_x() + bar.get_width() / 2, label_y, fmt,
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    quality = "Lower is better â†“" if lower_is_better else "Higher is better â†‘"
    ax.annotate(quality, xy=(0.98, 0.95), xycoords="axes fraction",
                ha="right", va="top", fontsize=9, fontstyle="italic",
                color="gray")

    plt.tight_layout()
    Path("benchmarks").mkdir(exist_ok=True)
    plt.savefig(f"benchmarks/{filename}", bbox_inches="tight")
    plt.close()
    print(f"  âœ“ benchmarks/{filename}")


# ---------------------------------------------------------------------------
# 4. Main
# ---------------------------------------------------------------------------

def main():
    setup_style()
    out_dir = Path("benchmarks")
    out_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("  Generating benchmark charts for the report")
    print("=" * 60)

    # --- Time charts (from pytest-benchmark JSON) ---
    print("\n[1/3] Parsing timing data from pytest-benchmark...")
    time_df = parse_time_benchmarks()

    if not time_df.empty:
        # Datalake write throughput
        dl = time_df[time_df["Test"] == "test_benchmark_datalake_write"]
        bar_chart(dl, "Adapter", "Mean Time (ms)",
                  "Datalake Write Throughput", "Mean Time (ms)",
                  "datalake_time.png", yerr="StdDev (ms)")

        # Datalake recovery (lookup)
        rec = time_df[time_df["Test"] == "test_benchmark_datalake_recovery"]
        bar_chart(rec, "Adapter", "Mean Time (ms)",
                  "Datalake Lookup Latency", "Mean Time (ms)",
                  "datalake_recovery_time.png", yerr="StdDev (ms)")

        # Index build time
        idx = time_df[time_df["Test"] == "test_benchmark_indexing"]
        bar_chart(idx, "Adapter", "Mean Time (ms)",
                  "Inverted Index Build Time", "Mean Time (ms)",
                  "indexer_time.png", yerr="StdDev (ms)", log_scale=True)

        # Query latency
        qry = time_df[time_df["Test"] == "test_benchmark_query"]
        bar_chart(qry, "Adapter", "Mean Time (ms)",
                  "Search Query Latency", "Mean Time (ms)",
                  "query_time.png", yerr="StdDev (ms)")

        # Metadata insertion time
        meta = time_df[time_df["Test"] == "test_benchmark_metadata"]
        bar_chart(meta, "Adapter", "Mean Time (ms)",
                  "Metadata Insertion Time", "Mean Time (ms)",
                  "metadata_time.png", yerr="StdDev (ms)")

    # --- RAM and Disk charts (run resource tests) ---
    print("\n[2/3] Running RAM and disk usage tests...")
    ram_df, disk_df = run_resource_tests()

    print("\n[3/3] Generating RAM and disk charts...")
    if not ram_df.empty:
        bar_chart(ram_df, "Adapter", "Peak RAM (MB)",
                  "Peak Memory (RAM) Usage", "Peak RAM (MB)",
                  "ram_usage.png", palette="Oranges_d")

    if not disk_df.empty:
        bar_chart(disk_df, "Adapter", "Disk Usage (KB)",
                  "Disk Space Consumption", "Disk Usage (KB)",
                  "disk_usage.png", palette="Greens_d")

    print("\n" + "=" * 60)
    print("  All charts saved to benchmarks/")
    print("=" * 60)


if __name__ == "__main__":
    main()

