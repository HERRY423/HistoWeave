"""Score DLPFC predictions and apply the frozen sequential policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from histoweave.benchmark.features import extract_features  # noqa: E402
from histoweave.data import SpatialTable  # noqa: E402

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


def _table_from_h5ad(path: Path) -> SpatialTable:
    adata = ad.read_h5ad(path)
    x = adata.layers["counts"] if "counts" in adata.layers else adata.X
    return SpatialTable(
        X=x,
        obs=adata.obs.copy(),
        var=adata.var.copy(),
        obsm={"spatial": np.asarray(adata.obsm["spatial"], dtype=float)},
    )


def score_cells(
    prepared: Path,
    results: Path,
    truth_dir: Path,
) -> pd.DataFrame:
    manifest = json.loads((prepared / "source_manifest.json").read_text(encoding="utf-8"))
    rows = []
    for record in manifest["records"]:
        sample_id = record["sample_id"]
        truth = pd.read_csv(truth_dir / f"{sample_id}.csv", index_col=0)
        y_true = truth["domain_truth"].astype(str)
        for method in METHODS:
            seed_aris = []
            for seed in SEEDS:
                status_path = results / "predictions" / f"{sample_id}__{method}__seed{seed}.json"
                if not status_path.is_file():
                    continue
                status = json.loads(status_path.read_text(encoding="utf-8"))
                if status.get("status") != "success" or not status.get("output_path"):
                    continue
                pred = pd.read_csv(status["output_path"])
                pred = pred.set_index("spot_id")
                common = y_true.index.intersection(pred.index)
                if len(common) < 10:
                    continue
                ari = float(
                    adjusted_rand_score(
                        y_true.loc[common].to_numpy(),
                        pred.loc[common, "label"].astype(str).to_numpy(),
                    )
                )
                seed_aris.append(ari)
                rows.append(
                    {
                        "sample_id": sample_id,
                        "donor_id": record["donor_id"],
                        "section_id": record["section_id"],
                        "method": method,
                        "seed": seed,
                        "ari": ari,
                    }
                )
            if not seed_aris:
                rows.append(
                    {
                        "sample_id": sample_id,
                        "donor_id": record["donor_id"],
                        "section_id": record["section_id"],
                        "method": method,
                        "seed": None,
                        "ari": np.nan,
                    }
                )
    return pd.DataFrame(rows)


def aggregate_donor_method(long: pd.DataFrame) -> pd.DataFrame:
    # mean seeds within section, mean sections within donor
    section = (
        long.dropna(subset=["ari"])
        .groupby(["donor_id", "section_id", "method"], as_index=False)["ari"]
        .mean()
    )
    donor = (
        section.groupby(["donor_id", "method"], as_index=False)["ari"]
        .mean()
        .pivot(index="donor_id", columns="method", values="ari")
    )
    return donor.reindex(columns=METHODS)


def donor_features(prepared: Path, feature_subset: list[str]) -> pd.DataFrame:
    manifest = json.loads((prepared / "source_manifest.json").read_text(encoding="utf-8"))
    by_donor: dict[str, list[dict[str, float]]] = {}
    for record in manifest["records"]:
        path = prepared / "inputs" / f"{record['sample_id']}.h5ad"
        feats = extract_features(_table_from_h5ad(path), include_domain=False)
        by_donor.setdefault(record["donor_id"], []).append(
            {k: float(feats.get(k, np.nan)) for k in feature_subset}
        )
    rows = []
    for donor, vectors in by_donor.items():
        arr = np.asarray([[v[k] for k in feature_subset] for v in vectors], dtype=float)
        means = np.nanmean(arr, axis=0)
        rows.append(
            {
                "donor_id": donor,
                **{
                    k: float(m) if np.isfinite(m) else 0.0
                    for k, m in zip(feature_subset, means, strict=True)
                },
            }
        )
    return pd.DataFrame(rows)


def apply_policy(
    donor_perf: pd.DataFrame,
    donor_feat: pd.DataFrame,
    policy: dict,
) -> dict:
    feature_subset = list(policy["feature_subset"])
    bank = policy["neighbor_bank"]
    x_bank = np.asarray(
        [[row["features"][k] for k in feature_subset] for row in bank], dtype=float
    )
    y_bank = np.asarray(
        [[row["performance"][m] for m in METHODS] for row in bank], dtype=float
    )
    global_method = policy["global_method"]
    g = METHODS.index(global_method)
    thr = float(policy["deployment_threshold"])
    scaler = RobustScaler().fit(x_bank)
    nn = NearestNeighbors(n_neighbors=1).fit(scaler.transform(x_bank))

    actions = []
    for _, row in donor_feat.iterrows():
        donor = str(row["donor_id"])
        x = np.asarray([[float(row[k]) for k in feature_subset]], dtype=float)
        ind = int(nn.kneighbors(scaler.transform(x), return_distance=False)[0, 0])
        scores = y_bank[ind]
        pick = int(scores.argmax())
        gain = float(scores[pick] - scores[g])
        if pick != g and gain >= thr:
            selected = METHODS[pick]
            action = "personalised_set"
        else:
            selected = global_method
            action = "global_default"
        perf = donor_perf.loc[donor]
        best = float(np.nanmax(perf.to_numpy(dtype=float)))
        selected_ari = float(perf[selected]) if pd.notna(perf[selected]) else float("nan")
        global_ari = float(perf[global_method]) if pd.notna(perf[global_method]) else float("nan")
        deployed_regret = best - selected_ari
        global_regret = best - global_ari
        actions.append(
            {
                "donor_id": donor,
                "action": action,
                "selected_method": selected,
                "predicted_gain": gain,
                "threshold": thr,
                "neighbor_unit": bank[ind]["unit_id"],
                "best_ari": best,
                "selected_ari": selected_ari,
                "global_ari": global_ari,
                "deployed_regret": deployed_regret,
                "global_regret": global_regret,
                "regret_difference": deployed_regret - global_regret,
            }
        )

    coverage = float(np.mean([a["action"] == "personalised_set" for a in actions]))
    mean_delta = float(np.mean([a["regret_difference"] for a in actions]))
    # n=3 bootstrap is descriptive only
    vals = np.asarray([a["regret_difference"] for a in actions], dtype=float)
    rng = np.random.default_rng(20260801)
    draws = rng.integers(0, len(vals), size=(10000, len(vals)))
    means = vals[draws].mean(axis=1)
    lo, hi = float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))
    success = bool(coverage >= 1 / 3 and mean_delta < 0.0)
    return {
        "schema_version": "histoweave.dlpfc_sequential_confirmation.results.v5",
        "protocol_id": "histoweave-dlpfc-sequential-confirmation-2026-08",
        "n_donors": len(actions),
        "global_method": global_method,
        "deployment_threshold": thr,
        "actions": actions,
        "evaluation": {
            "coverage": coverage,
            "n_personalised": int(sum(a["action"] == "personalised_set" for a in actions)),
            "mean_deployed_regret": float(np.mean([a["deployed_regret"] for a in actions])),
            "mean_global_regret": float(np.mean([a["global_regret"] for a in actions])),
            "mean_regret_difference": mean_delta,
            "bootstrap_95_interval_regret_difference_descriptive_n3": [lo, hi],
        },
        "sequential_confirmation_success": success,
        "claim_boundary": (
            "n=3 donors; bootstrap CI is descriptive. DLPFC was previously used for "
            "T1 oracle-K dual-track reporting. Policy parameters excluded DLPFC outcomes."
        ),
        "donor_method_matrix": donor_perf.reset_index().to_dict(orient="records"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepared",
        type=Path,
        default=ROOT / "datasets_cache" / "dlpfc_v5_prepared",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT / "datasets_cache" / "dlpfc_v5_results",
    )
    parser.add_argument(
        "--truth",
        type=Path,
        default=ROOT / "datasets_cache" / "dlpfc_v5_private_truth",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=ROOT / "sequential_confirmation_v5" / "results" / "frozen_policy.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "sequential_confirmation_v5" / "results" / "confirmation_results.json",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    long = score_cells(args.prepared, args.results, args.truth)
    long.to_csv(args.output.parent / "section_seed_scores.csv", index=False)
    donor_perf = aggregate_donor_method(long)
    donor_perf.to_csv(args.output.parent / "donor_method_matrix.csv")
    # Require full nine-method finite scores for strict mask.
    strict = donor_perf.dropna(axis=0, how="any")
    if len(strict) < len(donor_perf):
        print(
            f"warning: {len(donor_perf) - len(strict)} donors lack complete nine-method scores",
            flush=True,
        )
    donor_feat = donor_features(args.prepared, list(policy["feature_subset"]))
    # Align donors present in both.
    common = sorted(set(strict.index) & set(donor_feat["donor_id"]))
    if not common:
        raise SystemExit("no donors with complete scores and features")
    result = apply_policy(
        strict.loc[common],
        donor_feat[donor_feat["donor_id"].isin(common)].reset_index(drop=True),
        policy,
    )
    result["n_strict_donors"] = len(common)
    result["incomplete_donors"] = [
        d for d in donor_perf.index if d not in common
    ]
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "n_strict_donors": len(common),
                "coverage": result["evaluation"]["coverage"],
                "mean_regret_difference": result["evaluation"]["mean_regret_difference"],
                "success": result["sequential_confirmation_success"],
                "actions": result["actions"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
