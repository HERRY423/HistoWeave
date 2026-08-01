"""Audit and freeze every CRC prediction attempt before truth access."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

METHODS = (
    "spagcn",
    "stagate",
    "graphst",
    "bayesspace",
    "banksy",
    "spectral",
    "gaussian_mixture",
    "kmeans",
    "agglomerative",
)
SEEDS = (42, 1, 2)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any, *, exclusive: bool = False) -> None:
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def audit(prepared: Path, results: Path) -> dict[str, Any]:
    source_path = prepared / "source_manifest.json"
    k_path = results / "k_estimates.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    k_estimates = json.loads(k_path.read_text(encoding="utf-8"))
    samples = [str(row["sample_id"]) for row in source["records"]]
    input_hash = {str(row["sample_id"]): str(row["input_sha256"]) for row in source["records"]}
    expected = [
        (sample, method, seed)
        for sample in samples
        for method in METHODS
        for seed in SEEDS
    ]
    missing: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    for sample, method, seed in expected:
        status_path = results / "predictions" / f"{sample}__{method}__seed{seed}.json"
        if not status_path.is_file():
            missing.append({"sample_id": sample, "method": method, "seed": seed})
            continue
        row = json.loads(status_path.read_text(encoding="utf-8"))
        reasons = []
        if row.get("input_sha256") != input_hash[sample]:
            reasons.append("input_hash_mismatch")
        if int(row.get("estimated_k", -1)) != int(k_estimates[sample]["k"]):
            reasons.append("shared_k_mismatch")
        if row.get("status") == "success":
            output_value = row.get("output_path")
            output_path = Path(str(output_value)) if output_value else None
            if output_path is None or not output_path.is_file():
                reasons.append("success_output_missing")
            elif sha256(output_path) != row.get("output_sha256"):
                reasons.append("success_output_hash_mismatch")
        elif row.get("status") == "failed":
            if row.get("output_path") is not None or not row.get("error"):
                reasons.append("malformed_failure_record")
        else:
            reasons.append("unknown_status")
        if reasons:
            invalid.append(
                {"sample_id": sample, "method": method, "seed": seed, "reasons": reasons}
            )
        cells.append(row)
    complete = not missing and not invalid and len(cells) == len(expected)
    return {
        "schema_version": "histoweave.crc.prediction_freeze_audit.v4",
        "protocol_id": "histoweave-crc-patient-nonoracle-2026-07",
        "audited_utc": datetime.now(UTC).isoformat(),
        "source_manifest_sha256": sha256(source_path),
        "k_estimates_sha256": sha256(k_path),
        "expected_cells": len(expected),
        "observed_cells": len(cells),
        "success_cells": sum(row.get("status") == "success" for row in cells),
        "failed_cells": sum(row.get("status") == "failed" for row in cells),
        "missing_cells": missing,
        "invalid_cells": invalid,
        "all_samples_share_one_k_across_methods_and_seeds": not any(
            "shared_k_mismatch" in row["reasons"] for row in invalid
        ),
        "prediction_attempts_complete": complete,
        "prediction_component_complete": complete,
        "truth_accessed": False,
        "truth_unseal_permitted": False,
        "truth_unseal_requires_joint_authorization": True,
        "cells": cells if complete else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    payload = audit(args.prepared, args.results)
    audit_path = args.results / "prediction_freeze_audit.json"
    write_json(audit_path, payload)
    if payload["prediction_attempts_complete"]:
        freeze = {
            "schema_version": "histoweave.crc.prediction_freeze.v4",
            "protocol_id": payload["protocol_id"],
            "frozen_utc": datetime.now(UTC).isoformat(),
            "audit_sha256": sha256(audit_path),
            "source_manifest_sha256": payload["source_manifest_sha256"],
            "k_estimates_sha256": payload["k_estimates_sha256"],
            "expected_cells": payload["expected_cells"],
            "success_cells": payload["success_cells"],
            "failed_cells": payload["failed_cells"],
            "prediction_component_complete": True,
            "truth_accessed": False,
            "truth_unseal_permitted": False,
            "truth_unseal_requires_joint_authorization": True,
        }
        write_json(args.results / "prediction_freeze.json", freeze, exclusive=True)
    else:
        raise SystemExit(
            f"prediction freeze incomplete: {len(payload['missing_cells'])} missing, "
            f"{len(payload['invalid_cells'])} invalid"
        )


if __name__ == "__main__":
    main()
