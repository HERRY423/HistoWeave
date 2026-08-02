"""Nested leave-one-unit-out evaluation on the aligned multi-study panel.

Outer loop: each independent unit is scored once.
Inner loop: threshold is chosen by leave-one-unit-out on the remaining units only.

This is real-biology personalisation evidence on held-out units (not slice LOOCV).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler

OUT = Path(__file__).resolve().parent / "results"
METHODS = [
    "spagcn",
    "stagate",
    "graphst",
    "bayesspace",
    "banksy",
    "spectral",
    "gaussian_mixture",
    "kmeans",
    "agglomerative",
]
THRESHOLDS = (0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1)
FEATURE_SUBSET = [
    "library_cv",
    "spatial_autocorrelation",
    "effective_rank_90",
    "effective_rank_95",
    "sv_entropy",
]
BOOT_SEED = 20260801


def boot_ci(delta: np.ndarray, *, seed: int) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(delta), size=(10000, len(delta)))
    means = delta[draws].mean(axis=1)
    return float(means.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> int:
    units = pd.DataFrame(
        json.loads((OUT / "meta_panel_units.json").read_text(encoding="utf-8"))["units"]
    )
    feat = json.loads((OUT / "unit_features.json").read_text(encoding="utf-8"))
    rows = []
    for row in feat["units"]:
        rows.append(
            {
                "study_id": row["study_id"],
                "unit_id": str(row["unit_id"]),
                **{k: float(row["features"][k]) for k in FEATURE_SUBSET},
            }
        )
    frame = units.merge(pd.DataFrame(rows), on=["study_id", "unit_id"])
    x = frame[FEATURE_SUBSET].to_numpy(dtype=float)
    y = frame[METHODS].to_numpy(dtype=float)
    ids = [f"{s}:{u}" for s, u in zip(frame["study_id"], frame["unit_id"], strict=True)]

    selected = np.zeros(len(frame), dtype=int)
    globals_ = np.zeros(len(frame), dtype=int)
    thr_used: list[float | None] = []
    gains = np.zeros(len(frame), dtype=float)
    actions: list[dict] = []

    for i in range(len(frame)):
        train = np.ones(len(frame), dtype=bool)
        train[i] = False
        x_tr, y_tr = x[train], y[train]
        n = len(x_tr)
        g = int(y_tr.mean(axis=0).argmax())
        scaler = RobustScaler().fit(x_tr)
        xs = scaler.transform(x_tr)
        inner_sel = np.zeros(n, dtype=int)
        inner_gain = np.zeros(n, dtype=float)
        for j in range(n):
            mask = np.ones(n, dtype=bool)
            mask[j] = False
            nn = NearestNeighbors(n_neighbors=1).fit(xs[mask])
            ind = int(nn.kneighbors(xs[j : j + 1], return_distance=False)[0, 0])
            pos = np.where(mask)[0][ind]
            pick = int(y_tr[pos].argmax())
            inner_sel[j] = pick
            inner_gain[j] = float(y_tr[pos].max() - y_tr[pos, g])

        chosen_thr = None
        chosen_key = None
        for thr in THRESHOLDS:
            covered = (inner_sel != g) & (inner_gain >= thr)
            action = np.where(covered, inner_sel, g)
            best = y_tr.max(axis=1)
            delta = (best - y_tr[np.arange(n), action]) - (best - y_tr[:, g])
            cov = float(covered.mean())
            mean_delta = float(delta.mean())
            # Prefer safer gates: lower regret first, then adequate coverage, then higher thr.
            if cov >= 0.2 and mean_delta <= 0.0:
                key = (mean_delta, -cov, -thr)
                if chosen_key is None or key < chosen_key:
                    chosen_key = key
                    chosen_thr = float(thr)

        nn = NearestNeighbors(n_neighbors=1).fit(xs)
        ind = int(nn.kneighbors(scaler.transform(x[i : i + 1]), return_distance=False)[0, 0])
        pick = int(y_tr[ind].argmax())
        gain = float(y_tr[ind].max() - y_tr[ind, g])
        if chosen_thr is not None and pick != g and gain >= chosen_thr:
            selected[i] = pick
            action_name = "personalised_set"
            method = METHODS[pick]
        else:
            selected[i] = g
            action_name = "global_default" if chosen_thr is not None else "evidence_required"
            method = METHODS[g] if chosen_thr is not None else None
        globals_[i] = g
        thr_used.append(chosen_thr)
        gains[i] = gain
        actions.append(
            {
                "unit_id": ids[i],
                "selected_method": method,
                "action": action_name,
                "predicted_gain": gain,
                "training_global_method": METHODS[g],
                "threshold": chosen_thr,
            }
        )

    best = y.max(axis=1)
    deployed = best - y[np.arange(len(y)), selected]
    global_reg = np.asarray([best[i] - y[i, globals_[i]] for i in range(len(y))], dtype=float)
    delta = deployed - global_reg
    coverage = float((selected != globals_).mean())
    mean_delta, lo, hi = boot_ci(delta, seed=BOOT_SEED)
    success = bool(coverage >= 0.25 and mean_delta < 0.0 and hi < 0.0)
    soft = bool(coverage > 0.0 and mean_delta < 0.0)

    payload = {
        "schema_version": "histoweave.positive_personalisation.nested_louo.v5",
        "protocol_id": "histoweave-positive-personalisation-2026-08",
        "mode": "nested_leave_one_unit_out",
        "feature_subset": FEATURE_SUBSET,
        "n_units": int(len(frame)),
        "studies": sorted(frame["study_id"].unique().tolist()),
        "actions": actions,
        "evaluation": {
            "coverage": coverage,
            "n_personalised": int((selected != globals_).sum()),
            "mean_deployed_regret": float(deployed.mean()),
            "mean_global_regret": float(global_reg.mean()),
            "mean_regret_difference": mean_delta,
            "bootstrap_95_interval_regret_difference": [lo, hi],
            "unit_regret_differences": {
                ids[i]: float(delta[i]) for i in range(len(ids))
            },
        },
        "soft_positive": soft,
        "personalized_value_success": success,
        "claim_boundary": (
            "Nested LOUO on independent donor/patient units from the aligned "
            "non-oracle multi-study panel. Thresholds never use the outer held-out "
            "unit. This is real-biology personalisation evidence, not a prospective "
            "seal of a third untouched study."
        ),
    }
    out = OUT / "nested_louo_results.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "coverage": coverage,
                "mean_regret_difference": mean_delta,
                "ci": [lo, hi],
                "soft_positive": soft,
                "personalized_value_success": success,
                "n_personalised": int((selected != globals_).sum()),
            },
            indent=2,
        )
    )
    return 0 if success or soft else 3


if __name__ == "__main__":
    raise SystemExit(main())
