"""Tests for prediction and policy freeze contracts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRC = ROOT / "prospective_validation_v4"


def _module(name: str):
    path = CRC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_incomplete_prediction_panel_cannot_unseal_truth(tmp_path: Path) -> None:
    prepared = tmp_path / "prepared"
    results = tmp_path / "results"
    prepared.mkdir()
    results.mkdir()
    (prepared / "source_manifest.json").write_text(
        json.dumps({"records": [{"sample_id": "s", "input_sha256": "x"}]}),
        encoding="utf-8",
    )
    (results / "k_estimates.json").write_text(
        json.dumps({"s": {"k": 3}}), encoding="utf-8"
    )
    payload = _module("freeze_predictions").audit(prepared, results)
    assert payload["prediction_attempts_complete"] is False
    assert payload["truth_unseal_permitted"] is False
    assert len(payload["missing_cells"]) == 27


def test_current_development_status_fails_closed() -> None:
    status = json.loads(
        (CRC / "development_meta_panel_status.json").read_text(encoding="utf-8")
    )
    assert status["same_contract"] is False
    assert status["policy_frozen"] is False
    assert status["decision"] == "evidence_required"


def test_policy_freeze_is_write_once(tmp_path: Path) -> None:
    module = _module("freeze_policy_actions")
    path = tmp_path / "actions.json"
    module.write_once(path, {"status": "evidence_required"})
    try:
        module.write_once(path, {"status": "changed_after_truth"})
    except FileExistsError:
        pass
    else:
        raise AssertionError("a frozen action file was overwritten")
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "status": "evidence_required"
    }


def test_completed_prediction_freeze_is_write_once(tmp_path: Path) -> None:
    module = _module("freeze_predictions")
    path = tmp_path / "prediction_freeze.json"
    module.write_json(path, {"status": "complete"}, exclusive=True)
    try:
        module.write_json(path, {"status": "changed"}, exclusive=True)
    except FileExistsError:
        pass
    else:
        raise AssertionError("a completed prediction freeze was overwritten")
    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "complete"}


def test_truth_unseal_requires_both_matching_freezes(tmp_path: Path) -> None:
    module = _module("authorize_truth_unseal")
    prediction_path = tmp_path / "prediction.json"
    actions_path = tmp_path / "actions.json"
    prediction_path.write_text(
        json.dumps(
            {
                "schema_version": "histoweave.crc.prediction_freeze.v4",
                "protocol_id": "p",
                "prediction_component_complete": True,
                "truth_unseal_requires_joint_authorization": True,
                "expected_cells": 378,
                "source_manifest_sha256": "source",
                "truth_accessed": False,
            }
        ),
        encoding="utf-8",
    )
    actions_path.write_text(
        json.dumps(
            {
                "schema_version": "histoweave.crc.policy_actions.v4",
                "protocol_id": "p",
                "status": "evidence_required",
                "actions": [{"patient_id": str(i)} for i in range(7)],
                "source_manifest_sha256": "source",
                "truth_accessed": False,
            }
        ),
        encoding="utf-8",
    )
    payload = module.build_authorization(prediction_path, actions_path)
    assert payload["truth_unseal_authorized"] is True
    assert payload["policy_status"] == "evidence_required"
    altered = json.loads(actions_path.read_text(encoding="utf-8"))
    altered["source_manifest_sha256"] = "different"
    actions_path.write_text(json.dumps(altered), encoding="utf-8")
    try:
        module.build_authorization(prediction_path, actions_path)
    except ValueError as error:
        assert "source manifests disagree" in str(error)
    else:
        raise AssertionError("mismatched freezes authorized truth access")
