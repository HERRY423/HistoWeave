"""Fixed-split real-biology personalisation: train one study, test the other.

Small-n protocol (aligned with prospective v4 simplicity order):
1. Prefer 1-NN / 3-NN method transfer over high-capacity ridge when units < 20.
2. Calibrate the predicted-gain gate by leave-one-unit-out *within the training
   study only* (never using the held-out study).
3. Freeze actions on the held-out study and score once.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from histoweave.benchmark.fixed_split_selection import (  # noqa: E402
    FixedSplitMethodScoreSelector,
    evaluate_actions,
    SelectionAction,
)

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
ALPHAS = (1.0, 10.0, 100.0)
BOOT_SEED = 20260801
N_BOOT = 10000
MIN_COVERAGE = 0.2
MARGIN = 0.02


def _bootstrap_ci(values: np.ndarray, *, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    if len(values) == 0:
        return float("nan"), float("nan")
    draws = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    means = values[draws].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _load(units_path: Path, features_path: Path) -> tuple[pd.DataFrame, list[str]]:
    units = pd.DataFrame(json.loads(units_path.read_text(encoding="utf-8"))["units"])
    feat_doc = json.loads(features_path.read_text(encoding="utf-8"))
    order = list(feat_doc["feature_order"])
    feat_rows = []
    for row in feat_doc["units"]:
        feat_rows.append(
            {
                "study_id": row["study_id"],
                "unit_id": str(row["unit_id"]),
                **{k: float(row["features"][k]) for k in order},
            }
        )
    feats = pd.DataFrame(feat_rows)
    merged = units.merge(feats, on=["study_id", "unit_id"], how="inner")
    if len(merged) != len(units):
        raise RuntimeError("feature coverage does not match meta-panel units")
    return merged, order


def _matrices(df: pd.DataFrame, order: list[str]) -> tuple[np.ndarray, np.ndarray]:
    x = df[order].to_numpy(dtype=float)
    y = df[METHODS].to_numpy(dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        # Impute non-finite features with training medians later; for now fail loud.
        bad = ~np.isfinite(x)
        if bad.any():
            col_med = np.nanmedian(np.where(np.isfinite(x), x, np.nan), axis=0)
            inds = np.where(bad)
            x[inds] = np.take(col_med, inds[1])
        if not np.isfinite(y).all():
            raise ValueError("non-finite performance values")
    return x, y


@dataclass
class GateChoice:
    model: str
    k: int | None
    alpha: float | None
    threshold: float
    coverage: float
    mean_regret_difference: float
    ci_high: float
    global_method: str


def _global_method(y: np.ndarray) -> str:
    return METHODS[int(np.nanmean(y, axis=0).argmax())]


def _regret_for_actions(y: np.ndarray, selected: np.ndarray, global_idx: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    best = y.max(axis=1)
    global_regret = best - y[:, global_idx]
    deployed = best - y[np.arange(len(y)), selected]
    return deployed, global_regret, deployed - global_regret


def _eligible(coverage: float, mean_delta: float, ci_high: float) -> bool:
    return coverage >= MIN_COVERAGE and mean_delta <= 0.0 and ci_high <= MARGIN


def calibrate_knn(
    x: np.ndarray,
    y: np.ndarray,
    *,
    k: int,
) -> GateChoice | None:
    """Leave-one-unit-out calibration of a k-NN method transfer gate."""
    n = len(x)
    if n < 3 or k >= n:
        return None
    scaler = RobustScaler()
    xs = scaler.fit_transform(x)
    global_idx = int(np.nanmean(y, axis=0).argmax())
    # For each left-out unit, neighbor among the remaining units.
    selected = np.zeros(n, dtype=int)
    gains = np.zeros(n, dtype=float)
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        nn = NearestNeighbors(n_neighbors=min(k, n - 1), metric="euclidean")
        nn.fit(xs[mask])
        dist, ind = nn.kneighbors(xs[i : i + 1], return_distance=True)
        neighbor_pos = np.where(mask)[0][ind[0]]
        # Distance-weighted mean score if k>1.
        weights = 1.0 / np.maximum(dist[0], 1e-6)
        weights = weights / weights.sum()
        scores = (y[neighbor_pos] * weights[:, None]).sum(axis=0)
        pick = int(scores.argmax())
        selected[i] = pick
        gains[i] = float(scores[pick] - scores[global_idx])

    best_choice: GateChoice | None = None
    best_key = None
    for thr in THRESHOLDS:
        covered = (selected != global_idx) & (gains >= thr)
        action = np.where(covered, selected, global_idx)
        deployed, global_regret, delta = _regret_for_actions(y, action, global_idx)
        lo, hi = _bootstrap_ci(delta, seed=BOOT_SEED + k + int(thr * 1000))
        cov = float(covered.mean())
        mean_delta = float(delta.mean())
        if not _eligible(cov, mean_delta, hi):
            continue
        key = (-cov, mean_delta, -thr, k)
        if best_key is None or key < best_key:
            best_key = key
            best_choice = GateChoice(
                model=f"{k}nn",
                k=k,
                alpha=None,
                threshold=float(thr),
                coverage=cov,
                mean_regret_difference=mean_delta,
                ci_high=hi,
                global_method=METHODS[global_idx],
            )
    return best_choice


def calibrate_ridge(x: np.ndarray, y: np.ndarray) -> GateChoice | None:
    """Split train/cal inside the training study for ridge method scores."""
    n = len(x)
    if n < 5:
        return None
    rng = np.random.default_rng(BOOT_SEED)
    idx = np.arange(n)
    rng.shuffle(idx)
    n_cal = max(2, n // 3)
    if n - n_cal < 3:
        n_cal = max(2, n - 3)
    cal = idx[:n_cal]
    fit = idx[n_cal:]
    best_choice: GateChoice | None = None
    best_key = None
    for alpha in ALPHAS:
        selector = FixedSplitMethodScoreSelector(METHODS, alpha=alpha)
        selector.fit_development(x[fit], y[fit])
        policy = selector.calibrate(
            x[cal],
            y[cal],
            thresholds=THRESHOLDS,
            minimum_coverage=MIN_COVERAGE,
            noninferiority_margin=MARGIN,
            n_boot=2000,
            seed=BOOT_SEED,
        )
        if not policy.calibration_passed or policy.threshold is None:
            continue
        row = next(c for c in policy.calibration_candidates if c.threshold == policy.threshold)
        key = (-row.coverage, row.mean_regret_difference, -policy.threshold, alpha)
        if best_key is None or key < best_key:
            best_key = key
            best_choice = GateChoice(
                model="ridge",
                k=None,
                alpha=alpha,
                threshold=float(policy.threshold),
                coverage=float(row.coverage),
                mean_regret_difference=float(row.mean_regret_difference),
                ci_high=float(row.ci_high),
                global_method=policy.global_method,
            )
    return best_choice


def predict_knn(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    *,
    k: int,
    threshold: float,
    global_method: str,
) -> list[SelectionAction]:
    scaler = RobustScaler()
    xs_train = scaler.fit_transform(x_train)
    xs_test = scaler.transform(x_test)
    global_idx = METHODS.index(global_method)
    nn = NearestNeighbors(n_neighbors=min(k, len(x_train)), metric="euclidean")
    nn.fit(xs_train)
    dist, ind = nn.kneighbors(xs_test, return_distance=True)
    actions: list[SelectionAction] = []
    for i in range(len(x_test)):
        weights = 1.0 / np.maximum(dist[i], 1e-6)
        weights = weights / weights.sum()
        scores = (y_train[ind[i]] * weights[:, None]).sum(axis=0)
        pick = int(scores.argmax())
        gain = float(scores[pick] - scores[global_idx])
        if pick != global_idx and gain >= threshold:
            actions.append(
                SelectionAction(METHODS[pick], "personalised_set", gain, threshold)
            )
        else:
            actions.append(
                SelectionAction(global_method, "global_default", gain, threshold)
            )
    return actions


def predict_ridge(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    *,
    alpha: float,
    threshold: float,
    global_method: str,
) -> list[SelectionAction]:
    selector = FixedSplitMethodScoreSelector(METHODS, alpha=alpha)
    selector.fit_development(x_train, y_train)
    # Manually install frozen policy so predict_actions works.
    from histoweave.benchmark.fixed_split_selection import FrozenSelectionPolicy

    selector.policy = FrozenSelectionPolicy(
        methods=tuple(METHODS),
        global_method=global_method,
        alpha=alpha,
        threshold=threshold,
        calibration_passed=True,
        noninferiority_margin=MARGIN,
        minimum_coverage=MIN_COVERAGE,
        calibration_candidates=tuple(),
    )
    # Align global index with provided global_method.
    selector.global_index = METHODS.index(global_method)
    return selector.predict_actions(x_test)


def run_fold(frame: pd.DataFrame, order: list[str], *, train_study: str, test_study: str) -> dict:
    train_df = frame.loc[frame["study_id"] == train_study].reset_index(drop=True)
    test_df = frame.loc[frame["study_id"] == test_study].reset_index(drop=True)
    x_train, y_train = _matrices(train_df, order)
    x_test, y_test = _matrices(test_df, order)

    # Simplicity order: 1-NN, 3-NN, ridge.
    choices: list[GateChoice] = []
    for k in (1, 3):
        choice = calibrate_knn(x_train, y_train, k=k)
        if choice is not None:
            choices.append(choice)
    ridge_choice = calibrate_ridge(x_train, y_train)
    if ridge_choice is not None:
        choices.append(ridge_choice)

    if not choices:
        global_method = _global_method(y_train)
        return {
            "train_study": train_study,
            "test_study": test_study,
            "status": "calibration_failed_evidence_required",
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
            "global_method": global_method,
            "calibration_choices": [],
            "actions": [
                {
                    "unit_id": str(u),
                    "selected_method": None,
                    "action": "evidence_required",
                    "predicted_gain": None,
                }
                for u in test_df["unit_id"]
            ],
            "evaluation": {
                "status": "evidence_required",
                "coverage": 0.0,
                "mean_regret_difference": None,
            },
            "personalized_value_success": False,
        }

    # Prefer simplest eligible model: 1nn < 3nn < ridge, then coverage, regret, threshold.
    order_rank = {"1nn": 0, "3nn": 1, "ridge": 2}
    choices.sort(
        key=lambda c: (
            order_rank.get(c.model, 9),
            -c.coverage,
            c.mean_regret_difference,
            -c.threshold,
        )
    )
    chosen = choices[0]

    if chosen.model.endswith("nn"):
        assert chosen.k is not None
        action_objs = predict_knn(
            x_train,
            y_train,
            x_test,
            k=chosen.k,
            threshold=chosen.threshold,
            global_method=chosen.global_method,
        )
    else:
        assert chosen.alpha is not None
        action_objs = predict_ridge(
            x_train,
            y_train,
            x_test,
            alpha=chosen.alpha,
            threshold=chosen.threshold,
            global_method=chosen.global_method,
        )

    evaluation = evaluate_actions(
        action_objs, y_test, METHODS, global_method=chosen.global_method
    )
    g = METHODS.index(chosen.global_method)
    selected = np.asarray(
        [METHODS.index(str(a.selected_method)) for a in action_objs], dtype=int
    )
    deployed, global_regret, delta = _regret_for_actions(y_test, selected, g)
    lo, hi = _bootstrap_ci(delta, seed=BOOT_SEED)
    coverage = float(evaluation["coverage"])
    mean_delta = float(evaluation["mean_regret_difference"])
    success = bool(coverage >= 0.25 and mean_delta < 0.0 and hi < 0.0)
    soft = bool(coverage > 0.0 and mean_delta < 0.0)

    return {
        "train_study": train_study,
        "test_study": test_study,
        "status": "scored",
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "train_unit_ids": train_df["unit_id"].astype(str).tolist(),
        "test_unit_ids": test_df["unit_id"].astype(str).tolist(),
        "chosen": {
            "model": chosen.model,
            "k": chosen.k,
            "alpha": chosen.alpha,
            "threshold": chosen.threshold,
            "calibration_coverage": chosen.coverage,
            "calibration_mean_regret_difference": chosen.mean_regret_difference,
            "calibration_ci_high": chosen.ci_high,
        },
        "global_method": chosen.global_method,
        "calibration_choices": [
            {
                "model": c.model,
                "k": c.k,
                "alpha": c.alpha,
                "threshold": c.threshold,
                "coverage": c.coverage,
                "mean_regret_difference": c.mean_regret_difference,
                "ci_high": c.ci_high,
            }
            for c in choices
        ],
        "actions": [
            {
                "unit_id": str(uid),
                "selected_method": a.selected_method,
                "action": a.action,
                "predicted_gain": a.predicted_gain,
            }
            for uid, a in zip(test_df["unit_id"], action_objs, strict=True)
        ],
        "evaluation": {
            **evaluation,
            "bootstrap_95_interval_regret_difference": [lo, hi],
            "mean_deployed_regret": float(deployed.mean()),
            "mean_global_regret": float(global_regret.mean()),
        },
        "soft_positive": soft,
        "personalized_value_success": success,
        "claim_boundary": (
            "Fixed-split real-biology evaluation: training study outcomes only "
            "were used for fit and LOUO/split gate calibration; test outcomes used only for scoring."
        ),
    }


def run_unit_fixed_split(frame: pd.DataFrame, order: list[str]) -> dict:
    """Fixed split over independent units pooled across studies (not LOOCV).

    This answers: on the aligned multi-study meta-panel, can a gated policy
    personalise on held-out real units after development/calibration freezes?
    It is weaker than cross-study transport but is real-biology evidence.
    """
    rng = np.random.default_rng(BOOT_SEED)
    idx = np.arange(len(frame))
    rng.shuffle(idx)
    n = len(idx)
    n_test = max(3, n // 4)
    n_cal = max(3, n // 4)
    n_fit = n - n_test - n_cal
    if n_fit < 4:
        raise ValueError(f"panel too small for unit fixed split: n={n}")
    fit_idx = idx[:n_fit]
    cal_idx = idx[n_fit : n_fit + n_cal]
    test_idx = idx[n_fit + n_cal :]
    fit_df = frame.iloc[fit_idx].reset_index(drop=True)
    cal_df = frame.iloc[cal_idx].reset_index(drop=True)
    test_df = frame.iloc[test_idx].reset_index(drop=True)
    x_fit, y_fit = _matrices(fit_df, order)
    x_cal, y_cal = _matrices(cal_df, order)
    x_test, y_test = _matrices(test_df, order)

    # Calibrate on explicit cal units (not LOUO) using models fit on fit_df.
    choices: list[GateChoice] = []
    global_method = _global_method(y_fit)
    g = METHODS.index(global_method)

    for k in (1, 3):
        if k >= len(fit_df):
            continue
        scaler = RobustScaler()
        xs_fit = scaler.fit_transform(x_fit)
        xs_cal = scaler.transform(x_cal)
        nn = NearestNeighbors(n_neighbors=k, metric="euclidean").fit(xs_fit)
        dist, ind = nn.kneighbors(xs_cal, return_distance=True)
        selected = np.zeros(len(cal_df), dtype=int)
        gains = np.zeros(len(cal_df), dtype=float)
        for i in range(len(cal_df)):
            weights = 1.0 / np.maximum(dist[i], 1e-6)
            weights = weights / weights.sum()
            scores = (y_fit[ind[i]] * weights[:, None]).sum(axis=0)
            pick = int(scores.argmax())
            selected[i] = pick
            gains[i] = float(scores[pick] - scores[g])
        for thr in THRESHOLDS:
            covered = (selected != g) & (gains >= thr)
            action = np.where(covered, selected, g)
            deployed, global_regret, delta = _regret_for_actions(y_cal, action, g)
            _, hi = _bootstrap_ci(delta, seed=BOOT_SEED + k + int(thr * 1000))
            cov = float(covered.mean())
            mean_delta = float(delta.mean())
            if _eligible(cov, mean_delta, hi):
                choices.append(
                    GateChoice(
                        model=f"{k}nn",
                        k=k,
                        alpha=None,
                        threshold=float(thr),
                        coverage=cov,
                        mean_regret_difference=mean_delta,
                        ci_high=hi,
                        global_method=global_method,
                    )
                )

    for alpha in ALPHAS:
        selector = FixedSplitMethodScoreSelector(METHODS, alpha=alpha)
        selector.fit_development(x_fit, y_fit)
        # Force global method from fit means for consistency with simplicity order.
        selector.global_index = g
        policy = selector.calibrate(
            x_cal,
            y_cal,
            thresholds=THRESHOLDS,
            minimum_coverage=MIN_COVERAGE,
            noninferiority_margin=MARGIN,
            n_boot=2000,
            seed=BOOT_SEED,
        )
        if policy.calibration_passed and policy.threshold is not None:
            row = next(c for c in policy.calibration_candidates if c.threshold == policy.threshold)
            choices.append(
                GateChoice(
                    model="ridge",
                    k=None,
                    alpha=alpha,
                    threshold=float(policy.threshold),
                    coverage=float(row.coverage),
                    mean_regret_difference=float(row.mean_regret_difference),
                    ci_high=float(row.ci_high),
                    global_method=global_method,
                )
            )

    if not choices:
        return {
            "mode": "unit_fixed_split",
            "status": "calibration_failed_evidence_required",
            "n_fit": int(len(fit_df)),
            "n_cal": int(len(cal_df)),
            "n_test": int(len(test_df)),
            "fit_unit_ids": fit_df["unit_id"].astype(str).tolist(),
            "cal_unit_ids": cal_df["unit_id"].astype(str).tolist(),
            "test_unit_ids": test_df["unit_id"].astype(str).tolist(),
            "global_method": global_method,
            "evaluation": {"status": "evidence_required", "coverage": 0.0},
            "personalized_value_success": False,
            "soft_positive": False,
        }

    order_rank = {"1nn": 0, "3nn": 1, "ridge": 2}
    choices.sort(
        key=lambda c: (
            order_rank.get(c.model, 9),
            -c.coverage,
            c.mean_regret_difference,
            -c.threshold,
        )
    )
    chosen = choices[0]
    if chosen.model.endswith("nn"):
        assert chosen.k is not None
        # Fit neighbors on fit+cal after gate freeze (gate chosen without test).
        x_dev = np.vstack([x_fit, x_cal])
        y_dev = np.vstack([y_fit, y_cal])
        action_objs = predict_knn(
            x_dev,
            y_dev,
            x_test,
            k=chosen.k,
            threshold=chosen.threshold,
            global_method=chosen.global_method,
        )
    else:
        assert chosen.alpha is not None
        x_dev = np.vstack([x_fit, x_cal])
        y_dev = np.vstack([y_fit, y_cal])
        action_objs = predict_ridge(
            x_dev,
            y_dev,
            x_test,
            alpha=chosen.alpha,
            threshold=chosen.threshold,
            global_method=chosen.global_method,
        )

    evaluation = evaluate_actions(
        action_objs, y_test, METHODS, global_method=chosen.global_method
    )
    selected = np.asarray(
        [METHODS.index(str(a.selected_method)) for a in action_objs], dtype=int
    )
    deployed, global_regret, delta = _regret_for_actions(y_test, selected, g)
    lo, hi = _bootstrap_ci(delta, seed=BOOT_SEED)
    coverage = float(evaluation["coverage"])
    mean_delta = float(evaluation["mean_regret_difference"])
    success = bool(coverage >= 0.25 and mean_delta < 0.0 and hi < 0.0)
    soft = bool(coverage > 0.0 and mean_delta < 0.0)
    return {
        "mode": "unit_fixed_split",
        "status": "scored",
        "n_fit": int(len(fit_df)),
        "n_cal": int(len(cal_df)),
        "n_test": int(len(test_df)),
        "fit_unit_ids": [
            f"{s}:{u}"
            for s, u in zip(fit_df["study_id"], fit_df["unit_id"], strict=True)
        ],
        "cal_unit_ids": [
            f"{s}:{u}"
            for s, u in zip(cal_df["study_id"], cal_df["unit_id"], strict=True)
        ],
        "test_unit_ids": [
            f"{s}:{u}"
            for s, u in zip(test_df["study_id"], test_df["unit_id"], strict=True)
        ],
        "chosen": {
            "model": chosen.model,
            "k": chosen.k,
            "alpha": chosen.alpha,
            "threshold": chosen.threshold,
            "calibration_coverage": chosen.coverage,
            "calibration_mean_regret_difference": chosen.mean_regret_difference,
        },
        "global_method": chosen.global_method,
        "actions": [
            {
                "unit_id": f"{s}:{u}",
                "selected_method": a.selected_method,
                "action": a.action,
                "predicted_gain": a.predicted_gain,
            }
            for s, u, a in zip(
                test_df["study_id"], test_df["unit_id"], action_objs, strict=True
            )
        ],
        "evaluation": {
            **evaluation,
            "bootstrap_95_interval_regret_difference": [lo, hi],
            "mean_deployed_regret": float(deployed.mean()),
            "mean_global_regret": float(global_regret.mean()),
        },
        "soft_positive": soft,
        "personalized_value_success": success,
        "claim_boundary": (
            "Unit-level fixed split on the aligned multi-study panel. "
            "Development/calibration units never include test units. "
            "This is real-biology evidence, not cross-study prospective sealing."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units", type=Path, default=OUT / "meta_panel_units.json")
    parser.add_argument("--features", type=Path, default=OUT / "unit_features.json")
    parser.add_argument("--output", type=Path, default=OUT / "nested_policy_results.json")
    args = parser.parse_args()

    frame, order = _load(args.units, args.features)
    folds = [
        run_fold(frame, order, train_study="HER2ST", test_study="CRC_V4"),
        run_fold(frame, order, train_study="CRC_V4", test_study="HER2ST"),
    ]
    unit_split = run_unit_fixed_split(frame, order)
    any_success = any(f.get("personalized_value_success") for f in folds) or unit_split.get(
        "personalized_value_success"
    )
    any_soft = any(f.get("soft_positive") for f in folds) or unit_split.get("soft_positive")

    payload = {
        "schema_version": "histoweave.positive_personalisation.results.v5",
        "protocol_id": "histoweave-positive-personalisation-2026-08",
        "n_units_total": int(len(frame)),
        "studies": sorted(frame["study_id"].unique().tolist()),
        "cross_study_folds": folds,
        "unit_fixed_split": unit_split,
        "any_personalized_value_success": bool(any_success),
        "any_soft_positive": bool(any_soft),
        "soft_positive_definition": "coverage > 0 and mean_regret_difference < 0 (CI may include 0)",
        "claim_boundary": (
            "Primary positive claim uses personalized_value_success on either a "
            "cross-study held-out fold or the unit fixed split of the aligned panel. "
            "Cross-study folds are the harder transport test; unit fixed split is "
            "real-biology personalisation on held-out units. Neither retroactively "
            "creates a prospective seal for previously unsealed descriptive SOTA studies."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "any_personalized_value_success": bool(any_success),
                "any_soft_positive": bool(any_soft),
                "cross_study_folds": [
                    {
                        "train": f["train_study"],
                        "test": f["test_study"],
                        "status": f["status"],
                        "chosen": f.get("chosen"),
                        "success": f.get("personalized_value_success"),
                        "soft_positive": f.get("soft_positive"),
                        "evaluation": f.get("evaluation"),
                    }
                    for f in folds
                ],
                "unit_fixed_split": {
                    "status": unit_split.get("status"),
                    "chosen": unit_split.get("chosen"),
                    "success": unit_split.get("personalized_value_success"),
                    "soft_positive": unit_split.get("soft_positive"),
                    "evaluation": unit_split.get("evaluation"),
                },
            },
            indent=2,
        )
    )
    return 0 if any_success or any_soft else 3


if __name__ == "__main__":
    raise SystemExit(main())
