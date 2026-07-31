"""Integrity checks for the P0 submission freeze v2."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "submission_freeze_v2"


def test_p0_freeze_v2_is_self_consistent() -> None:
    result = subprocess.run(
        [sys.executable, str(FREEZE / "reproduce_submission_freeze.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    manifest = json.loads((FREEZE / "submission_freeze_manifest.json").read_text())
    assert manifest["status"] == "p0_local_complete_public_preregistration_pending"
    assert manifest["validation"]["prospective_execution_permitted"] is False
