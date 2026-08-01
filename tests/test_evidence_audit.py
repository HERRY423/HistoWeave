"""Paper-level regression tests for the P0 evidence-admission audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from histoweave.benchmark.decision import load_decision_evidence
from histoweave.benchmark.evidence_audit import run_evidence_admission_audit


def test_adversarial_evidence_audit_meets_predeclared_endpoints(tmp_path: Path) -> None:
    summary = run_evidence_admission_audit(tmp_path)
    assert summary["invalid_cases"] >= 8
    assert summary["incompatible_evidence_admission_rate"] == 0.0
    assert summary["valid_evidence_false_rejection_rate"] == 0.0
    assert summary["dominated_selection_rate"] == 0.0
    assert summary["all_cases_passed"] is True

    rows = json.loads((tmp_path / "adversarial_corpus_results.json").read_text())["cases"]
    oracle = next(row for row in rows if row["case_id"] == "oracle_k_reference")
    assert oracle["observed_action"] == "abstain"
    unverified = next(row for row in rows if row["case_id"] == "unverified_validation_json")
    assert unverified["observed_action"] == "evidence_required"
    dominated = next(row for row in rows if row["case_id"] == "valid_dominated_candidate")
    assert dominated["primary_set"] == ["global"]


def test_audit_manifest_hashes_every_artifact(tmp_path: Path) -> None:
    run_evidence_admission_audit(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for name, record in manifest["artifacts"].items():
        path = tmp_path / name
        assert path.stat().st_size == record["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]


def test_validation_loader_rejects_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text("{}\n", encoding="utf-8")
    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "source_artifacts": [
                    {"path": "source.json", "sha256": "0" * 64},
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        load_decision_evidence(evidence)
