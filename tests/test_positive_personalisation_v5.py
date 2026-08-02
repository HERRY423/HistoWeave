"""Contract tests for positive personalisation v5 meta-panel and policy pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "positive_personalisation_v5"


def test_build_meta_panel_complete(tmp_path: Path) -> None:
    import importlib.util

    module_path = ROOT / "positive_personalisation_v5" / "build_meta_panel.py"
    spec = importlib.util.spec_from_file_location("build_meta_panel_v5", module_path)
    assert spec and spec.loader
    bmp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bmp)

    her2 = pd.DataFrame(
        {
            "donor_id": list("ABCDEF"),
            **{m: np.linspace(0.1, 0.6, 6) + i * 0.01 for i, m in enumerate(bmp.METHODS)},
        }
    )
    her2.loc[0:2, "banksy"] = 0.9
    her2.loc[3:5, "kmeans"] = 0.9
    crc = pd.DataFrame(
        {
            "patient_id": [f"P{i}" for i in range(7)],
            **{m: np.linspace(0.15, 0.55, 7) + i * 0.005 for i, m in enumerate(bmp.METHODS)},
        }
    )
    crc.loc[0:2, "spagcn"] = 0.85
    crc.loc[3:6, "stagate"] = 0.85
    her2_path = tmp_path / "her2.csv"
    crc_path = tmp_path / "crc.csv"
    her2.to_csv(her2_path, index=False)
    crc.to_csv(crc_path, index=False)
    out = tmp_path / "out"

    her2_units = bmp.load_unit_matrix(her2_path, "HER2ST", "donor")
    crc_units = bmp.load_unit_matrix(crc_path, "CRC_V4", "patient")
    units = pd.concat([her2_units, crc_units], ignore_index=True)
    assert len(units) == 13
    long_rows = bmp.expand_seed_long(units)
    assert len(long_rows) == 13 * len(bmp.METHODS) * 3
    assert {row["k_policy"] for row in long_rows} == {"estimate"}


def test_fixed_split_can_succeed_on_planted_switch() -> None:
    from histoweave.benchmark.fixed_split_selection import (
        FixedSplitMethodScoreSelector,
        evaluate_actions,
    )

    rng = np.random.default_rng(0)
    n_train, n_cal, n_test = 40, 20, 30
    switch_train = rng.uniform(-1, 1, n_train)
    switch_cal = rng.uniform(-1, 1, n_cal)
    switch_test = rng.uniform(-1, 1, n_test)

    def panel(switch: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x = np.column_stack([switch, rng.normal(size=(len(switch), 3))])
        y = np.column_stack(
            [
                np.where(switch < 0, 0.8, 0.4),
                np.where(switch >= 0, 0.8, 0.4),
                np.full(len(switch), 0.3),
            ]
        )
        return x, y

    x_tr, y_tr = panel(switch_train)
    x_ca, y_ca = panel(switch_cal)
    x_te, y_te = panel(switch_test)
    selector = FixedSplitMethodScoreSelector(["a", "b", "c"], alpha=1.0)
    selector.fit_development(x_tr, y_tr)
    policy = selector.calibrate(
        x_ca,
        y_ca,
        thresholds=(0.0, 0.05),
        minimum_coverage=0.2,
        n_boot=200,
        seed=1,
    )
    assert policy.calibration_passed
    actions = selector.predict_actions(x_te)
    scored = evaluate_actions(actions, y_te, policy.methods, global_method=policy.global_method)
    assert scored["coverage"] > 0
    assert scored["mean_regret_difference"] < 0
