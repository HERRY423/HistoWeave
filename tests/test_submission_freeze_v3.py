"""Integrity checks for the Bioinformatics P1 submission freeze v3."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "submission_freeze_v3"


def test_p1_submission_freeze_v3_is_self_consistent() -> None:
    result = subprocess.run(
        [sys.executable, str(FREEZE / "reproduce_submission_freeze.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    manifest = json.loads(
        (FREEZE / "submission_freeze_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["schema_version"] == "histoweave.submission_freeze.v3"
    assert manifest["status"] == "p1_editorial_draft_complete_submission_blocked"
    assert manifest["validation"]["static_audit_passed"] is True
    assert manifest["validation"]["evidence_assertions"]["audit_all_cases_passed"] is True
    assert manifest["validation"]["author_required_placeholders"] > 0
    assert manifest["submission_blockers"]


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
