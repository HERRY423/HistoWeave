"""No-LOOCV positive-selection and fail-closed tests."""

from __future__ import annotations

import numpy as np

from histoweave.benchmark.fixed_split_selection import (
    FixedSplitMethodScoreSelector,
    evaluate_actions,
)


def _panel(seed: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    switch = rng.uniform(-1, 1, n)
    x = np.column_stack([switch, rng.normal(size=(n, 3))])
    y = np.column_stack(
        [
            np.where(switch < 0, 0.8, 0.45),
            np.where(switch >= 0, 0.8, 0.45),
            np.full(n, 0.3),
        ]
    )
    y += rng.normal(0, 0.01, y.shape)
    return x, y


def test_fixed_split_selector_improves_choice_on_unseen_test() -> None:
    train_x, train_y = _panel(1, 120)
    calibration_x, calibration_y = _panel(2, 80)
    test_x, test_y = _panel(3, 100)
    selector = FixedSplitMethodScoreSelector(["spectral", "stagate", "other"])
    selector.fit_development(train_x, train_y)
    policy = selector.calibrate(
        calibration_x,
        calibration_y,
        thresholds=(0.0, 0.02, 0.05, 0.1),
        minimum_coverage=0.2,
        n_boot=200,
        seed=4,
    )
    assert policy.calibration_passed
    actions = selector.predict_actions(test_x)
    scored = evaluate_actions(
        actions, test_y, policy.methods, global_method=policy.global_method
    )
    assert scored["status"] == "scored"
    assert scored["coverage"] >= 0.25
    assert scored["mean_regret_difference"] < -0.05


def test_failed_calibration_emits_evidence_required_not_forced_labels() -> None:
    train_x, train_y = _panel(5, 50)
    calibration_x, calibration_y = _panel(6, 30)
    selector = FixedSplitMethodScoreSelector(["spectral", "stagate", "other"])
    selector.fit_development(train_x, train_y)
    policy = selector.calibrate(
        calibration_x,
        calibration_y,
        thresholds=(10.0,),
        minimum_coverage=0.2,
        n_boot=50,
    )
    assert not policy.calibration_passed
    actions = selector.predict_actions(calibration_x[:3])
    assert {action.action for action in actions} == {"evidence_required"}
    assert {action.selected_method for action in actions} == {None}
