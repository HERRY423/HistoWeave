"""Freeze patient actions or fail closed before CRC truth is unsealed."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_once(path: Path, payload: dict[str, Any]) -> None:
    """Create a freeze artefact exactly once; never replace an existing lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--development-status", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_path = args.prepared / "source_manifest.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    development = json.loads(args.development_status.read_text(encoding="utf-8"))
    patients = sorted({str(row["patient_id"]) for row in source["records"]})
    gate = bool(
        development.get("same_contract")
        and int(development.get("n_studies", 0)) >= 2
        and int(development.get("n_independent_units", 0)) >= 12
        and int(development.get("min_method_units", 0)) >= 10
        and development.get("policy_frozen")
    )
    if gate:
        actions = development.get("crc_actions") or []
        if sorted(str(row["patient_id"]) for row in actions) != patients:
            raise ValueError("frozen development policy does not cover all CRC patients")
        status = "policy_actions_frozen"
    else:
        actions = [
            {
                "patient_id": patient,
                "action": "evidence_required",
                "selected_method": None,
                "reason": "registered development meta-panel minimum not met",
            }
            for patient in patients
        ]
        status = "evidence_required"
    payload: dict[str, Any] = {
        "schema_version": "histoweave.crc.policy_actions.v4",
        "protocol_id": "histoweave-crc-patient-nonoracle-2026-07",
        "frozen_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "development_gate_passed": gate,
        "development_status_sha256": sha256(args.development_status),
        "source_manifest_sha256": sha256(source_path),
        "truth_accessed": False,
        "actions": actions,
        "claim_boundary": (
            "evidence_required is not a personalised-policy efficacy result"
            if not gate
            else "actions were frozen from development evidence and label-free CRC inputs"
        ),
    }
    write_once(args.output, payload)


if __name__ == "__main__":
    main()
