"""Same-mask and independent-unit tests for multi-study SOTA summaries."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "multistudy_validation" / "analyze_same_mask.py"


def _module():
    spec = importlib.util.spec_from_file_location("same_mask", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_both_studies_use_one_within_study_nine_method_mask() -> None:
    payload = _module().analyze(SCRIPT.with_name("study_registry.json"), ROOT)
    assert payload["n_registered_studies"] == 2
    assert payload["n_completed_studies"] == 2
    assert payload["multistudy_complete"] is True
    her2 = payload["studies"][0]
    assert her2["study_id"] == "HER2ST"
    assert her2["n_all_units"] == 7
    assert her2["n_strict_nine_method_units"] == 6
    assert her2["excluded_from_strict_mask"] == ["C"]
    assert {row["n_strict_same_mask"] for row in her2["method_summary"]} == {6}
    crc = payload["studies"][1]
    assert crc["study_id"] == "CRC_V4"
    assert crc["n_all_units"] == 7
    assert crc["n_strict_nine_method_units"] == 7
    assert crc["excluded_from_strict_mask"] == []
    assert {row["n_strict_same_mask"] for row in crc["method_summary"]} == {7}
    assert payload["pending"] == []
    assert payload["cross_study_inference"] == "study-stratified_only_no_pooled_unit_bootstrap"


def test_registry_never_calls_sections_independent_units() -> None:
    registry = json.loads(SCRIPT.with_name("study_registry.json").read_text(encoding="utf-8"))
    assert {study["unit"] for study in registry["studies"]} == {"donor", "patient"}
    assert "section" not in registry["analysis_unit_rule"].split("; never ")[-1].split(", ")[:1]
