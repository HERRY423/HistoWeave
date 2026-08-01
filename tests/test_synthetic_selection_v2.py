"""Regression tests for the repaired fixed-split synthetic predicate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "synthetic_validation_v2" / "run_validation.py"


def _module():
    spec = importlib.util.spec_from_file_location("synthetic_selection_v2", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repaired_predicate_uses_disjoint_fixed_splits(tmp_path: Path) -> None:
    module = _module()
    payload = module.run(SCRIPT.with_name("protocol.json"), tmp_path)
    assert payload["success"] is True
    assert payload["signal_test"]["coverage"] >= 0.25
    assert payload["signal_test"]["bootstrap_95_interval_regret_difference"][1] < 0
    assert payload["null_test"]["bootstrap_95_interval_regret_difference"][1] <= 0.02
    assert payload["v3_failure_retained"] is True


def test_coverage_never_requires_global_method_on_covered_units() -> None:
    protocol = (SCRIPT.with_name("protocol.json")).read_text(encoding="utf-8")
    assert "No success condition may require the global method" not in protocol
    assert "covered_action_accuracy_floor" in protocol
    assert "non_global_opportunity_recall_floor" in protocol
