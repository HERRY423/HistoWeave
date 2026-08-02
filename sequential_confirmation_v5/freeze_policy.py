"""Freeze the sequential-confirmation policy from v5 LOUO artefacts (no DLPFC outcomes)."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "results"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--louo",
        type=Path,
        default=ROOT / "positive_personalisation_v5" / "results" / "nested_louo_results.json",
    )
    parser.add_argument(
        "--meta",
        type=Path,
        default=ROOT / "positive_personalisation_v5" / "results" / "meta_panel_units.json",
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=ROOT / "positive_personalisation_v5" / "results" / "unit_features.json",
    )
    parser.add_argument("--output", type=Path, default=OUT / "frozen_policy.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    louo = json.loads(args.louo.read_text(encoding="utf-8"))
    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    feats = json.loads(args.features.read_text(encoding="utf-8"))
    if not louo.get("personalized_value_success"):
        raise SystemExit("refuse freeze: primary LOUO endpoint did not succeed")

    thresholds = sorted(
        {
            float(a["threshold"])
            for a in louo["actions"]
            if a.get("threshold") is not None
        }
    )
    globals_ = [
        a["training_global_method"]
        for a in louo["actions"]
        if a.get("training_global_method")
    ]
    global_method = max(set(globals_), key=globals_.count)
    feature_subset = list(louo.get("feature_subset") or [])

    payload = {
        "schema_version": "histoweave.sequential_confirmation.frozen_policy.v5",
        "protocol_id": "histoweave-dlpfc-sequential-confirmation-2026-08",
        "frozen_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "model": "1nn",
        "k": 1,
        "global_method": global_method,
        "deployment_threshold": 0.08,
        "threshold_set_observed_on_source": thresholds,
        "feature_subset": feature_subset,
        "neighbor_bank_studies": ["HER2ST", "CRC_V4"],
        "neighbor_bank_units": [
            f"{u['study_id']}:{u['unit_id']}" for u in meta["units"]
        ],
        "source_hashes": {
            "louo": sha256(args.louo),
            "meta_panel_units": sha256(args.meta),
            "unit_features": sha256(args.features),
        },
        "source_evaluation": louo.get("evaluation"),
        "rule": (
            "Using only HER2ST+CRC neighbour bank features/performance, select the "
            "1-NN unit's best method if predicted gain over the frozen global method "
            "is >= deployment_threshold; otherwise return global_default."
        ),
        "claim_boundary": (
            "Policy freeze uses no DLPFC outcomes. DLPFC is sequential confirmation only."
        ),
    }
    # Embed neighbour bank feature/performance rows for offline application.
    methods = [
        "spagcn",
        "stagate",
        "graphst",
        "bayesspace",
        "banksy",
        "spectral",
        "gaussian_mixture",
        "kmeans",
        "agglomerative",
    ]
    feat_map = {
        f"{row['study_id']}:{row['unit_id']}": row["features"] for row in feats["units"]
    }
    bank = []
    for unit in meta["units"]:
        key = f"{unit['study_id']}:{unit['unit_id']}"
        bank.append(
            {
                "unit_id": key,
                "features": {k: float(feat_map[key][k]) for k in feature_subset},
                "performance": {m: float(unit[m]) for m in methods},
            }
        )
    payload["neighbor_bank"] = bank
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    payload["policy_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "global_method": global_method,
                "deployment_threshold": 0.08,
                "n_neighbor_units": len(bank),
                "policy_sha256": payload["policy_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
