"""Static and evidence-bound audit for the HistoWeave P1 manuscript."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pandas as pd
from PIL import Image

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
OUT = ROOT / "p1_validation_results"
OUT.mkdir(exist_ok=True)


def _without_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines())


def _plain_tex(text: str) -> str:
    text = _without_comments(text)
    text = re.sub(r"\\(?:url|href)\{[^{}]*\}(?:\{([^{}]*)\})?", r" \1 ", text)
    text = re.sub(r"\\(?:citep|citet|ref|label)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\begin\{[^{}]*\}|\\end\{[^{}]*\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"\\\([^)]*\\\)|\\\[[^\]]*\\\]", " ", text, flags=re.S)
    return re.sub(r"\s+", " ", text).strip()


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", _plain_tex(text))


def _extract(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main_tex = (MANUSCRIPT / "main.tex").read_text(encoding="utf-8")
    supp_tex = (MANUSCRIPT / "supplementary.tex").read_text(encoding="utf-8")
    abstract = _extract(main_tex, r"\begin{abstract}", r"\end{abstract}")
    body = _extract(main_tex, r"\section{Introduction}", r"\bibliographystyle")

    citation_keys = {
        key.strip()
        for group in re.findall(r"\\cite[tp]\{([^{}]+)\}", main_tex + "\n" + supp_tex)
        for key in group.split(",")
    }
    bibliography_keys = set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}", main_tex))
    labels = set(re.findall(r"\\label\{([^{}]+)\}", main_tex))
    refs = set(re.findall(r"\\ref\{([^{}]+)\}", main_tex))
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}", main_tex)
    figure_paths = [MANUSCRIPT / "figures" / name for name in figures]

    audit = json.loads(
        (ROOT / "p0_validation_results" / "evidence_admission" / "audit_summary.json").read_text()
    )
    wu = json.loads(
        (
            ROOT
            / "benchmark_external_validation"
            / "independent_test_wu2021"
            / "independent_test_summary.json"
        ).read_text()
    )
    selective = json.loads(
        (ROOT / "protocol_endpoints_results" / "selective_regret_coverage.json").read_text()
    )
    her2 = json.loads(
        (
            ROOT
            / "manuscript"
            / "prospective_validation_v3"
            / "figure_data.json"
        ).read_text(encoding="utf-8")
    )
    dlpfc = pd.read_csv(
        ROOT / "5x15_spatial_aware" / "performance_matrix_mean_full.csv", index_col=0
    )
    synthetic = json.loads(
        (ROOT / "synthetic_validation_v2" / "results" / "results.json").read_text(
            encoding="utf-8"
        )
    )
    crc = json.loads(
        (ROOT / "prospective_validation_v4" / "results" / "results_summary.json").read_text(
            encoding="utf-8"
        )
    )
    multistudy = json.loads(
        (ROOT / "multistudy_validation" / "same_mask_results.json").read_text(
            encoding="utf-8"
        )
    )

    her2_global = her2["policies"]["histoweave"]
    her2_contrast = her2["contrasts"]["histoweave_minus_always_global"]
    evidence_checks = {
        "audit_all_cases_passed": audit["all_cases_passed"] is True,
        "audit_zero_invalid_admissions": audit["invalid_admissions"] == 0,
        "audit_zero_false_rejections": audit["valid_rejections"] == 0,
        "audit_zero_dominated_selections": audit["dominated_selections"] == 0,
        "authoritative_manuscript_has_no_loocv_validation": not any(
            token in (main_tex + "\n" + supp_tex).lower()
            for token in ("loocv", "leave-one-out", "leave-one-dataset")
        ),
        "historical_external_landscape_is_descriptive_only": (
            "historical five-study oracle" in main_tex.lower()
            and "contributes no evidence" in main_tex.lower()
        ),
        "wu_negative": wu["success"] is False and wu["decision"] == "independent_test_fail",
        "wu_mean_matches_text": abs(wu["mean_frozen_policy_regret"] - 0.13126117338422785)
        < 1e-12,
        "selective_global_default": selective["recommended_policy"] == "always_global_default",
        "dlpfc_top_method_stagate": dlpfc.mean(axis=0).idxmax() == "stagate",
        "her2st_zero_personalisation_coverage": her2_global["coverage_at_0.25"] == 0.0,
        "her2st_action_is_global_default": her2_global["action"] == "global_default",
        "her2st_matches_always_global_by_identity": her2_contrast["deployed_regret_delta"]
        == 0.0,
        "her2st_locked_global_is_spagcn": her2["locked_global_default"] == "spagcn",
        "her2st_n_donors_seven": her2["n_donors"] == 7,
        "crc_strict_nine_method_patients_seven": crc["n_strict_nine_method_patients"]
        == 7,
        "crc_policy_fail_closed": crc["policy_endpoint_status"] == "evidence_required",
        "crc_all_methods_available_seven_patients": set(
            crc["method_patient_availability"].values()
        )
        == {7},
        "crc_runtime_skips_disclosed": crc["runtime_skip_failures"] == 15
        and crc["prediction_failures"] == 17,
        "multistudy_same_mask_complete": multistudy["multistudy_complete"] is True
        and [study["n_strict_nine_method_units"] for study in multistudy["studies"]]
        == [6, 7],
        "synthetic_v22_success": synthetic["success"] is True,
        "synthetic_v22_signal_coverage": abs(
            synthetic["signal_test"]["coverage"] - 0.45
        )
        < 1e-12,
        "synthetic_v22_signal_superiority": synthetic["signal_test"][
            "bootstrap_95_interval_regret_difference"
        ][1]
        < 0.0,
        "synthetic_v22_null_safe": synthetic["null_test"]["coverage"] == 0.0
        and synthetic["null_test"]["mean_regret_difference"] == 0.0,
        "synthetic_negative_runs_retained": (
            ROOT / "synthetic_validation_v2" / "results" / "INVALID_RUN_v2_0.md"
        ).is_file()
        and (
            ROOT / "synthetic_validation_v2" / "results" / "FAILED_RUN_v2_1.md"
        ).is_file(),
    }

    diagnostics_path = (
        ROOT / "manuscript" / "protocol_diagnostics" / "action_frequency_and_sensitivity.json"
    )
    if diagnostics_path.is_file():
        diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
        default_actions = diagnostics["action_frequency"]["default_policy"]["actions"]
        evidence_checks.update(
            {
                "diagnostics_evidence_required_modal": default_actions.get(
                    "evidence_required", 0
                )
                >= default_actions.get("global_default", 0),
                "diagnostics_no_personalised_under_default": default_actions.get(
                    "personalised_set", 0
                )
                == 0,
                "diagnostics_her2_risk_coverage_degenerate": diagnostics["risk_coverage"][
                    "her2st_t4"
                ]["risk_coverage_status"]
                == "degenerate_zero_coverage",
            }
        )

    figure_audit: dict[str, dict[str, object]] = {}
    for path in figure_paths:
        image = Image.open(path)
        dpi = tuple(round(float(v), 1) for v in image.info.get("dpi", (0, 0)))
        figure_audit[path.name] = {
            "exists": path.exists(),
            "width": image.width,
            "height": image.height,
            "dpi": dpi,
            "passes_350_dpi": min(dpi) >= 349.0,
        }

    abstract_word_count = len(_words(abstract))
    body_word_count = len(_words(body))
    result = {
        "schema_version": "histoweave.manuscript_audit.v1",
        "article_type": "Bioinformatics Original Paper",
        "checked_on": "2026-08-01",
        "abstract_word_count_including_headings_and_urls": abstract_word_count,
        "abstract_within_recommended_150_words": abstract_word_count <= 150,
        "main_body_word_count_excluding_references": body_word_count,
        "main_body_within_5000_words": body_word_count <= 5000,
        "structured_abstract_headings": {
            heading: heading in abstract
            for heading in (
                "Motivation:",
                "Results:",
                "Availability and Implementation:",
                "Contact:",
                "Supplementary information:",
            )
        },
        "citation_keys": sorted(citation_keys),
        "bibliography_keys": sorted(bibliography_keys),
        "missing_bibliography_keys": sorted(citation_keys - bibliography_keys),
        "uncited_bibliography_keys": sorted(bibliography_keys - citation_keys),
        "missing_labels": sorted(refs - labels),
        "unreferenced_labels": sorted(labels - refs),
        "figures": figure_audit,
        "all_figure_files_exist": all(path.exists() for path in figure_paths),
        "all_figures_at_least_350_dpi": all(
            bool(row["passes_350_dpi"]) for row in figure_audit.values()
        ),
        "author_required_placeholders": main_tex.count(r"\required{"),
        "evidence_checks": evidence_checks,
        "all_evidence_checks_passed": all(evidence_checks.values()),
        "latex_engine_available": False,
        "latex_compile_status": "not_run_no_engine_available",
        "submission_status": "editorial_draft_complete_author_and_policy_actions_required",
    }
    required_boolean_checks = [
        result["abstract_within_recommended_150_words"],
        result["main_body_within_5000_words"],
        all(result["structured_abstract_headings"].values()),
        not result["missing_bibliography_keys"],
        not result["missing_labels"],
        result["all_figure_files_exist"],
        result["all_figures_at_least_350_dpi"],
        result["all_evidence_checks_passed"],
    ]
    result["static_audit_passed"] = all(required_boolean_checks)

    (OUT / "submission_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# HistoWeave P1 submission audit",
        "",
        f"- Static audit passed: **{result['static_audit_passed']}**",
        f"- Abstract words: **{abstract_word_count} / 150 recommended**",
        f"- Main-body words: **{body_word_count} / 5,000**",
        f"- Main figures: **{len(figure_audit)}**, all at least 350 dpi: "
        f"**{result['all_figures_at_least_350_dpi']}**",
        f"- Missing citation keys: **{len(result['missing_bibliography_keys'])}**",
        f"- Evidence assertions passed: **{result['all_evidence_checks_passed']}**",
        f"- Author-required placeholders: **{result['author_required_placeholders']}**",
        "- LaTeX compilation: **not run; no TeX engine is installed locally**",
        "- Submission status: **author metadata and Bioinformatics AI-policy action required**",
        "",
    ]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    LOGGER.info("%s", json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
