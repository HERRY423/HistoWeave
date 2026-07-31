"""Build traceable Bioinformatics submission figures from frozen artefacts.

This script deliberately uses only deterministic plotting code.  It does not
use generative-image services.  Run from the repository root:

    python manuscript/make_submission_assets.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tifffile
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manuscript" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
RED = "#D55E00"
PURPLE = "#CC79A7"
SKY = "#56B4E9"
INK = "#17212B"
PALE = "#F4F7FA"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "figure.dpi": 150,
        "savefig.dpi": 400,
        "svg.fonttype": "none",
    }
)


def _save(fig: plt.Figure, stem: str, *, graphical_abstract: bool = False) -> None:
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.png", bbox_inches="tight", facecolor="white", dpi=400)
    png = np.asarray(Image.open(OUT / f"{stem}.png").convert("RGB"))
    dpi = 350 if graphical_abstract else 400
    tifffile.imwrite(
        OUT / f"{stem}.tif",
        png,
        photometric="rgb",
        resolution=(dpi, dpi),
        resolutionunit="INCH",
    )
    plt.close(fig)


def _box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    title: str,
    body: str,
    color: str,
) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.5,
        edgecolor=color,
        facecolor="white",
    )
    ax.add_patch(patch)
    ax.add_patch(
        FancyBboxPatch(
            (x, y + height - 0.16),
            width,
            0.16,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            linewidth=0,
            facecolor=color,
            alpha=0.16,
        )
    )
    ax.text(x + width / 2, y + height - 0.08, title, ha="center", va="center", weight="bold")
    ax.text(x + width / 2, y + 0.18, body, ha="center", va="center", linespacing=1.3)


def _arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.4,
            color=INK,
        )
    )


def build_workflow() -> None:
    fig, ax = plt.subplots(figsize=(12.4, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = [
        (0.025, "Declared analysis", "query data\n+ task contract", BLUE),
        (0.225, "Admissibility gate", "task · truth kind\nK policy · metric", ORANGE),
        (0.425, "Candidate evidence", "target-free neighbours\n+ global comparator", SKY),
        (0.625, "Validation gate", "grouped holdout\n+ source hashes", PURPLE),
        (0.825, "Trade-off gate", "matched Pareto front\n+ failure controls", GREEN),
    ]
    for x, title, body, color in boxes:
        _box(ax, (x, 0.60), 0.15, 0.25, title, body, color)
    for left, right in zip(boxes[:-1], boxes[1:], strict=True):
        _arrow(ax, (left[0] + 0.15, 0.725), (right[0], 0.725))

    outcomes = [
        (0.08, "personalised_set", "all hard gates pass", GREEN),
        (0.31, "global_default", "no advantage over global", BLUE),
        (0.54, "evidence_required", "held-out evidence missing", ORANGE),
        (0.77, "abstain", "no task-valid evidence", RED),
    ]
    for x, title, body, color in outcomes:
        _box(ax, (x, 0.18), 0.16, 0.22, title, body, color)
    _arrow(ax, (0.90, 0.60), (0.90, 0.43))
    ax.plot([0.16, 0.85], [0.48, 0.48], color=INK, lw=1.3)
    for x, *_ in outcomes:
        ax.plot([x + 0.08, x + 0.08], [0.40, 0.48], color=INK, lw=1.3)

    ax.text(
        0.5,
        0.96,
        "HistoWeave converts heterogeneous benchmark results into bounded, auditable actions",
        ha="center",
        va="center",
        fontsize=13,
        weight="bold",
        color=INK,
    )
    ax.text(
        0.5,
        0.07,
        "A DecisionCard records admitted and rejected evidence, checks, action, "
        "controls, and claim boundary.",
        ha="center",
        va="center",
        color=INK,
    )
    _save(fig, "figure1_workflow")

    # The graphical abstract uses the same deterministic evidence-flow drawing.
    src = np.asarray(Image.open(OUT / "figure1_workflow.png").convert("RGB"))
    tifffile.imwrite(
        OUT / "graphical_abstract.tif",
        src,
        photometric="rgb",
        resolution=(350, 350),
        resolutionunit="INCH",
    )
    shutil.copy2(OUT / "figure1_workflow.png", OUT / "graphical_abstract.png")
    shutil.copy2(OUT / "figure1_workflow.svg", OUT / "graphical_abstract.svg")


def build_dlpfc_oracle_figure() -> None:
    matrix = pd.read_csv(
        ROOT / "5x15_spatial_aware" / "performance_matrix_mean_full.csv", index_col=0
    )
    long = pd.read_csv(ROOT / "non_oracle_k_sota" / "benchmark_long.csv")
    methods = matrix.mean(axis=0).sort_values(ascending=False).index
    matrix = matrix.loc[:, methods]

    fig, (ax0, ax1) = plt.subplots(
        1,
        2,
        figsize=(13.0, 5.2),
        gridspec_kw={"width_ratios": [1.65, 1]},
        constrained_layout=True,
    )
    im = ax0.imshow(matrix.to_numpy(), aspect="auto", cmap="viridis", vmin=-0.1, vmax=0.55)
    ax0.set_xticks(np.arange(len(methods)))
    ax0.set_xticklabels(methods, rotation=60, ha="right")
    ax0.set_yticks(np.arange(len(matrix.index)))
    ax0.set_yticklabels(matrix.index)
    ax0.set_xlabel("Method configuration")
    ax0.set_ylabel("DLPFC slice")
    ax0.set_title("A  Oracle-K DLPFC benchmark (mean ARI, three seeds)", loc="left", weight="bold")
    cb = fig.colorbar(im, ax=ax0, fraction=0.025, pad=0.02)
    cb.set_label("Adjusted Rand index")

    subset = long[long["mode"].isin(["oracle", "estimate:silhouette"])].copy()
    subset["mode_label"] = subset["mode"].map(
        {"oracle": "truth-derived K", "estimate:silhouette": "estimated K"}
    )
    x = {"truth-derived K": 0, "estimated K": 1}
    marker = {"spagcn": "o", "stagate": "s"}
    colour = {"spagcn": BLUE, "stagate": ORANGE}
    for method in ["spagcn", "stagate"]:
        part = subset[subset["method"] == method]
        for _dataset, pair in part.groupby("dataset"):
            pair = pair.sort_values("mode_label", key=lambda s: s.map(x))
            ax1.plot(
                [x[v] for v in pair["mode_label"]],
                pair["ari"],
                color=colour[method],
                alpha=0.42,
                lw=1.2,
                marker=marker[method],
                ms=4,
            )
        means = part.groupby("mode_label")["ari"].mean()
        ax1.plot(
            [0, 1],
            [means["truth-derived K"], means["estimated K"]],
            color=colour[method],
            lw=3,
            marker=marker[method],
            ms=8,
            label=f"{method.upper()} mean",
        )
    ax1.set_xticks([0, 1], ["truth-derived K", "estimated K"])
    ax1.set_ylabel("Adjusted Rand index")
    ax1.set_ylim(0, 0.48)
    ax1.set_title("B  Oracle-K sensitivity (seed 42)", loc="left", weight="bold")
    ax1.grid(axis="y", color="#D9E0E6", lw=0.7)
    ax1.legend(frameon=False, loc="lower left")
    ax1.text(
        0.03,
        0.96,
        "SpaGCN mean: 0.299 → 0.237\nSTAGATE mean: 0.232 → 0.219",
        transform=ax1.transAxes,
        va="top",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": PALE, "edgecolor": "none"},
    )
    _save(fig, "figure2_dlpfc_oracle_k")


def build_external_figure() -> None:
    matrix = pd.read_csv(
        ROOT / "benchmark_external_validation" / "performance_matrix_mean.csv",
        index_col=0,
    )
    fig, ax = plt.subplots(figsize=(11.0, 4.7), constrained_layout=True)
    im = ax.imshow(matrix.to_numpy(), aspect="auto", cmap="viridis", vmin=-0.03, vmax=0.70)
    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=55, ha="right")
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels(
        [
            "Visium HD CRC",
            "Xenium lung",
            "Xenium Prime ovarian",
            "Visium mouse brain",
            "MERFISH mouse brain",
        ]
    )
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            if np.isfinite(value):
                ax.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color="white" if value < 0.42 else "black",
                )
    ax.set_title(
        "External oracle-K spatial-domain panel: mean ARI across three seeds",
        loc="left",
        weight="bold",
    )
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("Adjusted Rand index")
    _save(fig, "figure3_external_panel")


def build_validation_figure() -> None:
    selective = json.loads(
        (ROOT / "protocol_endpoints_results" / "selective_regret_coverage.json").read_text()
    )
    rows = selective["curve"]
    wu = pd.read_csv(
        ROOT / "benchmark_external_validation" / "independent_test_wu2021" / "sample_regret.csv"
    )

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12.2, 4.5), constrained_layout=True)
    coverage = np.array([row["coverage"] for row in rows], dtype=float)
    hybrid = np.array([row["mean_regret_abstain_as_global"] for row in rows], dtype=float)
    personalised = float(rows[0]["mean_regret_always_personalised"])
    global_regret = float(rows[0]["mean_regret_always_global"])
    order = np.argsort(coverage)
    ax0.plot(coverage[order], hybrid[order], "-o", color=GREEN, label="selective action")
    ax0.axhline(personalised, color=RED, ls="--", label="always personalised")
    ax0.axhline(global_regret, color=BLUE, ls="-.", label="always global")
    ax0.set_xlabel("Personalisation coverage")
    ax0.set_ylabel("Mean selection regret (ARI)")
    ax0.set_title("A  Grouped selective evaluation (n=20)", loc="left", weight="bold")
    ax0.grid(color="#D9E0E6", lw=0.7)
    ax0.legend(frameon=False)
    ax0.annotate(
        "minimum at zero coverage",
        xy=(0, global_regret),
        xytext=(0.22, global_regret + 0.009),
        arrowprops={"arrowstyle": "->", "color": INK},
    )

    labels = wu["sample"].astype(str)
    regrets = wu["frozen_regret"].astype(float)
    colors = [BLUE if value <= 0.02 else RED for value in regrets]
    ax1.bar(np.arange(len(regrets)), regrets, color=colors)
    ax1.axhline(0.02, color=INK, ls="--", lw=1.2, label="locked margin = 0.02")
    ax1.set_xticks(np.arange(len(labels)), labels, rotation=45, ha="right")
    ax1.set_ylabel("Frozen-policy regret (ARI)")
    ax1.set_title("B  Wu breast-cancer stress test (n=6)", loc="left", weight="bold")
    ax1.grid(axis="y", color="#D9E0E6", lw=0.7)
    ax1.legend(frameon=False)
    ax1.text(
        0.98,
        0.96,
        "mean 0.131\n95% bootstrap CI 0.034–0.236",
        transform=ax1.transAxes,
        ha="right",
        va="top",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": PALE, "edgecolor": "none"},
    )
    _save(fig, "figure4_validation")


def main() -> None:
    build_workflow()
    build_dlpfc_oracle_figure()
    build_external_figure()
    build_validation_figure()


if __name__ == "__main__":
    main()
