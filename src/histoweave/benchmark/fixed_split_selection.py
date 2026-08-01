"""Fixed development/calibration method selection without LOOCV.

The selector fits method-score regression on development units, chooses one
predicted-gain gate on a disjoint calibration set, and then emits actions from
label-free test features.  Test outcomes are accepted only by the separate
``evaluate_actions`` function after actions have been frozen.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class CalibrationCandidate:
    threshold: float
    coverage: float
    mean_regret_difference: float
    ci_low: float
    ci_high: float
    eligible: bool


@dataclass(frozen=True)
class FrozenSelectionPolicy:
    methods: tuple[str, ...]
    global_method: str
    alpha: float
    threshold: float | None
    calibration_passed: bool
    noninferiority_margin: float
    minimum_coverage: float
    calibration_candidates: tuple[CalibrationCandidate, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["methods"] = list(self.methods)
        payload["calibration_candidates"] = [
            asdict(row) for row in self.calibration_candidates
        ]
        return payload


@dataclass(frozen=True)
class SelectionAction:
    selected_method: str | None
    action: str
    predicted_gain: float | None
    threshold: float | None


def _matrix(value: np.ndarray, *, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite two-dimensional matrix")
    return array


def _bootstrap_interval(values: np.ndarray, *, seed: int, n_boot: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(values), size=(n_boot, len(values)))
    means = values[draws].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


class FixedSplitMethodScoreSelector:
    """Ridge method-score selector with an explicitly disjoint calibration gate."""

    def __init__(self, methods: Sequence[str], *, alpha: float = 1.0) -> None:
        self.methods = tuple(str(method) for method in methods)
        if len(self.methods) < 2 or len(set(self.methods)) != len(self.methods):
            raise ValueError("methods must contain at least two unique names")
        self.alpha = float(alpha)
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=self.alpha)
        self.global_index: int | None = None
        self.policy: FrozenSelectionPolicy | None = None

    def fit_development(self, features: np.ndarray, performance: np.ndarray) -> None:
        x = _matrix(features, name="development features")
        y = _matrix(performance, name="development performance")
        if len(x) != len(y) or y.shape[1] != len(self.methods):
            raise ValueError("development features/performance/method dimensions do not align")
        transformed = self.scaler.fit_transform(x)
        self.model.fit(transformed, y)
        self.global_index = int(y.mean(axis=0).argmax())
        self.policy = None

    def _scores(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.global_index is None:
            raise RuntimeError("fit_development must run before scoring")
        x = _matrix(features, name="features")
        scores = np.asarray(self.model.predict(self.scaler.transform(x)), dtype=float)
        selected = scores.argmax(axis=1)
        gain = scores[np.arange(len(scores)), selected] - scores[:, self.global_index]
        return scores, selected, gain

    def calibrate(
        self,
        features: np.ndarray,
        performance: np.ndarray,
        *,
        thresholds: Sequence[float],
        minimum_coverage: float = 0.20,
        noninferiority_margin: float = 0.02,
        n_boot: int = 10000,
        seed: int = 0,
    ) -> FrozenSelectionPolicy:
        if self.global_index is None:
            raise RuntimeError("fit_development must run before calibration")
        y = _matrix(performance, name="calibration performance")
        _, selected, gain = self._scores(features)
        if len(y) != len(selected) or y.shape[1] != len(self.methods):
            raise ValueError("calibration features/performance/method dimensions do not align")
        best = y.max(axis=1)
        global_regret = best - y[:, self.global_index]
        candidates: list[CalibrationCandidate] = []
        for index, threshold in enumerate(thresholds):
            threshold = float(threshold)
            covered = (selected != self.global_index) & (gain >= threshold)
            action = np.where(covered, selected, self.global_index)
            regret = best - y[np.arange(len(y)), action]
            delta = regret - global_regret
            lo, hi = _bootstrap_interval(delta, seed=seed + index, n_boot=n_boot)
            coverage = float(covered.mean())
            eligible = bool(
                coverage >= minimum_coverage
                and float(delta.mean()) <= 0.0
                and hi <= noninferiority_margin
            )
            candidates.append(
                CalibrationCandidate(
                    threshold=threshold,
                    coverage=coverage,
                    mean_regret_difference=float(delta.mean()),
                    ci_low=lo,
                    ci_high=hi,
                    eligible=eligible,
                )
            )
        eligible_rows = [row for row in candidates if row.eligible]
        chosen = (
            sorted(
                eligible_rows,
                key=lambda row: (-row.coverage, row.mean_regret_difference, -row.threshold),
            )[0]
            if eligible_rows
            else None
        )
        self.policy = FrozenSelectionPolicy(
            methods=self.methods,
            global_method=self.methods[self.global_index],
            alpha=self.alpha,
            threshold=chosen.threshold if chosen else None,
            calibration_passed=chosen is not None,
            noninferiority_margin=float(noninferiority_margin),
            minimum_coverage=float(minimum_coverage),
            calibration_candidates=tuple(candidates),
        )
        return self.policy

    def predict_actions(self, features: np.ndarray) -> list[SelectionAction]:
        if self.policy is None:
            raise RuntimeError("calibrate must run before test actions are emitted")
        _, selected, gain = self._scores(features)
        if not self.policy.calibration_passed or self.policy.threshold is None:
            return [
                SelectionAction(None, "evidence_required", None, None)
                for _ in range(len(selected))
            ]
        actions = []
        assert self.global_index is not None
        for method_index, predicted_gain in zip(selected, gain, strict=True):
            if method_index != self.global_index and predicted_gain >= self.policy.threshold:
                actions.append(
                    SelectionAction(
                        self.methods[int(method_index)],
                        "personalised_set",
                        float(predicted_gain),
                        self.policy.threshold,
                    )
                )
            else:
                actions.append(
                    SelectionAction(
                        self.methods[self.global_index],
                        "global_default",
                        float(predicted_gain),
                        self.policy.threshold,
                    )
                )
        return actions


def evaluate_actions(
    actions: Sequence[SelectionAction],
    performance: np.ndarray,
    methods: Sequence[str],
    *,
    global_method: str,
) -> dict[str, object]:
    """Evaluate already-frozen actions; never called while fitting/calibrating."""
    y = _matrix(performance, name="test performance")
    method_names = tuple(str(method) for method in methods)
    if y.shape[1] != len(method_names) or len(y) != len(actions):
        raise ValueError("test actions/performance/method dimensions do not align")
    lookup = {method: index for index, method in enumerate(method_names)}
    if global_method not in lookup:
        raise ValueError("global method is outside the fixed panel")
    if any(action.selected_method not in lookup for action in actions):
        return {
            "status": "evidence_required",
            "n_units": len(actions),
            "coverage": 0.0,
            "claim_boundary": "no performance contrast when any frozen action lacks a method",
        }
    selected = np.asarray([lookup[str(action.selected_method)] for action in actions], dtype=int)
    best = y.max(axis=1)
    global_regret = best - y[:, lookup[global_method]]
    deployed_regret = best - y[np.arange(len(y)), selected]
    return {
        "status": "scored",
        "n_units": len(actions),
        "coverage": float(np.mean(selected != lookup[global_method])),
        "mean_deployed_regret": float(deployed_regret.mean()),
        "mean_global_regret": float(global_regret.mean()),
        "mean_regret_difference": float((deployed_regret - global_regret).mean()),
    }
