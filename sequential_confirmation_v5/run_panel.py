"""Run the locked nine-method DLPFC panel without reading pathology truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans, SpectralClustering
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = ROOT / "5x15_spatial_aware"
if str(ADAPTERS) not in sys.path:
    sys.path.insert(0, str(ADAPTERS))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from adapters import graphst_adapter, spagcn_adapter, stagate_adapter  # noqa: E402
from histoweave.benchmark.k_selection import estimate_n_domains  # noqa: E402
from histoweave.data import SpatialTable  # noqa: E402

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
R_SCRIPTS = ROOT / "prospective_validation_v4"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dense_counts(adata: ad.AnnData) -> np.ndarray:
    value = adata.layers.get("counts", adata.X)
    if hasattr(value, "toarray"):
        value = value.toarray()
    return np.asarray(value, dtype=np.float32)


def simple_embedding(counts: np.ndarray, seed: int) -> np.ndarray:
    totals = counts.sum(axis=1, keepdims=True)
    norm = np.divide(counts, totals, out=np.zeros_like(counts), where=totals > 0) * 10000.0
    logged = np.log1p(norm)
    variance = logged.var(axis=0)
    keep = np.argsort(variance)[-min(2000, logged.shape[1]) :]
    scaled = StandardScaler().fit_transform(logged[:, keep])
    n_components = min(15, scaled.shape[0] - 1, scaled.shape[1])
    return PCA(n_components=n_components, random_state=seed).fit_transform(scaled)


def estimate_k(adata: ad.AnnData) -> dict[str, object]:
    counts = dense_counts(adata)
    table = SpatialTable(
        X=counts,
        obs=adata.obs.copy(),
        var=adata.var.copy(),
        obsm={"spatial": np.asarray(adata.obsm["spatial"])},
    )
    # Cap spots and high-variance genes to stay within workstation memory on
    # full Visium sections (~3–5k spots × 30k genes).
    result = estimate_n_domains(
        table,
        method="ensemble",
        k_min=2,
        k_max=12,
        n_pcs=15,
        random_state=0,
        max_obs=2500,
        knn=6,
        spatial_weight=0.75,
    )
    payload = result.to_dict()
    if payload.get("oracle_k") is not None:
        raise RuntimeError("oracle K unexpectedly visible in prediction input")
    return payload


def run_python_method(
    method: str,
    adata: ad.AnnData,
    q: int,
    seed: int,
    *,
    embedding: np.ndarray | None = None,
) -> np.ndarray:
    counts = dense_counts(adata)
    coords = np.asarray(adata.obsm["spatial"], dtype=np.float32)
    genes = adata.var_names.astype(str).tolist()
    array_coords = None
    if {"array_row", "array_col"}.issubset(adata.obs.columns):
        array_coords = adata.obs[["array_row", "array_col"]].to_numpy()
    if method == "spagcn":
        return np.asarray(
            spagcn_adapter.run(
                counts, coords, genes, seed=seed, n_domains=q, array_coords=array_coords
            )
        )
    if method == "stagate":
        return np.asarray(
            stagate_adapter.run(counts, coords, genes, seed=seed, n_domains=q)
        )
    if method == "graphst":
        return np.asarray(
            graphst_adapter.run(counts, coords, genes, seed=seed, n_domains=q)
        )
    if embedding is None:
        embedding = simple_embedding(counts, seed)
    if method == "spectral":
        return SpectralClustering(
            n_clusters=q,
            random_state=seed,
            affinity="nearest_neighbors",
            n_neighbors=min(10, len(embedding) - 1),
            assign_labels="kmeans",
        ).fit_predict(embedding)
    if method == "gaussian_mixture":
        return GaussianMixture(
            n_components=q, covariance_type="full", random_state=seed, n_init=5
        ).fit_predict(embedding)
    if method == "kmeans":
        return KMeans(n_clusters=q, random_state=seed, n_init=20).fit_predict(embedding)
    if method == "agglomerative":
        return AgglomerativeClustering(n_clusters=q, linkage="ward").fit_predict(embedding)
    raise KeyError(method)


def run_r_method(
    method: str,
    input_path: Path,
    output_path: Path,
    q: int,
    seed: int,
    r_lib: Path,
    rscript: Path,
) -> None:
    script = R_SCRIPTS / f"run_{method}_v4.R"
    proc = subprocess.run(
        [
            str(rscript),
            "--vanilla",
            str(script),
            str(input_path),
            str(output_path),
            str(seed),
            str(q),
            str(r_lib),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=7200,
        check=False,
        env={**os.environ, "R_LIBS_USER": str(r_lib)},
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{method} R bridge failed ({proc.returncode})\n"
            f"stdout: {proc.stdout[-2000:]}\nstderr: {proc.stderr[-4000:]}"
        )


def run_cell(
    method: str,
    sample_id: str,
    seed: int,
    input_path: Path,
    out_dir: Path,
    k_payload: dict[str, object],
    r_lib: Path,
    rscript: Path,
    input_sha256: str,
) -> dict[str, object]:
    cell_dir = out_dir / "predictions"
    cell_dir.mkdir(parents=True, exist_ok=True)
    output_path = cell_dir / f"{sample_id}__{method}__seed{seed}.csv"
    status_path = cell_dir / f"{sample_id}__{method}__seed{seed}.json"
    if status_path.is_file():
        existing = json.loads(status_path.read_text(encoding="utf-8"))
        if existing.get("input_sha256") == input_sha256:
            return existing

    adata = ad.read_h5ad(input_path)
    # Guard: no truth columns in prediction inputs.
    for col in ("domain_truth", "spatialLIBD_layer", "layer"):
        if col in adata.obs.columns:
            raise RuntimeError(f"{sample_id}: truth column {col} present in label-free input")
    q = int(k_payload["k"])
    started = time.perf_counter()
    status = "success"
    error = None
    try:
        if method in {"bayesspace", "banksy"}:
            run_r_method(method, input_path, output_path, q, seed, r_lib, rscript)
            pred = pd.read_csv(output_path)
            if pred["spot_id"].astype(str).tolist() != adata.obs_names.astype(str).tolist():
                raise RuntimeError(f"{method}: output spot order does not match input")
        else:
            embedding = None
            if method in {"spectral", "gaussian_mixture", "kmeans", "agglomerative"}:
                cache_dir = out_dir / "embedding_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path = cache_dir / f"{sample_id}__seed{seed}__{input_sha256[:12]}.npy"
                if cache_path.is_file():
                    embedding = np.load(cache_path)
                else:
                    embedding = simple_embedding(dense_counts(adata), seed)
                    np.save(cache_path, embedding)
            labels = run_python_method(method, adata, q, seed, embedding=embedding)
            pd.DataFrame(
                {"spot_id": adata.obs_names.astype(str), "label": labels.astype(str)}
            ).to_csv(output_path, index=False)
    except Exception as exc:  # noqa: BLE001 — retain every failure
        status = "failed"
        error = f"{type(exc).__name__}: {exc}"
        if output_path.exists():
            output_path.unlink()
    payload = {
        "sample_id": sample_id,
        "method": method,
        "seed": seed,
        "estimated_k": q,
        "input_sha256": input_sha256,
        "status": status,
        "error": error,
        "seconds": time.perf_counter() - started,
        "output_path": str(output_path) if output_path.is_file() else None,
        "output_sha256": sha256(output_path) if output_path.is_file() else None,
        "finished_utc": datetime.now(UTC).isoformat(),
    }
    write_json(status_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepared",
        type=Path,
        default=ROOT / "datasets_cache" / "dlpfc_v5_prepared",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "datasets_cache" / "dlpfc_v5_results",
    )
    parser.add_argument(
        "--r-lib",
        type=Path,
        default=Path(r"C:\Spatial Transcriptomics\histoweave-r-lib-v3"),
    )
    parser.add_argument(
        "--rscript",
        type=Path,
        default=Path(r"C:\R1\R-4.5.3\bin\Rscript.exe"),
    )
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--samples", default="")
    parser.add_argument("--seeds", default=",".join(map(str, SEEDS)))
    args = parser.parse_args()

    source_manifest = json.loads(
        (args.prepared / "source_manifest.json").read_text(encoding="utf-8")
    )
    all_samples = [str(row["sample_id"]) for row in source_manifest["records"]]
    input_hashes = {
        str(row["sample_id"]): str(row["input_sha256"])
        for row in source_manifest["records"]
    }
    samples = [s for s in args.samples.split(",") if s] or all_samples
    methods = [m for m in args.methods.split(",") if m]
    seeds = [int(v) for v in args.seeds.split(",") if v]
    args.output.mkdir(parents=True, exist_ok=True)

    k_path = args.output / "k_estimates.json"
    k_estimates = json.loads(k_path.read_text(encoding="utf-8")) if k_path.is_file() else {}
    for sample_id in samples:
        if sample_id not in k_estimates:
            adata = ad.read_h5ad(args.prepared / "inputs" / f"{sample_id}.h5ad")
            k_estimates[sample_id] = estimate_k(adata)
            write_json(k_path, k_estimates)
            print(f"estimated K for {sample_id}: {k_estimates[sample_id].get('k')}")

    cells = []
    for sample_id in samples:
        for method in methods:
            for seed in seeds:
                print(f"run {sample_id} {method} seed={seed}", flush=True)
                cells.append(
                    run_cell(
                        method,
                        sample_id,
                        seed,
                        args.prepared / "inputs" / f"{sample_id}.h5ad",
                        args.output,
                        k_estimates[sample_id],
                        args.r_lib,
                        args.rscript,
                        input_hashes[sample_id],
                    )
                )
                print(
                    f"  -> {cells[-1]['status']} ({cells[-1].get('seconds', 0):.1f}s)",
                    flush=True,
                )

    write_json(
        args.output / "prediction_manifest.json",
        {
            "schema_version": "histoweave.dlpfc_v5_predictions.v1",
            "n_cells": len(cells),
            "n_success": sum(1 for c in cells if c["status"] == "success"),
            "n_failed": sum(1 for c in cells if c["status"] != "success"),
            "cells": cells,
            "finished_utc": datetime.now(UTC).isoformat(),
        },
    )
    print(
        json.dumps(
            {
                "n_cells": len(cells),
                "n_success": sum(1 for c in cells if c["status"] == "success"),
                "n_failed": sum(1 for c in cells if c["status"] != "success"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
