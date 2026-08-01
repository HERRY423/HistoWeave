"""Create the one-time CRC truth-unseal authorization from both required freezes."""

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


def build_authorization(prediction_path: Path, actions_path: Path) -> dict[str, Any]:
    prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
    actions = json.loads(actions_path.read_text(encoding="utf-8"))
    if prediction.get("schema_version") != "histoweave.crc.prediction_freeze.v4":
        raise ValueError("completed v4 prediction freeze is required")
    if prediction.get("prediction_component_complete") is not True:
        raise ValueError("prediction component is not complete")
    if prediction.get("truth_unseal_requires_joint_authorization") is not True:
        raise ValueError("prediction freeze lacks the joint-authorization safeguard")
    if int(prediction.get("expected_cells", -1)) != 378:
        raise ValueError("prediction freeze does not cover all 378 registered attempts")
    if actions.get("schema_version") != "histoweave.crc.policy_actions.v4":
        raise ValueError("completed v4 policy-action freeze is required")
    if actions.get("status") not in {"evidence_required", "policy_actions_frozen"}:
        raise ValueError("policy action status is not frozen")
    if len(actions.get("actions", [])) != 7:
        raise ValueError("policy action freeze does not cover all seven patients")
    if prediction.get("protocol_id") != actions.get("protocol_id"):
        raise ValueError("freeze protocol identifiers disagree")
    if prediction.get("source_manifest_sha256") != actions.get("source_manifest_sha256"):
        raise ValueError("freeze source manifests disagree")
    if prediction.get("truth_accessed") is not False or actions.get("truth_accessed") is not False:
        raise ValueError("freeze artefact indicates prior truth access")
    return {
        "schema_version": "histoweave.crc.truth_unseal_authorization.v4",
        "protocol_id": prediction["protocol_id"],
        "authorized_utc": datetime.now(UTC).isoformat(),
        "prediction_freeze_sha256": sha256(prediction_path),
        "policy_actions_sha256": sha256(actions_path),
        "source_manifest_sha256": prediction["source_manifest_sha256"],
        "policy_status": actions["status"],
        "truth_unseal_authorized": True,
        "claim_boundary": (
            "Authorization protects outcome sealing; it is not evidence of policy efficacy."
        ),
    }


def write_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction-freeze", type=Path, required=True)
    parser.add_argument("--policy-actions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_once(args.output, build_authorization(args.prediction_freeze, args.policy_actions))


if __name__ == "__main__":
    main()
