#!/usr/bin/env python3
"""Plot the finite semantic/noise robustness sweep."""

from pathlib import Path
import argparse

import matplotlib.pyplot as plt
import pandas as pd


NOISE_ORDER = ["perfect", "nominal", "conservative_error", "false_free_stress"]
METHOD_ORDER = ["coverage_greedy", "singleton_voi", "set_independent", "set_joint"]
LABELS = {
    "perfect": "Perfect",
    "nominal": "Nominal",
    "conservative_error": "Conservative error",
    "false_free_stress": "False-free stress",
    "coverage_greedy": "Coverage greedy",
    "singleton_voi": "Singleton VoI",
    "set_independent": "Set / independent",
    "set_joint": "Set / joint",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()
    result_dir = args.result_dir
    plot_dir = result_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(result_dir / "summary.csv")
    summary = (
        summary.groupby(["config", "noise", "method"], as_index=False)
        .agg(progress_mean=("progress_mean", "mean"), unsafe_go_mean=("unsafe_go_mean", "mean"))
    )
    summary["noise"] = pd.Categorical(summary["noise"], NOISE_ORDER, ordered=True)
    summary["method"] = pd.Categorical(summary["method"], METHOD_ORDER, ordered=True)

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.2), sharex=True)
    colors = dict(zip(METHOD_ORDER, ["#777777", "#d95f02", "#1b9e77", "#7570b3"]))
    for col, config in enumerate(["independent", "contention"]):
        sub = summary[summary["config"] == config]
        for method in METHOD_ORDER:
            d = sub[sub["method"] == method].sort_values("noise")
            x = range(len(d))
            axes[0, col].plot(x, d["progress_mean"], marker="o", label=LABELS[method], color=colors[method])
            axes[1, col].plot(x, 100 * d["unsafe_go_mean"], marker="o", color=colors[method])
        axes[0, col].set_title(config.capitalize())
        axes[0, col].set_ylabel("Progress ratio")
        axes[1, col].set_ylabel("Unsafe-go rate (%)")
        axes[1, col].set_xticks(range(len(NOISE_ORDER)), [LABELS[n] for n in NOISE_ORDER], rotation=18, ha="right")
        for row in range(2):
            axes[row, col].grid(alpha=0.25)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.94), ncol=4, frameon=False)
    fig.suptitle("Semantic-noise robustness (500 paired seeds per scenario and cell)", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    for suffix in ["png", "pdf"]:
        fig.savefig(plot_dir / f"robustness.{suffix}", dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
