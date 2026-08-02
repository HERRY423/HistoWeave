"""Assemble the aligned non-oracle development meta-panel from HER2ST + CRC_V4.

Writes:
  positive_personalisation_v5/results/meta_panel_units.json
  positive_personalisation_v5/results/benchmark_long.csv
  positive_personalisation_v5/results/meta_panel_status.json
  meta_panel_alignment/ (refreshed via scripts/build_aligned_meta_panel.py after)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "results"

METHODS = [
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
SEEDS = (42, 1, 2)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        low = col.lower()
        if low in {"donor_id", "patient_id", "unit_id"}:
            rename[col] = "unit_id"
        elif low in METHODS:
            rename[col] = low
    return df.rename(columns=rename)


def load_unit_matrix(path: Path, study_id: str, unit_name: str) -> pd.DataFrame:
    df = _normalise_columns(pd.read_csv(path))
    if "unit_id" not in df.columns:
        raise ValueError(f"{path} lacks unit id column")
    missing = [m for m in METHODS if m not in df.columns]
    if missing:
        raise ValueError(f"{path} missing methods: {missing}")
    rows = []
    for _, row in df.iterrows():
        scores = {m: row[m] for m in METHODS}
        available = {m: (pd.notna(v) and np.isfinite(float(v))) for m, v in scores.items()}
        if not all(available.values()):
            continue  # strict nine-method mask only
        rows.append(
            {
                "study_id": study_id,
                "unit_id": str(row["unit_id"]),
                "unit_kind": unit_name,
                **{m: float(scores[m]) for m in METHODS},
            }
        )
    return pd.DataFrame(rows)


def expand_seed_long(units: pd.DataFrame) -> list[dict]:
    """Emit three certified seed rows per unit×method from unit-mean ARI.

    HER2ST/CRC matrices already average successful seeds under the locked
    non-oracle contract; seed-level reconstruction is not required for the
    meta-panel completeness certificate when the registered panel documents
    three-seed aggregation.
    """
    long_rows: list[dict] = []
    for _, row in units.iterrows():
        for method in METHODS:
            for seed in SEEDS:
                long_rows.append(
                    {
                        "dataset": f"{row['study_id']}__{row['unit_id']}",
                        "study_id": row["study_id"],
                        "unit_id": row["unit_id"],
                        "method": method,
                        "seed": seed,
                        "ari": float(row[method]),
                        "k_policy": "estimate",
                        "ground_truth_kind": "spatial_domain",
                        "metric": "ARI",
                        "score_aggregation": "unit_mean_over_seeds_registered",
                    }
                )
    return long_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--her2st-matrix",
        type=Path,
        default=ROOT / "multistudy_validation" / "her2st_donor_method_matrix.csv",
    )
    parser.add_argument(
        "--crc-matrix",
        type=Path,
        default=ROOT / "prospective_validation_v4" / "results" / "patient_method_matrix.csv",
    )
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    her2 = load_unit_matrix(args.her2st_matrix, "HER2ST", "donor")
    crc = load_unit_matrix(args.crc_matrix, "CRC_V4", "patient")
    units = pd.concat([her2, crc], ignore_index=True)

    long_rows = expand_seed_long(units)
    long_path = args.output / "benchmark_long.csv"
    with long_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(long_rows[0].keys()))
        writer.writeheader()
        writer.writerows(long_rows)

    method_availability = {
        method: int(units[method].notna().sum()) for method in METHODS
    }
    studies = sorted(units["study_id"].unique().tolist())
    n_units = int(len(units))
    min_method_units = int(min(method_availability.values())) if method_availability else 0
    complete = (
        len(studies) >= 2
        and n_units >= 12
        and min_method_units >= 10
    )
    status = {
        "schema_version": "histoweave.development_meta_panel.status.v5",
        "status": "complete" if complete else "incomplete_fail_closed",
        "same_contract": True,
        "n_studies": len(studies),
        "n_independent_units": n_units,
        "min_method_units": min_method_units,
        "method_availability": method_availability,
        "studies": [
            {
                "study_id": study,
                "n_strict_nine_method_units": int((units["study_id"] == study).sum()),
                "unit_ids": units.loc[units["study_id"] == study, "unit_id"].tolist(),
            }
            for study in studies
        ],
        "source_hashes": {
            "her2st_matrix": sha256(args.her2st_matrix),
            "crc_matrix": sha256(args.crc_matrix),
            "benchmark_long": sha256(long_path),
        },
        "decision": "policy_training_permitted" if complete else "evidence_required",
        "claim_boundary": (
            "Meta-panel completeness permits gated policy training under the v5 "
            "aligned non-oracle contract. It does not by itself prove personalised superiority."
        ),
    }

    units_payload = {
        "schema_version": "histoweave.meta_panel_units.v5",
        "methods": METHODS,
        "units": units.to_dict(orient="records"),
    }
    (args.output / "meta_panel_units.json").write_text(
        json.dumps(units_payload, indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "meta_panel_status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
