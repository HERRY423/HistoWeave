"""Score frozen CRC predictions at the registered patient level after truth unsealing."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import adjusted_rand_score

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


def verify_authorization(results: Path, authorization_path: Path) -> dict[str, Any]:
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    prediction_path = results / "prediction_freeze.json"
    actions_path = results / "policy_actions.json"
    if authorization.get("schema_version") != "histoweave.crc.truth_unseal_authorization.v4":
        raise ValueError("v4 truth-unseal authorization is required")
    if authorization.get("truth_unseal_authorized") is not True:
        raise ValueError("truth access is not authorized")
    if sha256(prediction_path) != authorization.get("prediction_freeze_sha256"):
        raise ValueError("prediction freeze changed after truth authorization")
    if sha256(actions_path) != authorization.get("policy_actions_sha256"):
        raise ValueError("policy actions changed after truth authorization")
    return authorization


def load_truth(path: Path, expected_samples: set[str]) -> pd.DataFrame:
    truth = pd.read_csv(path, dtype=str)
    required = {"sample_id", "spot_id", "truth_label"}
    if not required.issubset(truth.columns):
        raise ValueError(f"truth table requires columns {sorted(required)}")
    truth = truth[list(sorted(required))].copy()
    if truth.isna().any().any() or (truth == "").any().any():
        raise ValueError("truth table contains missing identifiers or labels")
    if truth.duplicated(["sample_id", "spot_id"]).any():
        raise ValueError("truth table contains duplicate sample/spot identifiers")
    unknown = set(truth["sample_id"]) - expected_samples
    if unknown:
        raise ValueError(f"truth table contains unknown samples: {sorted(unknown)}")
    missing = expected_samples - set(truth["sample_id"])
    if missing:
        raise ValueError(f"truth table omits registered samples: {sorted(missing)}")
    return truth


def score_panel(
    prepared: Path,
    results: Path,
    truth_path: Path,
    authorization_path: Path,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    authorization = verify_authorization(results, authorization_path)
    source_path = prepared / "source_manifest.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if sha256(source_path) != authorization.get("source_manifest_sha256"):
        raise ValueError("prepared source manifest changed after truth authorization")
    records = source["records"]
    samples = {str(row["sample_id"]) for row in records}
    patient_by_sample = {
        str(row["sample_id"]): str(row["patient_id"]) for row in records
    }
    truth = load_truth(truth_path, samples)
    truth_by_sample = {
        sample: frame[["spot_id", "truth_label"]]
        for sample, frame in truth.groupby("sample_id", sort=False)
    }
    cell_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for sample in sorted(samples):
        sample_truth = truth_by_sample[sample]
        for method in METHODS:
            for seed in SEEDS:
                status_path = results / "predictions" / f"{sample}__{method}__seed{seed}.json"
                status = json.loads(status_path.read_text(encoding="utf-8"))
                if status.get("status") != "success":
                    failures.append(
                        {
                            "sample_id": sample,
                            "patient_id": patient_by_sample[sample],
                            "method": method,
                            "seed": seed,
                            "status": status.get("status"),
                            "error": status.get("error"),
                        }
                    )
                    continue
                prediction_path = Path(str(status["output_path"]))
                if sha256(prediction_path) != status.get("output_sha256"):
                    raise ValueError(f"prediction hash mismatch: {sample}/{method}/{seed}")
                prediction = pd.read_csv(prediction_path, dtype={"spot_id": str})
                if not {"spot_id", "label"}.issubset(prediction.columns):
                    raise ValueError(f"malformed prediction: {sample}/{method}/{seed}")
                if prediction["spot_id"].duplicated().any():
                    raise ValueError(f"duplicate predicted spots: {sample}/{method}/{seed}")
                aligned = sample_truth.merge(
                    prediction[["spot_id", "label"]],
                    on="spot_id",
                    how="inner",
                    validate="one_to_one",
                )
                if aligned.empty:
                    raise ValueError(f"no labelled spots align: {sample}/{method}/{seed}")
                if len(aligned) != len(sample_truth):
                    raise ValueError(
                        f"some uniquely labelled spots lack predictions: {sample}/{method}/{seed}"
                    )
                cell_rows.append(
                    {
                        "sample_id": sample,
                        "patient_id": patient_by_sample[sample],
                        "method": method,
                        "seed": seed,
                        "n_labelled_spots": int(len(aligned)),
                        "ari": float(adjusted_rand_score(aligned["truth_label"], aligned["label"])),
                    }
                )
    cells = pd.DataFrame(cell_rows)
    if cells.empty:
        raise ValueError("no successful prediction cells can be scored")
    sections = (
        cells.groupby(["sample_id", "patient_id", "method"], as_index=False)
        .agg(mean_seed_ari=("ari", "mean"), n_successful_seeds=("seed", "nunique"))
    )
    patients = (
        sections.groupby(["patient_id", "method"], as_index=False)
        .agg(
            mean_section_ari=("mean_seed_ari", "mean"),
            n_evaluable_sections=("sample_id", "nunique"),
        )
    )
    patient_matrix = (
        patients.pivot(index="patient_id", columns="method", values="mean_section_ari")
        .reindex(columns=list(METHODS))
        .reset_index()
    )
    availability = {
        method: int(patient_matrix[method].notna().sum()) for method in METHODS
    }
    strict_mask = patient_matrix[list(METHODS)].notna().all(axis=1)
    minimum_method_patients = min(availability.values())
    aligned_status = (
        "complete"
        if minimum_method_patients >= 5 and int(strict_mask.sum()) >= 5
        else "evidence_required"
    )
    actions = json.loads((results / "policy_actions.json").read_text(encoding="utf-8"))
    payload = {
        "schema_version": "histoweave.crc.scored_results.v4",
        "protocol_id": authorization["protocol_id"],
        "scored_utc": datetime.now(UTC).isoformat(),
        "truth_unseal_authorization_sha256": sha256(authorization_path),
        "truth_table_sha256": sha256(truth_path),
        "n_registered_patients": len(set(patient_by_sample.values())),
        "n_registered_sections": len(samples),
        "aggregation": (
            "ARI per section/seed; mean seeds within section; "
            "mean sections within patient"
        ),
        "no_section_or_seed_pseudoreplication": True,
        "method_patient_availability": availability,
        "n_strict_nine_method_patients": int(strict_mask.sum()),
        "strict_patient_ids": patient_matrix.loc[strict_mask, "patient_id"].tolist(),
        "aligned_sota_status": aligned_status,
        "prediction_failures": len(failures),
        "policy_status": actions["status"],
        "policy_endpoint_status": (
            "evidence_required"
            if actions["status"] == "evidence_required"
            else "requires_registered_policy_contrast_scoring"
        ),
        "claim_boundary": (
            "The same-mask method panel is descriptive. An evidence_required action "
            "does not support personalised-policy efficacy."
        ),
        "cell_scores": cell_rows,
    }
    return payload, patient_matrix, pd.DataFrame(failures)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    args = parser.parse_args()
    payload, patient_matrix, failures = score_panel(
        args.prepared, args.results, args.truth, args.authorization
    )
    args.results.mkdir(parents=True, exist_ok=True)
    patient_matrix.to_csv(args.results / "patient_method_matrix.csv", index=False)
    failures.to_csv(args.results / "failure_ledger.csv", index=False)
    (args.results / "scored_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    compact = {key: value for key, value in payload.items() if key != "cell_scores"}
    compact["method_mean_ari_same_patient_mask"] = {
        method: float(patient_matrix[method].mean()) for method in METHODS
    }
    compact["patient_best_method"] = {
        str(row["patient_id"]): str(row[list(METHODS)].astype(float).idxmax())
        for _, row in patient_matrix.iterrows()
    }
    compact["runtime_skip_failures"] = int(
        failures.get("error", pd.Series(dtype=str))
        .fillna("")
        .str.startswith("RuntimeSkip:")
        .sum()
    )
    (args.results / "results_summary.json").write_text(
        json.dumps(compact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
