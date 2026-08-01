"""Study-level, same-mask summaries for the two prospective external studies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def bootstrap_mean(values: np.ndarray, *, seed: int, n_boot: int = 10000) -> list[float]:
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(values), size=(n_boot, len(values)))
    means = values[draws].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def summarize_study(
    frame: pd.DataFrame,
    methods: list[str],
    *,
    study_id: str,
    unit_name: str,
    global_method: str | None,
    seed: int,
) -> dict[str, Any]:
    missing = [method for method in methods if method not in frame]
    if missing:
        raise ValueError(f"{study_id}: missing fixed methods {missing}")
    unit_column = frame.columns[0]
    if frame[unit_column].astype(str).duplicated().any():
        raise ValueError(f"{study_id}: duplicate {unit_name} identifiers")
    scores = frame[methods].apply(pd.to_numeric, errors="coerce")
    strict_mask = scores.notna().all(axis=1)
    strict = scores.loc[strict_mask]
    if strict.empty:
        raise ValueError(f"{study_id}: no nine-method complete {unit_name} mask")
    rows = []
    for index, method in enumerate(methods):
        values = strict[method].to_numpy(dtype=float)
        rows.append(
            {
                "method": method,
                "n_available_all_units": int(scores[method].notna().sum()),
                "n_strict_same_mask": int(len(values)),
                "mean_ari_same_mask": float(values.mean()),
                "sd_ari_same_mask": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
                "bootstrap_95_interval_mean_ari": bootstrap_mean(
                    values, seed=seed + index
                ),
            }
        )
    paired = []
    if global_method:
        if global_method not in methods:
            raise ValueError(f"{study_id}: global method is outside the fixed panel")
        best = strict.max(axis=1).to_numpy(dtype=float)
        global_regret = best - strict[global_method].to_numpy(dtype=float)
        for index, method in enumerate(methods):
            method_regret = best - strict[method].to_numpy(dtype=float)
            delta = method_regret - global_regret
            paired.append(
                {
                    "method": method,
                    "comparator": global_method,
                    "n_same_mask": int(len(delta)),
                    "mean_regret_difference_vs_global": float(delta.mean()),
                    "bootstrap_95_interval": bootstrap_mean(delta, seed=seed + 100 + index),
                }
            )
    return {
        "study_id": study_id,
        "unit": unit_name,
        "n_all_units": int(len(frame)),
        "n_strict_nine_method_units": int(strict_mask.sum()),
        "strict_unit_ids": frame.loc[strict_mask, unit_column].astype(str).tolist(),
        "excluded_from_strict_mask": frame.loc[~strict_mask, unit_column].astype(str).tolist(),
        "same_mask_applied_to_every_method": True,
        "method_summary": rows,
        "paired_vs_locked_global": paired,
    }


def analyze(registry_path: Path, root: Path) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    methods = list(registry["methods"])
    studies = []
    pending = []
    for index, study in enumerate(registry["studies"]):
        matrix_path = root / study["matrix"]
        if not matrix_path.is_file():
            pending.append(
                {
                    "study_id": study["study_id"],
                    "status": study["status"],
                    "reason": "patient/donor method matrix is not yet available",
                }
            )
            continue
        frame = pd.read_csv(matrix_path)
        studies.append(
            summarize_study(
                frame,
                methods,
                study_id=str(study["study_id"]),
                unit_name=str(study["unit"]),
                global_method=study.get("locked_global_method"),
                seed=20260801 + 1000 * index,
            )
        )
    return {
        "schema_version": "histoweave.multistudy_same_mask.results.v1",
        "n_registered_studies": len(registry["studies"]),
        "n_completed_studies": len(studies),
        "multistudy_complete": len(studies) == len(registry["studies"]),
        "methods": methods,
        "studies": studies,
        "pending": pending,
        "cross_study_inference": (
            "study-stratified_only_no_pooled_unit_bootstrap"
            if len(studies) >= 2
            else "not_available_until_second_study_is_scored"
        ),
        "claim_boundary": (
            "A same-mask SOTA table is descriptive. Personalised efficacy requires the "
            "separately frozen policy contrast and cannot be inferred from the best method."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry", type=Path, default=Path(__file__).with_name("study_registry.json")
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).with_name("same_mask_results.json")
    )
    args = parser.parse_args()
    payload = analyze(args.registry, args.root)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
