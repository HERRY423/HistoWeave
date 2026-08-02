"""Extract label-free recommendation features for meta-panel units."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from histoweave.benchmark.features import (  # noqa: E402
    RECOMMENDATION_FEATURE_ORDER,
    extract_features,
)
from histoweave.data import SpatialTable  # noqa: E402

HER2ST_INPUTS = Path(r"C:\Spatial Transcriptomics\histoweave-her2st-data\prepared\inputs")
CRC_INPUTS = ROOT / "datasets_cache" / "crc_v4_prepared" / "inputs"
OUT = Path(__file__).resolve().parent / "results"


def _table_from_h5ad(path: Path) -> SpatialTable:
    adata = ad.read_h5ad(path)
    if hasattr(SpatialTable, "from_anndata"):
        table = SpatialTable.from_anndata(adata)
        # Prefer raw counts when present for library-size features.
        if "counts" in adata.layers:
            table = SpatialTable(
                X=adata.layers["counts"],
                obs=adata.obs.copy(),
                var=adata.var.copy(),
                obsm={"spatial": np.asarray(adata.obsm["spatial"], dtype=float)},
                layers={"counts": adata.layers["counts"]},
            )
        return table
    coords = np.asarray(adata.obsm["spatial"], dtype=float)
    x = adata.layers["counts"] if "counts" in adata.layers else adata.X
    return SpatialTable(
        X=x,
        obs=adata.obs.copy(),
        var=adata.var.copy(),
        obsm={"spatial": coords},
    )


def _mean_features(paths: list[Path]) -> dict[str, float]:
    vectors = []
    for path in paths:
        feats = extract_features(_table_from_h5ad(path), include_domain=False)
        vectors.append([float(feats.get(k, np.nan)) for k in RECOMMENDATION_FEATURE_ORDER])
    arr = np.asarray(vectors, dtype=float)
    means = np.nanmean(arr, axis=0)
    return {
        name: (float(val) if np.isfinite(val) else 0.0)
        for name, val in zip(RECOMMENDATION_FEATURE_ORDER, means, strict=True)
    }


def her2st_paths(unit_id: str) -> list[Path]:
    # Donor A -> A1.h5ad (registration used one section per donor).
    path = HER2ST_INPUTS / f"{unit_id}1.h5ad"
    if not path.exists():
        raise FileNotFoundError(path)
    return [path]


def crc_paths(unit_id: str) -> list[Path]:
    matches = sorted(CRC_INPUTS.glob(f"*_{unit_id}_*.h5ad"))
    if not matches:
        matches = sorted(CRC_INPUTS.glob(f"*{unit_id}*.h5ad"))
    if not matches:
        raise FileNotFoundError(f"No CRC inputs for patient {unit_id} under {CRC_INPUTS}")
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--units",
        type=Path,
        default=OUT / "meta_panel_units.json",
    )
    parser.add_argument("--output", type=Path, default=OUT / "unit_features.json")
    args = parser.parse_args()

    units = json.loads(args.units.read_text(encoding="utf-8"))["units"]
    rows = []
    for unit in units:
        study = unit["study_id"]
        unit_id = str(unit["unit_id"])
        if study == "HER2ST":
            paths = her2st_paths(unit_id)
        elif study == "CRC_V4":
            paths = crc_paths(unit_id)
        else:
            raise ValueError(f"unknown study {study}")
        feats = _mean_features(paths)
        rows.append(
            {
                "study_id": study,
                "unit_id": unit_id,
                "n_sections": len(paths),
                "features": feats,
                "feature_order": list(RECOMMENDATION_FEATURE_ORDER),
                "source_paths": [str(p) for p in paths],
            }
        )
        print(f"features {study}/{unit_id}: n_sections={len(paths)}")

    payload = {
        "schema_version": "histoweave.unit_features.v5",
        "feature_order": list(RECOMMENDATION_FEATURE_ORDER),
        "units": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    flat = []
    for row in rows:
        flat.append(
            {
                "study_id": row["study_id"],
                "unit_id": row["unit_id"],
                **row["features"],
            }
        )
    pd.DataFrame(flat).to_csv(args.output.with_suffix(".csv"), index=False)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
