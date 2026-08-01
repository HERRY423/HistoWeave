"""Record outcome-sealed runtime skips as explicit failed prediction cells."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def write_runtime_skip(
    prepared: Path, results: Path, sample_id: str, method: str, seed: int
) -> Path:
    if (results / "truth_unseal_authorization.json").exists():
        raise RuntimeError("runtime skips cannot be recorded after truth-unseal authorization")
    source = json.loads((prepared / "source_manifest.json").read_text(encoding="utf-8"))
    input_hashes = {
        str(row["sample_id"]): str(row["input_sha256"]) for row in source["records"]
    }
    k_estimates = json.loads((results / "k_estimates.json").read_text(encoding="utf-8"))
    if sample_id not in input_hashes or sample_id not in k_estimates:
        raise ValueError(f"unknown prepared sample: {sample_id}")
    status_path = results / "predictions" / f"{sample_id}__{method}__seed{seed}.json"
    if status_path.exists():
        raise FileExistsError(f"prediction status already exists: {status_path}")
    payload = {
        "sample_id": sample_id,
        "method": method,
        "seed": seed,
        "estimated_k": int(k_estimates[sample_id]["k"]),
        "input_sha256": input_hashes[sample_id],
        "status": "failed",
        "failure_class": "user_authorized_runtime_skip",
        "error": (
            "RuntimeSkip: outcome-sealed execution was stopped after repeated "
            "infrastructure timeouts; no prediction was produced or imputed"
        ),
        "seconds": None,
        "output_path": None,
        "output_sha256": None,
        "finished_utc": datetime.now(UTC).isoformat(),
        "truth_accessed": False,
        "user_authorized": True,
    }
    status_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return status_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--cell", action="append", required=True, help="sample_id:seed")
    args = parser.parse_args()
    for value in args.cell:
        sample_id, seed = value.rsplit(":", 1)
        print(write_runtime_skip(args.prepared, args.results, sample_id, args.method, int(seed)))


if __name__ == "__main__":
    main()
