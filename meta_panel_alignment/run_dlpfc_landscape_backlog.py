"""Optional: expand the broad 135-cell landscape with DLPFC estimate-K cells.

The v5 sequential confirmation panel (three donors × nine methods × three seeds)
is the preferred path for DLPFC non-oracle completeness. This helper only
documents how to feed those cells into the historical landscape scanner after
`sequential_confirmation_v5` finishes scoring.

It does not re-run methods.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scores",
        type=Path,
        default=ROOT
        / "sequential_confirmation_v5"
        / "results"
        / "section_seed_scores.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "meta_panel_alignment" / "dlpfc_v5_landscape_long.csv",
    )
    args = parser.parse_args()
    if not args.scores.is_file():
        print(f"missing scores (run sequential panel first): {args.scores}")
        return 2
    rows = list(csv.DictReader(args.scores.open(encoding="utf-8")))
    out_rows = []
    for row in rows:
        if row.get("ari") in {"", None} or row.get("seed") in {"", None}:
            continue
        section = row["section_id"]
        out_rows.append(
            {
                "dataset": section,
                "method": row["method"],
                "seed": row["seed"],
                "ari": row["ari"],
                "k_policy": "estimate",
                "ground_truth_kind": "spatial_domain",
                "metric": "ARI",
                "source": "sequential_confirmation_v5",
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(json.dumps({"n_rows": len(out_rows), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
