"""Fixed-split synthetic validation of positive selection, without LOOCV.

The protocol is construct validity only.  Training fits the neighbour model,
calibration chooses a gate by a locked rule, and two independently generated
test panels assess positive selection and no-signal safety.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

METHODS = (
    "spectral",
    "stagate",
    "spagcn",
    "graphst",
    "bayesspace",
    "banksy",
    "gaussian_mixture",
    "kmeans",
    "agglomerative",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _features(seed: int, n: int, *, signal: bool = True) -> np.ndarray:
    rng = np.random.default_rng(seed)
    switch = rng.uniform(-1.0, 1.0, n) if signal else np.zeros(n)
    return np.column_stack([switch, rng.normal(size=(n, 8))])


def _performance(
    seed: int,
    x: np.ndarray,
    *,
    signal: bool = True,
    null_global_index: int | None = None,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    perf = np.full((len(x), len(METHODS)), 0.35, dtype=float)
    if signal:
        perf[:, 0] = np.where(x[:, 0] < 0, 0.78, 0.48)
        perf[:, 1] = np.where(x[:, 0] >= 0, 0.78, 0.48)
    else:
        if null_global_index is None:
            raise ValueError("null_global_index is required for a no-signal panel")
        perf[:, null_global_index] = 0.78
    return np.clip(perf + rng.normal(0.0, 0.03, perf.shape), 0.0, 1.0)


def _predict(
    model: Ridge, query_x: np.ndarray, global_index: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    scores = np.asarray(model.predict(query_x), dtype=float)
    selected = scores.argmax(axis=1)
    predicted_gain = scores[np.arange(len(scores)), selected] - scores[:, global_index]
    return scores, selected, predicted_gain


def _bootstrap_interval(values: np.ndarray, *, seed: int, n_boot: int = 10000) -> list[float]:
    if len(values) == 0:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(values), size=(n_boot, len(values)))
    means = values[draws].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def _evaluate(
    scores: np.ndarray,
    selected: np.ndarray,
    confidence: np.ndarray,
    perf: np.ndarray,
    *,
    global_index: int,
    threshold: float,
    bootstrap_seed: int,
) -> dict[str, Any]:
    reference_advantage = scores[np.arange(len(scores)), selected] > scores[:, global_index]
    covered = (selected != global_index) & reference_advantage & (confidence >= threshold)
    action = np.where(covered, selected, global_index)
    best_index = perf.argmax(axis=1)
    best = perf[np.arange(len(perf)), best_index]
    global_regret = best - perf[:, global_index]
    deployed_regret = best - perf[np.arange(len(perf)), action]
    delta = deployed_regret - global_regret
    opportunity = best_index != global_index
    return {
        "threshold": float(threshold),
        "coverage": float(covered.mean()),
        "n_covered": int(covered.sum()),
        "deployed_regret": float(deployed_regret.mean()),
        "always_global_regret": float(global_regret.mean()),
        "mean_regret_difference": float(delta.mean()),
        "bootstrap_95_interval_regret_difference": _bootstrap_interval(
            delta, seed=bootstrap_seed
        ),
        "covered_action_accuracy": (
            float((action[covered] == best_index[covered]).mean()) if covered.any() else None
        ),
        "non_global_opportunity_recall": (
            float((covered & (action == best_index))[opportunity].mean())
            if opportunity.any()
            else None
        ),
        "global_index": int(global_index),
        "global_method": METHODS[global_index],
        "selected_methods_on_covered_units": sorted({METHODS[i] for i in action[covered]}),
        "same_mask_complete": bool(np.isfinite(perf).all()),
    }


def run(protocol_path: Path, output: Path) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    base = int(protocol["seeds"]["generator_base"])
    boot = int(protocol["seeds"]["bootstrap"])
    sizes = protocol["partition"]

    train_x = _features(base, int(sizes["training_units"]))
    signal_calibration_x = _features(base + 1, int(sizes["signal_calibration_units"]))
    null_calibration_x = _features(
        base + 2, int(sizes["null_calibration_units"]), signal=False
    )
    signal_x = _features(base + 3, int(sizes["signal_test_units"]))
    null_x = _features(base + 4, int(sizes["null_test_units"]), signal=False)
    train_perf = _performance(base + 10, train_x)
    signal_calibration_perf = _performance(base + 11, signal_calibration_x)
    signal_perf = _performance(base + 13, signal_x)
    scaler = StandardScaler().fit(train_x)
    train_z = scaler.transform(train_x)
    global_index = int(train_perf.mean(axis=0).argmax())
    null_perf = _performance(
        base + 14, null_x, signal=False, null_global_index=global_index
    )
    null_calibration_perf = _performance(
        base + 12,
        null_calibration_x,
        signal=False,
        null_global_index=global_index,
    )
    model = Ridge(alpha=1.0).fit(train_z, train_perf)
    cal_scores, cal_selected, cal_confidence = _predict(
        model, scaler.transform(signal_calibration_x), global_index
    )
    null_cal_scores, null_cal_selected, null_cal_confidence = _predict(
        model, scaler.transform(null_calibration_x), global_index
    )
    calibration_rows = []
    for i, threshold in enumerate(protocol["model"]["threshold_grid"]):
        signal_row = _evaluate(
                cal_scores,
                cal_selected,
                cal_confidence,
                signal_calibration_perf,
                global_index=global_index,
                threshold=float(threshold),
                bootstrap_seed=boot + i,
        )
        null_row = _evaluate(
            null_cal_scores,
            null_cal_selected,
            null_cal_confidence,
            null_calibration_perf,
            global_index=global_index,
            threshold=float(threshold),
            bootstrap_seed=boot + 50 + i,
        )
        calibration_rows.append(
            {"threshold": float(threshold), "signal": signal_row, "null": null_row}
        )
    margin = float(protocol["model"]["noninferiority_margin"])
    eligible = [
        row
        for row in calibration_rows
        if row["signal"]["coverage"] >= 0.20
        and row["signal"]["mean_regret_difference"] < 0.0
        and row["signal"]["bootstrap_95_interval_regret_difference"][1] <= margin
        and row["null"]["bootstrap_95_interval_regret_difference"][1] <= margin
    ]
    if not eligible:
        raise RuntimeError("no calibration threshold meets the locked selection rule")
    chosen = sorted(
        eligible,
        key=lambda row: (
            -row["signal"]["coverage"],
            row["signal"]["deployed_regret"],
            -row["threshold"],
        ),
    )[0]
    threshold = float(chosen["threshold"])

    signal_scores, signal_selected, signal_confidence = _predict(
        model, scaler.transform(signal_x), global_index
    )
    null_scores, null_selected, null_confidence = _predict(
        model, scaler.transform(null_x), global_index
    )
    signal = _evaluate(
        signal_scores,
        signal_selected,
        signal_confidence,
        signal_perf,
        global_index=global_index,
        threshold=threshold,
        bootstrap_seed=boot + 100,
    )
    null = _evaluate(
        null_scores,
        null_selected,
        null_confidence,
        null_perf,
        global_index=global_index,
        threshold=threshold,
        bootstrap_seed=boot + 101,
    )

    success_cfg = protocol["signal_test_success"]
    signal_checks = {
        "coverage": signal["coverage"] >= float(success_cfg["coverage_floor"]),
        "covered_action_accuracy": signal["covered_action_accuracy"] is not None
        and signal["covered_action_accuracy"]
        >= float(success_cfg["covered_action_accuracy_floor"]),
        "opportunity_recall": signal["non_global_opportunity_recall"] is not None
        and signal["non_global_opportunity_recall"]
        >= float(success_cfg["non_global_opportunity_recall_floor"]),
        "superior_deployed_regret": signal["bootstrap_95_interval_regret_difference"][1]
        < 0.0,
        "same_mask_complete": signal["same_mask_complete"],
    }
    null_checks = {
        "noninferior_deployed_regret": null["bootstrap_95_interval_regret_difference"][1]
        <= margin,
        "same_mask_complete": null["same_mask_complete"],
    }
    payload = {
        "schema_version": "histoweave.synthetic_selection.results.v2.2",
        "protocol_sha256": _sha256(protocol_path),
        "protocol_status": protocol["status"],
        "global_method": METHODS[global_index],
        "calibration": {
            "selected_threshold": threshold,
            "selection_rule": protocol["model"]["calibration_rule"],
            "threshold_rows": calibration_rows,
        },
        "signal_test": signal,
        "null_test": null,
        "signal_checks": signal_checks,
        "null_checks": null_checks,
        "success": bool(all(signal_checks.values()) and all(null_checks.values())),
        "claim_boundary": protocol["claim_boundary"],
        "v3_failure_retained": True,
        "invalid_v2_0_run_retained": True,
        "failed_v2_1_run_retained": True,
    }
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "results.json", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--protocol", type=Path, default=Path(__file__).with_name("protocol.json")
    )
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results"))
    args = parser.parse_args()
    payload = run(args.protocol, args.output)
    if not payload["success"]:
        raise SystemExit("locked synthetic v2 success conditions were not met")


if __name__ == "__main__":
    main()
