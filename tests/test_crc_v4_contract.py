"""Static safety checks for the CRC outcome-sealed runner."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRC = ROOT / "prospective_validation_v4"


def test_public_receipt_precedes_execution() -> None:
    receipt = json.loads((CRC / "registration_receipt.json").read_text(encoding="utf-8"))
    assert receipt["unlock_status"] == "satisfied"
    assert receipt["public_issue"].endswith("/20")
    assert receipt["outcome_access_status_at_receipt"] == "not_started"


def test_preparer_has_14_sections_and_never_reads_pathology() -> None:
    source = (CRC / "prepare_crc_v4.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignment = next(
        node for node in tree.body if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SAMPLES" for target in node.targets
        )
    )
    assert isinstance(assignment.value, ast.Dict)
    assert len(assignment.value.keys) == 14
    lowered = source.lower()
    assert "pathology_spotannotations" not in lowered
    assert "truth_sealed" in source
    assert '"k_policy": "estimate"' in source
