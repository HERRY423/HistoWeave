"""Tests for outcome-unseal and patient-level CRC scoring safeguards."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "prospective_validation_v4" / "score_crc_v4.py"
SPEC = importlib.util.spec_from_file_location("score_crc_v4", MODULE_PATH)
assert SPEC and SPEC.loader
SCORER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCORER)


def test_truth_table_requires_unique_registered_sample_spots(tmp_path: Path) -> None:
    truth_path = tmp_path / "truth.csv"
    pd.DataFrame(
        {
            "sample_id": ["s1", "s1"],
            "spot_id": ["a", "a"],
            "truth_label": ["tumour", "stroma"],
        }
    ).to_csv(truth_path, index=False)
    with pytest.raises(ValueError, match="duplicate sample/spot"):
        SCORER.load_truth(truth_path, {"s1"})


def test_scoring_rejects_freeze_changed_after_authorization(tmp_path: Path) -> None:
    results = tmp_path / "results"
    results.mkdir()
    prediction_path = results / "prediction_freeze.json"
    actions_path = results / "policy_actions.json"
    prediction_path.write_text('{"status":"complete"}\n', encoding="utf-8")
    actions_path.write_text('{"status":"evidence_required"}\n', encoding="utf-8")
    authorization_path = results / "truth_unseal_authorization.json"
    authorization_path.write_text(
        json.dumps(
            {
                "schema_version": "histoweave.crc.truth_unseal_authorization.v4",
                "truth_unseal_authorized": True,
                "prediction_freeze_sha256": SCORER.sha256(prediction_path),
                "policy_actions_sha256": SCORER.sha256(actions_path),
            }
        ),
        encoding="utf-8",
    )
    SCORER.verify_authorization(results, authorization_path)
    actions_path.write_text('{"status":"changed"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="policy actions changed"):
        SCORER.verify_authorization(results, authorization_path)
