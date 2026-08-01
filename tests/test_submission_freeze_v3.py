"""Integrity checks for the Bioinformatics P1 submission freeze v3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "submission_freeze_v3"


def test_historical_p1_submission_freeze_v3_manifest_is_intact() -> None:
    manifest = json.loads(
        (FREEZE / "submission_freeze_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["schema_version"] == "histoweave.submission_freeze.v3"
    assert manifest["status"] == "p1_editorial_draft_complete_submission_blocked"
    assert manifest["validation"]["static_audit_passed"] is True
    assert manifest["validation"]["evidence_assertions"]["audit_all_cases_passed"] is True
    assert manifest["validation"]["author_required_placeholders"] > 0
    assert manifest["submission_blockers"]
    for relative, record in manifest["generated_artifacts"].items():
        path = ROOT / relative
        assert path.is_file()
        raw = path.read_bytes()
        canonical = raw.replace(b"\r\n", b"\n")
        assert len(canonical) == record["bytes"]
        assert hashlib.sha256(canonical).hexdigest() == record["sha256"]


def test_p1_freeze_contains_all_intended_submission_artwork() -> None:
    manifest = json.loads(
        (FREEZE / "submission_freeze_manifest.json").read_text(encoding="utf-8")
    )
    sources = manifest["source_artifacts"]
    expected = {
        f"manuscript/figures/{stem}.{extension}"
        for stem in (
            "figure1_workflow",
            "figure2_dlpfc_oracle_k",
            "figure3_external_panel",
            "figure4_validation",
            "graphical_abstract",
        )
        for extension in ("png", "svg", "tif")
    }
    assert expected <= sources.keys()
