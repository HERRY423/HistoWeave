"""Prepare the registered CRC cohort without reading pathology labels.

Only Space Ranger count/coordinate archives are accepted.  The pathology
archive is deliberately neither an input nor mentioned by a glob, so method
runners cannot gain accidental access to outcome labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy import sparse

PROTOCOL_ID = "histoweave-crc-patient-nonoracle-2026-07"
SAMPLES = {
    "SN048_A121573_Rep1": ("A121573", 1, "608a39f21da059024121407967a76b8a"),
    "SN048_A121573_Rep2": ("A121573", 2, "a9f516ca415ad68be283ef0b431c35ce"),
    "SN048_A416371_Rep1": ("A416371", 1, "8aec27998074f672fcdaba6faa609da0"),
    "SN048_A416371_Rep2": ("A416371", 2, "9a49067a4a6d89521601b562011dc02e"),
    "SN123_A551763_Rep1": ("A551763", 1, "b26940f8bf3b3e9855b0a116825e638c"),
    "SN123_A595688_Rep1": ("A595688", 1, "b5aa2ee18977b0be67a72ff2b966ab26"),
    "SN123_A798015_Rep1": ("A798015", 1, "0e589a2c96546fff5ca21cb18d597791"),
    "SN123_A938797_Rep1_X": ("A938797", 1, "08e3c7fe308db62b658cacc6b4be4e1c"),
    "SN124_A551763_Rep2": ("A551763", 2, "adf0ea575a09f473fa4ceb465a6ec66e"),
    "SN124_A595688_Rep2": ("A595688", 2, "808ed49a24eea7d41c575d8c238caa76"),
    "SN124_A798015_Rep2": ("A798015", 2, "db421ccd3e1be463573be562c3266aef"),
    "SN124_A938797_Rep2": ("A938797", 2, "ee145e0f97146586baa8ef95edae05b0"),
    "SN84_A120838_Rep1": ("A120838", 1, "4a185c5e1bf88995ee0c03dbb4e8b63c"),
    "SN84_A120838_Rep2": ("A120838", 2, "d59ffee02162ba7b900199786e536a30"),
}


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as handle:
        for member in handle.infolist():
            target = (destination / member.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"unsafe archive member: {member.filename}")
        handle.extractall(destination)


def read_10x_h5(path: Path) -> tuple[sparse.csr_matrix, list[str], list[str]]:
    """Read a 10x filtered matrix as observations x genes without scanpy."""
    with h5py.File(path, "r") as handle:
        matrix = handle["matrix"]
        shape = tuple(int(v) for v in matrix["shape"][:])
        genes_by_spots = sparse.csc_matrix(
            (
                matrix["data"][:],
                matrix["indices"][:],
                matrix["indptr"][:],
            ),
            shape=shape,
        )
        barcodes = [v.decode("utf-8") for v in matrix["barcodes"][:]]
        features = matrix["features"]
        names = [v.decode("utf-8") for v in features["name"][:]]
        if "feature_type" in features:
            kinds = np.asarray([v.decode("utf-8") for v in features["feature_type"][:]])
            keep = kinds == "Gene Expression"
            genes_by_spots = genes_by_spots[keep]
            names = [name for name, admitted in zip(names, keep, strict=True) if admitted]
    return genes_by_spots.T.tocsr(), barcodes, names


def unique_names(names: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    result = []
    for name in names:
        count = counts.get(name, 0)
        result.append(name if count == 0 else f"{name}-{count}")
        counts[name] = count + 1
    return result


def prepare_sample(sample_id: str, source: Path, output: Path) -> dict[str, Any]:
    patient_id, replicate, expected_md5 = SAMPLES[sample_id]
    archive = source / f"{sample_id}.zip"
    if not archive.is_file():
        raise FileNotFoundError(archive)
    observed_md5 = digest(archive, "md5")
    if observed_md5 != expected_md5:
        raise ValueError(f"{sample_id}: MD5 {observed_md5} != locked {expected_md5}")

    extracted = source / "extracted"
    sample_root = extracted / sample_id
    if not sample_root.is_dir():
        safe_extract(archive, extracted)
    matrix_path = sample_root / "filtered_feature_bc_matrix.h5"
    positions_path = sample_root / "spatial" / "tissue_positions_list.csv"
    if not matrix_path.is_file() or not positions_path.is_file():
        raise FileNotFoundError(f"{sample_id}: incomplete Space Ranger archive")

    matrix, barcodes, genes = read_10x_h5(matrix_path)
    positions = pd.read_csv(
        positions_path,
        header=None,
        names=[
            "spot_id",
            "in_tissue",
            "array_row",
            "array_col",
            "pixel_row",
            "pixel_col",
        ],
    )
    if positions["spot_id"].duplicated().any():
        raise ValueError(f"{sample_id}: duplicate spatial barcodes")
    positions = positions.set_index("spot_id").reindex(barcodes)
    if positions[["in_tissue", "array_row", "array_col"]].isna().any().any():
        raise ValueError(f"{sample_id}: filtered barcodes missing from spatial table")
    keep_spot = positions["in_tissue"].to_numpy(dtype=int) == 1
    matrix = matrix[keep_spot]
    positions = positions.iloc[np.flatnonzero(keep_spot)].copy()
    keep_nonzero = np.asarray(matrix.sum(axis=1)).ravel() > 0
    matrix = matrix[keep_nonzero]
    positions = positions.iloc[np.flatnonzero(keep_nonzero)].copy()
    keep_gene = np.asarray((matrix > 0).sum(axis=0)).ravel() >= 3
    matrix = matrix[:, keep_gene].tocsr().astype(np.float32)
    genes = [gene for gene, admitted in zip(genes, keep_gene, strict=True) if admitted]
    if matrix.shape[0] < 50 or matrix.shape[1] < 100:
        raise ValueError(f"{sample_id}: insufficient post-filter data {matrix.shape}")

    obs = positions[["array_row", "array_col", "pixel_row", "pixel_col"]].copy()
    obs.index = obs.index.astype(str)
    obs["sample_id"] = sample_id
    obs["patient_id"] = patient_id
    obs["technical_replicate"] = replicate
    coords = obs[["array_col", "array_row"]].to_numpy(dtype=np.float32)
    pixel_coords = obs[["pixel_col", "pixel_row"]].to_numpy(dtype=np.float32)
    adata = ad.AnnData(
        X=matrix,
        obs=obs,
        var=pd.DataFrame(index=unique_names(genes)),
        obsm={"spatial": coords, "spatial_pixel": pixel_coords},
    )
    adata.layers["counts"] = adata.X.copy()
    adata.uns.update(
        {
            "protocol_id": PROTOCOL_ID,
            "truth_sealed": True,
            "histology_available_to_methods": False,
            "k_policy": "estimate",
        }
    )
    inputs = output / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    input_path = inputs / f"{sample_id}.h5ad"
    adata.write_h5ad(input_path, compression="gzip")
    return {
        "sample_id": sample_id,
        "patient_id": patient_id,
        "technical_replicate": replicate,
        "n_spots": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "archive": archive.name,
        "archive_md5": observed_md5,
        "archive_sha256": digest(archive),
        "input_path": str(input_path),
        "input_sha256": digest(input_path),
        "truth_accessed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--receipt", type=Path, default=Path(__file__).with_name("registration_receipt.json")
    )
    parser.add_argument("--samples", default="")
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt.get("unlock_status") != "satisfied" or not receipt.get("public_issue"):
        raise RuntimeError("public registration receipt has not unlocked execution")
    requested = args.samples.split(",") if args.samples else list(SAMPLES)
    unknown = sorted(set(requested) - set(SAMPLES))
    if unknown:
        raise ValueError(f"unknown samples: {unknown}")
    records = [prepare_sample(sample, args.source, args.output) for sample in requested]
    patients = sorted({row["patient_id"] for row in records})
    manifest = {
        "schema_version": "histoweave.crc.source_manifest.v4",
        "protocol_id": PROTOCOL_ID,
        "prepared_utc": datetime.now(UTC).isoformat(),
        "registration": receipt,
        "records": records,
        "n_sections": len(records),
        "n_patients": len(patients),
        "patients": patients,
        "truth_accessed": False,
        "truth_storage": "not downloaded during label-free preparation",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "source_manifest.json", manifest)
    if not args.samples and (len(records) != 14 or len(patients) != 7):
        raise RuntimeError("registered 14-section / 7-patient panel is incomplete")


if __name__ == "__main__":
    main()
