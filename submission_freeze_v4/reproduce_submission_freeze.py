"""Create or verify the 2026-08-01 HistoWeave submission freeze v4.

Version 4 extends the validated v3 freeze builder without rewriting the
historical v3 artefacts.  It binds the current manuscript to the registered
HER2ST and CRC non-oracle studies, the strict same-mask comparison, and the
fixed-split synthetic construct-validity experiment.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "submission_freeze_v4"


def _load_v3_builder() -> ModuleType:
    path = ROOT / "submission_freeze_v3" / "reproduce_submission_freeze.py"
    spec = importlib.util.spec_from_file_location("histoweave_freeze_v3_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load freeze builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V3 = _load_v3_builder()
V3.FREEZE = FREEZE
V3.SCHEMA = "histoweave.submission_freeze.v4"
V3.FREEZE_DATE = "2026-08-01"

CURRENT_EVIDENCE_PATHS = (
    "submission_freeze_v3/submission_freeze_manifest.json",
    "submission_freeze_v3/REPORT.md",
    "multistudy_validation/study_registry.json",
    "multistudy_validation/analyze_same_mask.py",
    "multistudy_validation/her2st_donor_method_matrix.csv",
    "multistudy_validation/same_mask_results.json",
    "prospective_validation_v4/README.md",
    "prospective_validation_v4/authorize_truth_unseal.py",
    "prospective_validation_v4/protocol.json",
    "prospective_validation_v4/registration_receipt.json",
    "prospective_validation_v4/development_meta_panel_status.json",
    "prospective_validation_v4/execution_incident_20260801.json",
    "prospective_validation_v4/freeze_policy_actions.py",
    "prospective_validation_v4/freeze_predictions.py",
    "prospective_validation_v4/import_crc_truth.py",
    "prospective_validation_v4/prepare_crc_v4.py",
    "prospective_validation_v4/record_runtime_skips.py",
    "prospective_validation_v4/run_banksy_v4.R",
    "prospective_validation_v4/run_bayesspace_v4.R",
    "prospective_validation_v4/run_panel.py",
    "prospective_validation_v4/score_crc_v4.py",
    "prospective_validation_v4/results/results_summary.json",
    "prospective_validation_v4/results/patient_method_matrix.csv",
    "prospective_validation_v4/results/failure_ledger.csv",
    "prospective_validation_v4/results/truth_import_manifest.json",
    "synthetic_validation_v2/protocol.json",
    "synthetic_validation_v2/results/results.json",
    "synthetic_validation_v2/results/INVALID_RUN_v2_0.md",
    "synthetic_validation_v2/results/FAILED_RUN_v2_1.md",
    "synthetic_validation_v2/run_validation.py",
    "src/histoweave/__init__.py",
    "src/histoweave/benchmark/fixed_split_selection.py",
    "docs/zenodo_doi_guide.md",
    "tests/test_fixed_split_selection.py",
    "tests/test_synthetic_selection_v2.py",
    "tests/test_multistudy_same_mask.py",
    "tests/test_crc_v4_contract.py",
    "tests/test_crc_v4_freeze.py",
    "tests/test_crc_v4_scoring.py",
)

V4_IMPLEMENTATION_PATHS = (
    "submission_freeze_v4/reproduce_submission_freeze.py",
    "tests/test_submission_freeze_v4.py",
    ".zenodo.json",
    "CITATION.cff",
)

V3.EVIDENCE_PATHS = V3.EVIDENCE_PATHS + CURRENT_EVIDENCE_PATHS
V3.IMPLEMENTATION_PATHS = V4_IMPLEMENTATION_PATHS
V3.SOURCE_PATHS = (
    V3.MANUSCRIPT_PATHS
    + V3.FIGURE_PATHS
    + V3.AUDIT_PATHS
    + V3.EVIDENCE_PATHS
    + V3.IMPLEMENTATION_PATHS
)
V3.FREEZE_CRITICAL_TESTS = V3.FREEZE_CRITICAL_TESTS + (
    "tests/test_fixed_split_selection.py",
    "tests/test_synthetic_selection_v2.py",
    "tests/test_multistudy_same_mask.py",
    "tests/test_crc_v4_contract.py",
    "tests/test_crc_v4_freeze.py",
    "tests/test_crc_v4_scoring.py",
)

_v3_report_text = V3._report_text


def _report_text(audit: dict[str, Any], regression: dict[str, Any]) -> str:
    report = _v3_report_text(audit, regression)
    report = report.replace("submission freeze v3", "submission freeze v4")
    report = report.replace("submission_freeze_v3/", "submission_freeze_v4/")
    report = report.replace(
        "Scientific risks remain explicit: HER2ST personalisation coverage is zero "
        "(fail-closed global default; not personalised superiority), LOOCV is "
        "editorially vulnerable and diagnostic-only, the diagnostic external panel is "
        "not a complete aligned SOTA comparison, and Wu remains a secondary oracle-K "
        "stress test only.",
        "Scientific risks remain explicit: the real-study policies still do not show "
        "improved personalised selection (HER2ST uses the global default and CRC returns "
        "evidence_required); the strict same-mask panel contains 13 units across two "
        "studies; 15 CRC attempts were user-authorised runtime skips without imputation; "
        "and the positive selection result is synthetic construct validity only.",
    )
    return report


V3._report_text = _report_text
_v3_expected_outputs = V3._expected_outputs


def _expected_outputs() -> dict[str, str]:
    outputs = _v3_expected_outputs()
    report = outputs["REPORT.md"]
    inventory = outputs["SUBMISSION_FILE_INVENTORY.md"]
    manifest = json.loads(outputs["submission_freeze_manifest.json"])
    multistudy = V3._read_json(ROOT / "multistudy_validation" / "same_mask_results.json")
    crc = V3._read_json(
        ROOT / "prospective_validation_v4" / "results" / "results_summary.json"
    )
    synthetic = V3._read_json(
        ROOT / "synthetic_validation_v2" / "results" / "results.json"
    )

    manifest["generated_artifacts"] = {
        "submission_freeze_v4/REPORT.md": V3._generated_record(report),
        "submission_freeze_v4/SUBMISSION_FILE_INVENTORY.md": V3._generated_record(
            inventory
        ),
    }
    manifest["multistudy_nonoracle_validation"] = {
        "completed_studies": multistudy["n_completed_studies"],
        "strict_units": sum(
            study["n_strict_nine_method_units"] for study in multistudy["studies"]
        ),
        "inference": multistudy["cross_study_inference"],
        "crc_strict_patients": crc["n_strict_nine_method_patients"],
        "crc_policy_status": crc["policy_endpoint_status"],
        "crc_prediction_failures": crc["prediction_failures"],
        "crc_runtime_skips": crc["runtime_skip_failures"],
    }
    manifest["synthetic_construct_validity"] = {
        "success": synthetic["success"],
        "signal_coverage": synthetic["signal_test"]["coverage"],
        "signal_mean_regret_difference": synthetic["signal_test"][
            "mean_regret_difference"
        ],
        "null_coverage": synthetic["null_test"]["coverage"],
        "claim_boundary": synthetic["claim_boundary"],
    }
    manifest["scientific_risks"] = [
        "Neither real external study establishes improved personalised selection.",
        "The strict common panel has 13 units across only two studies.",
        "CRC contains 15 disclosed user-authorised runtime skips and 17 total failures.",
        "Synthetic positive selection is construct validity, not biological validation.",
        "The Wu cohort remains a secondary oracle-K stress test only.",
    ]
    manifest["claim_boundaries"] = [
        (
            "The work supports fail-closed evidence governance and "
            "study-stratified same-mask comparison."
        ),
        "HER2ST uses a global default and CRC returns evidence_required under the frozen policies.",
        "The work does not establish superior personalised selection on unseen real studies.",
        "The fixed-split synthetic result establishes software construct validity only.",
        "Historical LOOCV results remain diagnostic and cannot be promoted to validation evidence.",
    ]
    outputs["submission_freeze_manifest.json"] = V3._json_text(manifest)
    return outputs


V3._expected_outputs = _expected_outputs


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args(argv)

    expected = _expected_outputs()
    FREEZE.mkdir(parents=True, exist_ok=True)
    if args.check:
        mismatches = [
            name
            for name, value in expected.items()
            if not (FREEZE / name).is_file()
            or (FREEZE / name).read_text(encoding="utf-8") != value
        ]
        if mismatches:
            logging.error("Submission freeze v4 mismatch: %s", ", ".join(mismatches))
            return 1
        logging.info("HistoWeave Bioinformatics submission freeze v4: VERIFIED")
        return 0

    for name, value in expected.items():
        (FREEZE / name).write_text(value, encoding="utf-8")
    logging.info("HistoWeave Bioinformatics submission freeze v4: FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
