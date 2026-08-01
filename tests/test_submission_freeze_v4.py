"""Integrity checks for the current Bioinformatics submission freeze v4."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "submission_freeze_v4"


def test_submission_freeze_v4_is_self_consistent() -> None:
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
    assert manifest["schema_version"] == "histoweave.submission_freeze.v4"
    assert manifest["validation"]["static_audit_passed"] is True
    assert manifest["multistudy_nonoracle_validation"]["completed_studies"] == 2
    assert manifest["multistudy_nonoracle_validation"]["strict_units"] == 13
    assert manifest["multistudy_nonoracle_validation"]["crc_policy_status"] == (
        "evidence_required"
    )
    assert manifest["synthetic_construct_validity"]["success"] is True
