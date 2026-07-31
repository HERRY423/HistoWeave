"""Regenerate and verify the HistoWeave P0 submission freeze v2.

This freeze does not rewrite the legacy v1 figure bundle. It locks the P0
evidence-admission implementation, adversarial audit, method-coverage ledger,
manuscript claim boundaries, and prospective-registration readiness status.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "submission_freeze_v2"
AUDIT = ROOT / "p0_validation_results" / "evidence_admission"

FREEZE_DATE = "2026-07-26"
SCHEMA = "histoweave.submission_freeze.v2"

SOURCE_PATHS = (
    "src/histoweave/benchmark/recommend.py",
    "src/histoweave/benchmark/decision.py",
    "src/histoweave/benchmark/evidence_audit.py",
    "scripts/run_p0_evidence_audit.py",
    "tests/test_decision.py",
    "scripts/update_zenodo_doi.py",
    "scripts/build_reference_artefact_manifest.py",
    "tests/test_evidence_audit.py",
    "benchmark_external_validation/decision_validation.json",
    "examples/case_study_intercepted_recommendation.py",
    "benchmark_external_validation/recommendation_loocv.json",
    "tests/test_submission_freeze_v2.py",
    "benchmark_external_validation/benchmark_long.csv",
    "benchmark_external_validation/strict_external_panel_v2/loocv_summary.json",
    "benchmark_external_validation/strict_external_panel_v2/sota_coverage.csv",
    "5x15_spatial_aware/performance_matrix_mean_full.csv",
    "non_oracle_k_sota/summary.json",
    "protocol_endpoints_results/selective_regret_coverage.json",
    "benchmark_external_validation/independent_test_wu2021/preregistered_protocol.json",
    "benchmark_external_validation/independent_test_wu2021/independent_test_summary.json",
    "benchmark_external_validation/independent_test_wu2021/independence_audit.json",
    "prospective_validation_v2/protocol.json",
    "prospective_validation_v2/STATUS.md",
    "manuscript/main_p0_archive.tex",
    "reference_artefacts/MANIFEST.json",
    "manuscript/cover_letter_p0_archive.md",
    "manuscript/supplementary_p0_archive.tex",
    "submission_freeze_v1/main_figures.lock.json",
    "submission_freeze_v1/DATA_CODE_AVAILABILITY.md",
    "submission_freeze_v2/reproduce_submission_freeze.py",
)

AUDIT_PATHS = (
    "p0_validation_results/evidence_admission/audit_summary.json",
    "p0_validation_results/evidence_admission/adversarial_corpus_results.json",
    "p0_validation_results/evidence_admission/manifest.json",
    "p0_validation_results/evidence_admission/REPORT.md",
    "p0_validation_results/evidence_admission/validation_source.json",
    "p0_validation_results/evidence_admission/validation_valid.json",
    "p0_validation_results/evidence_admission/validation_oracle_k.json",
    "p0_validation_results/evidence_admission/validation_task_mismatch.json",
    "p0_validation_results/evidence_admission/validation_panel_mismatch.json",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": _sha_bytes(raw)}


def _generated_record(text: str) -> dict[str, Any]:
    raw = text.encode("utf-8")
    return {"bytes": len(raw), "sha256": _sha_bytes(raw)}


def _coverage_ledger() -> dict[str, Any]:
    dlpfc_path = ROOT / "5x15_spatial_aware" / "performance_matrix_mean_full.csv"
    with dlpfc_path.open(newline="", encoding="utf-8") as handle:
        dlpfc_header = next(csv.reader(handle))[1:]

    external_path = ROOT / "benchmark_external_validation" / "benchmark_long.csv"
    with external_path.open(newline="", encoding="utf-8") as handle:
        external_rows = list(csv.DictReader(handle))
    nominal = sorted({row["method"] for row in external_rows})
    cells: dict[str, list[str]] = defaultdict(list)
    for row in external_rows:
        cells[row["method"]].append(row["ari"].strip())
    fully_finite = sorted(method for method, values in cells.items() if values and all(values))
    no_finite = sorted(method for method, values in cells.items() if not any(values))

    strict = _read_json(
        ROOT / "benchmark_external_validation" / "strict_external_panel_v2" / "loocv_summary.json"
    )
    non_oracle = _read_json(ROOT / "non_oracle_k_sota" / "summary.json")
    audit = _read_json(AUDIT / "audit_summary.json")

    ledger = {
        "schema_version": "histoweave.method_coverage_ledger.v2",
        "freeze_date": FREEZE_DATE,
        "claim_boundary": (
            "Panels are reported separately. A method absent from a panel is not treated "
            "as evaluated, and oracle-K evidence cannot unlock non-oracle personalisation."
        ),
        "panels": [
            {
                "id": "dlpfc_oracle_5x20",
                "task": "spatial_domain",
                "units": 5,
                "unit_kind": "slice",
                "seeds": [42, 1, 2],
                "k_policy": "oracle",
                "n_method_configurations": len(dlpfc_header),
                "method_configurations": dlpfc_header,
                "source": "5x15_spatial_aware/performance_matrix_mean_full.csv",
            },
            {
                "id": "external_oracle_5x15",
                "task": "spatial_domain",
                "units": len({row["dataset"] for row in external_rows}),
                "unit_kind": "dataset",
                "seeds": sorted({int(row["seed"]) for row in external_rows}),
                "k_policy": "oracle",
                "n_prespecified_methods": len(nominal),
                "prespecified_methods": nominal,
                "n_fully_finite_methods": len(fully_finite),
                "fully_finite_methods": fully_finite,
                "methods_without_finite_ari": no_finite,
                "aligned_dlpfc_sota_families": ["banksy_py"],
                "missing_dlpfc_sota_families": [
                    "spagcn",
                    "stagate",
                    "graphst",
                    "bayesspace",
                ],
                "source": "benchmark_external_validation/benchmark_long.csv",
            },
            {
                "id": "strict_task_stratified_v2",
                "task": "spatial_domain",
                "units": int(strict["n_queries"]),
                "unit_kind": "study_or_donor",
                "k_policy": "oracle_derived_source_landscape",
                "methods": list(strict["locked_parameters"]["methods"]),
                "n_methods": len(strict["locked_parameters"]["methods"]),
                "personalisation_superior": bool(strict["primary_superior"]),
                "source": (
                    "benchmark_external_validation/strict_external_panel_v2/loocv_summary.json"
                ),
            },
            {
                "id": "dlpfc_dual_k_sota",
                "task": "spatial_domain",
                "units": len(non_oracle["slices"]),
                "unit_kind": "slice",
                "methods": list(non_oracle["methods"]),
                "n_methods": len(non_oracle["methods"]),
                "k_policy": "oracle_and_three_estimated_tracks",
                "seed_scope": "one run per slice-mode combination",
                "source": "non_oracle_k_sota/summary.json",
            },
            {
                "id": "p0_adversarial_evidence_admission",
                "task": "decision_protocol",
                "n_cases": int(audit["n_cases"]),
                "invalid_cases": int(audit["invalid_cases"]),
                "valid_controls": int(audit["valid_cases"]),
                "incompatible_evidence_admission_rate": float(
                    audit["incompatible_evidence_admission_rate"]
                ),
                "valid_evidence_false_rejection_rate": float(
                    audit["valid_evidence_false_rejection_rate"]
                ),
                "dominated_selection_rate": float(audit["dominated_selection_rate"]),
                "source": "p0_validation_results/evidence_admission/audit_summary.json",
            },
        ],
    }
    if len(dlpfc_header) != 20:
        raise RuntimeError("DLPFC coverage drift: expected 20 configurations")
    if len(nominal) != 15 or len(fully_finite) != 13:
        raise RuntimeError("External coverage drift: expected 15 nominal / 13 finite")
    if not audit.get("all_cases_passed"):
        raise RuntimeError("P0 evidence-admission audit failed")
    return ledger


def _coverage_markdown(ledger: dict[str, Any]) -> str:
    rows = []
    for panel in ledger["panels"]:
        methods = panel.get("n_method_configurations", panel.get("n_methods", "--"))
        if panel["id"] == "external_oracle_5x15":
            methods = "15 prespecified / 13 fully finite"
        rows.append(
            f"| `{panel['id']}` | {panel.get('units', panel.get('n_cases'))} | "
            f"{methods} | {panel.get('k_policy', '--')} | `{panel['source']}` |"
        )
    return (
        "# P0 method and evidence coverage ledger\n\n"
        "Panels are not pooled when task, K policy, method coverage, or split unit differs.\n\n"
        "| Panel | Units/cases | Methods/configurations | K policy | Source |\n"
        "|---|---:|---:|---|---|\n"
        + "\n".join(rows)
        + "\n\nThe five-dataset external panel is not a full aligned SOTA comparison: "
        "SpaGCN, STAGATE, GraphST, and BayesSpace are missing; only BANKSY overlaps. "
        "All external results are spatial-region, oracle-K evidence and cannot establish "
        "cell-type performance or unlock non-oracle personalisation.\n"
    )


def _verify_decision_validation_binding() -> dict[str, Any]:
    evidence_path = ROOT / "benchmark_external_validation" / "decision_validation.json"
    evidence = _read_json(evidence_path)
    if evidence.get("schema_version") != "histoweave.validation_evidence.v2":
        raise RuntimeError("Decision validation schema is not v2")
    verified = []
    for item in evidence.get("source_artifacts", []):
        source = evidence_path.parent / item["path"]
        observed = _record(source)["sha256"]
        if observed != item["sha256"]:
            raise RuntimeError(f"Validation source hash mismatch: {source}")
        verified.append(item["path"])
    if not verified:
        raise RuntimeError("Decision validation has no verified source artifacts")
    return {
        "schema": evidence["schema_version"],
        "verified_source_artifacts": verified,
        "task": evidence.get("task"),
        "metric": evidence.get("metric"),
        "k_policy": evidence.get("k_policy"),
        "can_unlock_non_oracle_personalisation": False,
    }


def _expected_outputs() -> dict[str, str]:
    for relative in SOURCE_PATHS + AUDIT_PATHS:
        if not (ROOT / relative).is_file():
            raise FileNotFoundError(ROOT / relative)

    ledger = _coverage_ledger()
    ledger_json = _json_text(ledger)
    ledger_md = _coverage_markdown(ledger)
    source_records = {relative: _record(ROOT / relative) for relative in SOURCE_PATHS + AUDIT_PATHS}
    prospective = _read_json(ROOT / "prospective_validation_v2" / "protocol.json")
    audit = _read_json(AUDIT / "audit_summary.json")
    manifest = {
        "schema_version": SCHEMA,
        "freeze_date": FREEZE_DATE,
        "status": "p0_local_complete_public_preregistration_pending",
        "source_artifacts": source_records,
        "generated_artifacts": {
            "submission_freeze_v2/method_coverage_ledger.json": _generated_record(ledger_json),
            "submission_freeze_v2/METHOD_COVERAGE.md": _generated_record(ledger_md),
        },
        "validation": {
            "evidence_admission_audit": audit,
            "decision_validation_binding": _verify_decision_validation_binding(),
            "prospective_registration_status": prospective["status"],
            "prospective_execution_permitted": prospective["registration_gate"][
                "execution_permitted"
            ],
        },
        "claim_boundaries": [
            "External five-dataset results are oracle-K spatial-region evidence.",
            (
                "The external panel has 15 prespecified and 13 fully finite methods; "
                "it is not a full aligned SOTA panel."
            ),
            (
                "The Wu analysis is a negative in-repository stress test, not a "
                "publicly timestamped preregistration."
            ),
            "No current held-out artifact can unlock non-oracle personalised deployment.",
        ],
    }
    manifest_text = _json_text(manifest)
    report = (
        "# HistoWeave P0 submission freeze v2\n\n"
        "Local P0 engineering and verification are complete. The evidence gate is fail-closed "
        "for task, ground truth, K policy, metric, method panel, grouped holdout, and "
        "source hashes.\n\n"
        f"- Adversarial cases: {audit['n_cases']} ({audit['invalid_cases']} invalid; "
        f"{audit['valid_cases']} valid controls)\n"
        "- Incompatible-evidence admission rate: "
        f"{audit['incompatible_evidence_admission_rate']:.3f}\n"
        "- Valid-evidence false-rejection rate: "
        f"{audit['valid_evidence_false_rejection_rate']:.3f}\n"
        f"- Dominated-selection rate: {audit['dominated_selection_rate']:.3f}\n"
        "- External panel: 15 prespecified methods, 13 fully finite, oracle K\n"
        "- Public prospective registration: pending; execution remains blocked\n\n"
        "Run `python submission_freeze_v2/reproduce_submission_freeze.py --check` "
        "to verify every locked source and generated artifact.\n"
    )
    return {
        "method_coverage_ledger.json": ledger_json,
        "METHOD_COVERAGE.md": ledger_md,
        "submission_freeze_manifest.json": manifest_text,
        "REPORT.md": report,
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="do not rerun the adversarial audit before freezing",
    )
    args = parser.parse_args(argv)

    if not args.check and not args.skip_audit:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_p0_evidence_audit.py")],
            cwd=ROOT,
            check=True,
        )

    expected = _expected_outputs()
    FREEZE.mkdir(parents=True, exist_ok=True)
    if args.check:
        mismatches = [
            name
            for name, text in expected.items()
            if not (FREEZE / name).is_file() or (FREEZE / name).read_text(encoding="utf-8") != text
        ]
        if mismatches:
            _LOGGER.error("Freeze mismatch: %s", ", ".join(mismatches))
            return 1
        _LOGGER.info("HistoWeave P0 submission freeze v2: VERIFIED")
        return 0

    for name, text in expected.items():
        (FREEZE / name).write_text(text, encoding="utf-8")
    _LOGGER.info("HistoWeave P0 submission freeze v2: FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
