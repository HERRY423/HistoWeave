"""Create or verify the HistoWeave Bioinformatics P1 submission freeze.

The freeze locks the canonical manuscript, supplementary material, cover
letter, deterministic artwork, journal-compliance record, manuscript audit,
and the P0 evidence artifacts on which the paper's numerical claims depend.
It deliberately records unresolved author and journal-policy actions rather
than representing the package as immediately uploadable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "submission_freeze_v3"
SCHEMA = "histoweave.submission_freeze.v3"
FREEZE_DATE = "2026-07-31"

# Fast freeze-critical suite (always run). Full-suite summary is optional via env.
# Do not include tests/test_submission_freeze_v3.py here: it invokes --check and
# would race with writing the freeze outputs.
FREEZE_CRITICAL_TESTS = (
    "tests/test_evidence_audit.py",
    "tests/test_decision.py",
    "tests/test_recommend.py",
    "tests/test_install_smoke.py",
)

MANUSCRIPT_PATHS = (
    "manuscript/main.tex",
    "manuscript/supplementary.tex",
    "manuscript/cover_letter.md",
    "manuscript/README.md",
    "manuscript/SUBMISSION_COMPLIANCE.md",
    "manuscript/AUTHOR_METADATA_REQUIRED.md",
    "manuscript/make_submission_assets.py",
    "manuscript/audit_submission.py",
)

FIGURE_PATHS = tuple(
    f"manuscript/figures/{stem}.{extension}"
    for stem in (
        "figure1_workflow",
        "figure2_dlpfc_oracle_k",
        "figure3_external_panel",
        "figure4_validation",
        "graphical_abstract",
    )
    for extension in ("png", "svg", "tif")
)

AUDIT_PATHS = (
    "p1_validation_results/submission_audit.json",
    "p1_validation_results/REPORT.md",
    "p1_validation_results/TEST_REPORT.md",
)

EVIDENCE_PATHS = (
    "submission_freeze_v2/submission_freeze_manifest.json",
    "submission_freeze_v2/REPORT.md",
    "p0_validation_results/evidence_admission/audit_summary.json",
    "benchmark_external_validation/decision_validation.json",
    "benchmark_external_validation/independent_test_wu2021/independent_test_summary.json",
    "protocol_endpoints_results/selective_regret_coverage.json",
    "non_oracle_k_sota/summary.json",
    "5x15_spatial_aware/performance_matrix_mean_full.csv",
    "benchmark_external_validation/performance_matrix_mean.csv",
    "prospective_validation_v2/protocol.json",
    "manuscript/prospective_validation_v3/figure_data.json",
    "manuscript/prospective_validation_v3/REPORT.md",
    "manuscript/prospective_validation_v3/SUBMISSION_ASSESSMENT.md",
    "manuscript/protocol_diagnostics/action_frequency_and_sensitivity.json",
    "manuscript/protocol_diagnostics/REPORT.md",
    "scripts/build_protocol_diagnostics.py",
    "tests/test_install_smoke.py",
)

IMPLEMENTATION_PATHS = (
    "submission_freeze_v3/reproduce_submission_freeze.py",
    "tests/test_submission_freeze_v3.py",
    ".zenodo.json",
    "CITATION.cff",
)

SOURCE_PATHS = MANUSCRIPT_PATHS + FIGURE_PATHS + AUDIT_PATHS + EVIDENCE_PATHS + IMPLEMENTATION_PATHS


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _generated_record(text: str) -> dict[str, Any]:
    raw = text.encode("utf-8")
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _parse_pytest_summary(text: str) -> dict[str, int]:
    """Parse the final pytest short summary line."""
    counts = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "xfailed": 0}
    # e.g. "12 passed, 1 skipped in 2.34s"
    for key in counts:
        match = re.search(rf"(\d+)\s+{key}", text)
        if match:
            counts[key] = int(match.group(1))
    return counts


def _stable_pytest_summary_line(counts: dict[str, int]) -> str:
    """Deterministic summary without wall-clock duration (required for freeze hashes)."""
    parts = []
    for key in ("passed", "failed", "skipped", "errors", "xfailed"):
        n = int(counts.get(key, 0))
        if n or key in {"passed", "failed", "skipped"}:
            parts.append(f"{n} {key}")
    return ", ".join(parts)


def _run_pytest(paths: tuple[str, ...], *, timeout_s: int = 300) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=no", *paths]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_s,
    )
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    counts = _parse_pytest_summary(combined)
    return {
        "paths": list(paths),
        "returncode": proc.returncode,
        "summary_line": _stable_pytest_summary_line(counts),
        **counts,
        "ok": proc.returncode == 0 and counts["failed"] == 0 and counts["errors"] == 0,
    }


def _regression_report() -> dict[str, Any]:
    critical = _run_pytest(FREEZE_CRITICAL_TESTS, timeout_s=180)
    # Optional full suite: set HISTOWEAVE_FREEZE_FULL_PYTEST=1 (slow).
    import os

    full: dict[str, Any] | None = None
    if os.environ.get("HISTOWEAVE_FREEZE_FULL_PYTEST", "").strip() in {"1", "true", "yes"}:
        full = _run_pytest(("tests",), timeout_s=3600)
    return {
        "critical": critical,
        "full_suite": full,
        "note": (
            "critical suite always runs at freeze time; "
            "set HISTOWEAVE_FREEZE_FULL_PYTEST=1 for full tests/"
        ),
    }


def _validate_inputs() -> dict[str, Any]:
    missing = [relative for relative in SOURCE_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError("Missing frozen source artifacts: " + ", ".join(missing))

    audit = _read_json(ROOT / "p1_validation_results" / "submission_audit.json")
    if audit.get("schema_version") != "histoweave.manuscript_audit.v1":
        raise RuntimeError("Unexpected P1 manuscript-audit schema")
    if not audit.get("static_audit_passed"):
        raise RuntimeError("P1 static manuscript audit did not pass")
    if not audit.get("all_evidence_checks_passed"):
        raise RuntimeError("P1 evidence assertions did not pass")
    if not audit.get("abstract_within_recommended_150_words"):
        raise RuntimeError("Structured abstract exceeds the recommended 150 words")
    if not audit.get("main_body_within_5000_words"):
        raise RuntimeError("Main manuscript exceeds the 5,000-word target")
    if not audit.get("all_figures_at_least_350_dpi"):
        raise RuntimeError("One or more raster figures are below 350 dpi")
    if audit.get("missing_bibliography_keys") or audit.get("missing_labels"):
        raise RuntimeError("P1 manuscript has unresolved citation or reference keys")

    p0 = _read_json(ROOT / "submission_freeze_v2" / "submission_freeze_manifest.json")
    if p0.get("schema_version") != "histoweave.submission_freeze.v2":
        raise RuntimeError("Unexpected P0 freeze schema")
    p0_audit = p0["validation"]["evidence_admission_audit"]
    if not p0_audit.get("all_cases_passed"):
        raise RuntimeError("P0 adversarial evidence audit is not passing")

    prospective = _read_json(ROOT / "prospective_validation_v2" / "protocol.json")
    if prospective["registration_gate"]["execution_permitted"] is not False:
        raise RuntimeError("Prospective execution gate drifted from the paper's claim boundary")

    return audit


def _inventory_text() -> str:
    upload_files = (
        ("Main manuscript", "manuscript/main.tex"),
        ("Supplementary material", "manuscript/supplementary.tex"),
        ("Cover letter", "manuscript/cover_letter.md"),
        ("Figure 1", "manuscript/figures/figure1_workflow.tif"),
        ("Figure 2", "manuscript/figures/figure2_dlpfc_oracle_k.tif"),
        ("Figure 3", "manuscript/figures/figure3_external_panel.tif"),
        ("Figure 4", "manuscript/figures/figure4_validation.tif"),
        ("Graphical abstract", "manuscript/figures/graphical_abstract.tif"),
    )
    rows = "\n".join(f"| {label} | `{path}` |" for label, path in upload_files)
    return (
        "# Bioinformatics P1 submission-file inventory\n\n"
        "These are the intended upload files after all author-only and AI-policy "
        "actions in `manuscript/SUBMISSION_COMPLIANCE.md` are resolved.\n\n"
        "| Submission item | Repository source |\n"
        "|---|---|\n"
        f"{rows}\n\n"
        "PNG and SVG counterparts are frozen for review and reproducibility. "
        "The canonical LaTeX sources must be compiled once in the current official "
        "OUP/Overleaf environment before upload.\n"
    )


def _report_text(audit: dict[str, Any], regression: dict[str, Any]) -> str:
    critical = regression["critical"]
    crit_line = (
        f"{critical['passed']} passed, {critical['skipped']} skipped, "
        f"{critical['failed']} failed"
    )
    full = regression.get("full_suite")
    if full:
        full_line = (
            f"{full['passed']} passed, {full['skipped']} skipped, "
            f"{full['failed']} failed"
        )
    else:
        full_line = (
            "not re-run at freeze (set HISTOWEAVE_FREEZE_FULL_PYTEST=1); "
            "critical suite recorded below"
        )
    return (
        "# HistoWeave Bioinformatics P1 submission freeze v3\n\n"
        "The scientific narrative, evidence boundaries, supplementary material, "
        "cover letter, references, and deterministic artwork are frozen at editorial "
        "review quality. The package is not represented as immediately uploadable.\n\n"
        f"- Freeze date: {FREEZE_DATE}\n"
        f"- Structured abstract: {audit['abstract_word_count_including_headings_and_urls']} "
        "words (recommended maximum 150)\n"
        f"- Main body: {audit['main_body_word_count_excluding_references']} "
        "words (target maximum 5,000)\n"
        "- Main figures: 4; Fig.4 includes HER2ST primary external panels; "
        "all PNG review copies are at least 350 dpi\n"
        f"- Citation-key gaps: {len(audit['missing_bibliography_keys'])}\n"
        f"- Evidence assertions passed: {audit['all_evidence_checks_passed']}\n"
        f"- Author-required placeholders: {audit['author_required_placeholders']}\n"
        "- LaTeX compile: not run because no TeX engine is installed locally\n"
        f"- Freeze-critical pytest: {crit_line} "
        f"({'ok' if critical['ok'] else 'FAILED'})\n"
        f"- Full repository regression: {full_line}\n"
        "- Canonical narrative: `manuscript/main.tex` + "
        "`manuscript/supplementary.tex` (Markdown drafts deprecated)\n"
        "- Zenodo concept DOI: https://doi.org/10.5281/zenodo.21586217 "
        "(re-deposit after freeze changes)\n\n"
        "Blocking actions before journal upload:\n\n"
        "1. Human authors must resolve Bioinformatics AI-policy compliance, "
        "substantively verify/rewrite the text as required, and make an accurate disclosure.\n"
        "2. Authors must supply names, affiliations, ORCID, corresponding-author details, "
        "CRediT roles, funding, acknowledgements, and conflicts.\n"
        "3. Compile and visually inspect the sources in the current official OUP template.\n"
        "4. Publish a Zenodo version whose notes match this freeze date and "
        "HER2ST `figure_data.json` hash.\n\n"
        "Scientific risks remain explicit: HER2ST personalisation coverage is zero "
        "(fail-closed global default; not personalised superiority), LOOCV is "
        "editorially vulnerable and diagnostic-only, the diagnostic external panel is "
        "not a complete aligned SOTA comparison, and Wu remains a secondary oracle-K "
        "stress test only.\n\n"
        "Run `python submission_freeze_v3/reproduce_submission_freeze.py --check` "
        "to verify the complete locked package.\n"
    )


def _expected_outputs() -> dict[str, str]:
    audit = _validate_inputs()
    regression = _regression_report()
    if not regression["critical"]["ok"]:
        raise RuntimeError(
            "Freeze-critical pytest failed: " + regression["critical"]["summary_line"]
        )
    inventory = _inventory_text()
    report = _report_text(audit, regression)
    source_records = {relative: _record(ROOT / relative) for relative in SOURCE_PATHS}
    her2 = _read_json(
        ROOT / "manuscript" / "prospective_validation_v3" / "figure_data.json"
    )
    manifest = {
        "schema_version": SCHEMA,
        "freeze_date": FREEZE_DATE,
        "article_type": "Bioinformatics Original Paper",
        "status": "p1_editorial_draft_complete_submission_blocked",
        "canonical_narrative": {
            "main": "manuscript/main.tex",
            "supplement": "manuscript/supplementary.tex",
            "deprecated_markdown_drafts": [
                "manuscript/HistoWeave_manuscript (1).md",
            ],
        },
        "source_artifacts": source_records,
        "generated_artifacts": {
            "submission_freeze_v3/REPORT.md": _generated_record(report),
            "submission_freeze_v3/SUBMISSION_FILE_INVENTORY.md": _generated_record(inventory),
        },
        "validation": {
            "static_audit_passed": audit["static_audit_passed"],
            "abstract_words": audit["abstract_word_count_including_headings_and_urls"],
            "main_body_words": audit["main_body_word_count_excluding_references"],
            "main_figures": len(audit["figures"]),
            "all_figures_at_least_350_dpi": audit["all_figures_at_least_350_dpi"],
            "missing_bibliography_keys": audit["missing_bibliography_keys"],
            "missing_labels": audit["missing_labels"],
            "evidence_assertions": audit["evidence_checks"],
            "latex_compile_status": audit["latex_compile_status"],
            "author_required_placeholders": audit["author_required_placeholders"],
            "regression": regression,
        },
        "her2st_primary_external": {
            "study": her2.get("study"),
            "n_donors": her2.get("n_donors"),
            "coverage_at_0.25": her2["policies"]["histoweave"]["coverage_at_0.25"],
            "action": her2["policies"]["histoweave"]["action"],
            "claim_boundary": her2.get("claim_boundary"),
            "figure_data": "manuscript/prospective_validation_v3/figure_data.json",
            "registration_url": her2.get("registration_url"),
        },
        "zenodo": {
            "concept_doi": "10.5281/zenodo.21586217",
            "metadata_files": [".zenodo.json", "CITATION.cff"],
            "sync_required_after_freeze": True,
            "notes": (
                "Re-deposit a version whose description matches freeze_date and "
                "lists evidence-governance Original Paper package + HER2ST figure_data."
            ),
        },
        "submission_blockers": [
            "Bioinformatics AI-policy compliance and accurate disclosure require author action.",
            "Author identity, affiliation, ORCID, CRediT, funding, and conflict "
            "metadata are missing.",
            "The manuscript requires compilation and visual inspection in the "
            "current OUP environment.",
            "Zenodo version notes must be re-synced after this freeze before citing "
            "the archive as submission-identical.",
        ],
        "scientific_risks": [
            "HER2ST primary external validation has zero personalisation coverage; "
            "action identity with always-global is not selection advantage.",
            "No independent non-oracle validation supports personalised method selection.",
            "The Wu stress test is secondary, small, oracle-K, and not independently timestamped.",
            "The grouped five-dataset LOOCV result is diagnostic-only and editorially vulnerable.",
            "The diagnostic external panel is not a complete aligned SOTA comparison.",
        ],
        "claim_boundaries": [
            "The work supports a fail-closed evidence-governance protocol and global default.",
            "HER2ST shows correct refusal of personalisation under missing development gates.",
            "The work does not establish superior personalised selection on unseen studies.",
            "Oracle-K spatial-region evidence is not represented as non-oracle "
            "or cell-type evidence.",
            "The ISUS score is not represented as a reliable predictor of method gain.",
        ],
        "official_guidance": {
            "author_guidelines": "https://academic.oup.com/bioinformatics/pages/author-guidelines",
            "submission_preparation": "https://academic.oup.com/bioinformatics/pages/submission_online",
            "checked_on": FREEZE_DATE,
        },
    }
    return {
        "REPORT.md": report,
        "SUBMISSION_FILE_INVENTORY.md": inventory,
        "submission_freeze_manifest.json": _json_text(manifest),
    }


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
            for name, text in expected.items()
            if not (FREEZE / name).is_file()
            or (FREEZE / name).read_text(encoding="utf-8") != text
        ]
        if mismatches:
            LOGGER.error("P1 freeze mismatch: %s", ", ".join(mismatches))
            return 1
        LOGGER.info("HistoWeave Bioinformatics P1 submission freeze v3: VERIFIED")
        return 0

    for name, text in expected.items():
        (FREEZE / name).write_text(text, encoding="utf-8")
    LOGGER.info("HistoWeave Bioinformatics P1 submission freeze v3: FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
