"""Prepare label-free DLPFC inputs for sequential confirmation (truth sealed)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import anndata as ad
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DONORS = {
    "Br5595": ["151507", "151508", "151509", "151510"],
    "Br8100": ["151669", "151670", "151671", "151672"],
    "Br5292": ["151673", "151674", "151675", "151676"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_source(section: str) -> Path:
    candidates = [
        ROOT / "datasets_cache" / "dlpfc" / f"dlpfc_{section}.h5ad",
        ROOT / "datasets_cache" / f"dlpfc_{section}" / f"dlpfc_{section}.h5ad",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"DLPFC section {section} not found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "datasets_cache" / "dlpfc_v5_prepared",
    )
    parser.add_argument(
        "--truth-output",
        type=Path,
        default=ROOT / "datasets_cache" / "dlpfc_v5_private_truth",
    )
    args = parser.parse_args()
    inputs = args.output / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    args.truth_output.mkdir(parents=True, exist_ok=True)

    records = []
    for donor, sections in DONORS.items():
        for section in sections:
            source = find_source(section)
            adata = ad.read_h5ad(source)
            sample_id = f"{donor}_{section}"
            # Seal truth separately.
            label_col = None
            for col in ("domain_truth", "spatialLIBD_layer", "layer"):
                if col in adata.obs.columns:
                    label_col = col
                    break
            if label_col is None:
                raise RuntimeError(f"{source}: no domain labels")
            truth = adata.obs[[label_col]].copy()
            truth.columns = ["domain_truth"]
            truth_path = args.truth_output / f"{sample_id}.csv"
            truth.to_csv(truth_path)
            # Label-free prediction input.
            keep_obs = [c for c in ("array_row", "array_col") if c in adata.obs.columns]
            clean = ad.AnnData(
                X=adata.layers["counts"] if "counts" in adata.layers else adata.X,
                obs=adata.obs[keep_obs].copy() if keep_obs else adata.obs.iloc[:, 0:0].copy(),
                var=adata.var.copy(),
                obsm={"spatial": np.asarray(adata.obsm["spatial"], dtype=np.float32)},
            )
            clean.obs["sample_id"] = sample_id
            clean.obs["donor_id"] = donor
            clean.obs["section_id"] = section
            clean.layers["counts"] = clean.X.copy()
            clean.uns["protocol_id"] = "histoweave-dlpfc-sequential-confirmation-2026-08"
            clean.uns["truth_sealed"] = True
            out_path = inputs / f"{sample_id}.h5ad"
            clean.write_h5ad(out_path)
            records.append(
                {
                    "sample_id": sample_id,
                    "donor_id": donor,
                    "section_id": section,
                    "source_path": str(source),
                    "source_sha256": sha256(source),
                    "input_path": str(out_path),
                    "input_sha256": sha256(out_path),
                    "truth_path": str(truth_path),
                    "truth_sha256": sha256(truth_path),
                    "n_obs": int(clean.n_obs),
                    "n_vars": int(clean.n_vars),
                }
            )
            print(f"prepared {sample_id}: n_obs={clean.n_obs}")

    manifest = {
        "schema_version": "histoweave.dlpfc_v5_prepared.v1",
        "protocol_id": "histoweave-dlpfc-sequential-confirmation-2026-08",
        "n_samples": len(records),
        "n_donors": len(DONORS),
        "records": records,
    }
    (args.output / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.output / 'source_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
