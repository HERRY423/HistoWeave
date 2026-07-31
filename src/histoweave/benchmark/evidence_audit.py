"""Adversarial, paper-level audit of HistoWeave evidence admission."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .decision import (
    DecisionAction,
    VerifiedEvidence,
    build_decision_card,
    load_decision_evidence,
)
from .recommend import MethodScore, Recommendation

PROTOCOL = "histoweave.evidence_admission_audit.v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _base_recommendation() -> Recommendation:
    ranked = [
        MethodScore(
            method="local@sw0.8",
            score=0.82,
            confidence=0.80,
            wins=2,
            neighbour_scores={"ref_a": 0.84, "ref_b": 0.80},
            uncertainty=0.02,
            support=2,
            coverage=1.0,
            base_method="local",
            spatial_context_policy="sw0.8",
        ),
        MethodScore(
            method="global",
            score=0.79,
            confidence=0.75,
            wins=0,
            neighbour_scores={"ref_a": 0.78, "ref_b": 0.80},
            uncertainty=0.01,
            support=2,
            coverage=1.0,
            base_method="global",
        ),
    ]
    return Recommendation(
        task="spatial_domain",
        dataset_name="audit_query",
        ranked_methods=ranked,
        neighbours=[
            {
                "name": "ref_a",
                "similarity": 0.9,
                "task": "spatial_domain",
                "ground_truth_kind": "spatial_domain",
                "k_policy": "estimate",
                "oracle_k": False,
            },
            {
                "name": "ref_b",
                "similarity": 0.8,
                "task": "spatial_domain",
                "ground_truth_kind": "spatial_domain",
                "k_policy": "estimate",
                "oracle_k": False,
            },
        ],
        global_best_method="global",
        global_best_score=0.79,
        beats_global_best_baseline=True,
        selection_regret_vs_global_best=-0.03,
        evidence_contract={
            "task": "spatial_domain",
            "metric": "ARI",
            "higher_is_better": True,
            "ground_truth_kinds": ["spatial_domain"],
            "k_policies": ["estimate"],
            "method_panel": ["global", "local@sw0.8"],
        },
    )


def _pareto(*, dominated_local: bool = False) -> dict[str, Any]:
    frontier = ["global"] if dominated_local else ["local@sw0.8", "global"]
    ranks = {"local@sw0.8": 1 if dominated_local else 0, "global": 0}
    return {
        "dataset": "audit_query",
        "frontier": frontier,
        "ranks": ranks,
        "directions": {"accuracy": "max", "seconds": "min"},
        "table": {
            "local@sw0.8": {"accuracy": 0.75 if dominated_local else 0.82, "seconds": 4.0},
            "global": {"accuracy": 0.79, "seconds": 2.0},
        },
    }


def _validation_payload(source_hash: str) -> dict[str, Any]:
    return {
        "schema_version": "histoweave.validation_evidence.v2",
        "protocol": "study_grouped_holdout",
        "task": "spatial_domain",
        "ground_truth_kind": "spatial_domain",
        "k_policy": "estimate",
        "metric": "ARI",
        "higher_is_better": True,
        "method_panel": ["global", "local@sw0.8"],
        "split_unit": "study",
        "training_exclusion_verified": True,
        "n_queries": 12,
        "beats_global_best": True,
        "source_artifacts": [{"path": "validation_source.json", "sha256": source_hash}],
    }


def _write_validation(
    output_dir: Path,
    name: str,
    source_hash: str,
    **updates: Any,
) -> VerifiedEvidence:
    payload = _validation_payload(source_hash)
    payload.update(updates)
    path = output_dir / f"validation_{name}.json"
    _write_json(path, payload)
    return load_decision_evidence(path)


def run_evidence_admission_audit(output_dir: str | Path) -> dict[str, Any]:
    """Run the frozen adversarial corpus and write a hash-locked result bundle."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    source = out / "validation_source.json"
    _write_json(
        source,
        {
            "protocol": "synthetic_adversarial_validation_source.v1",
            "n_queries": 12,
            "mean_personalised_regret": 0.01,
            "mean_global_regret": 0.03,
        },
    )
    source_hash = _sha256(source)
    valid_validation = _write_validation(out, "valid", source_hash)

    cases: list[dict[str, Any]] = []

    def evaluate(
        case_id: str,
        recommendation: Recommendation,
        validation: dict[str, Any] | None,
        *,
        expected_personalised: bool,
        dominated_local: bool = False,
    ) -> None:
        card = build_decision_card(
            recommendation,
            pareto=_pareto(dominated_local=dominated_local),
            validation=validation,
        )
        personalised = card.action is DecisionAction.PERSONALISED_SET
        cases.append(
            {
                "case_id": case_id,
                "expected_personalised": expected_personalised,
                "observed_action": card.action.value,
                "personalised": personalised,
                "passed": personalised is expected_personalised,
                "primary_set": card.primary_set,
                "checks": [check.to_dict() for check in card.checks],
                "dominated_local": dominated_local,
                "dominated_selected": dominated_local and "local@sw0.8" in card.primary_set,
            }
        )

    valid = _base_recommendation()
    evaluate("valid_bound_evidence", valid, valid_validation, expected_personalised=True)

    cross_task = copy.deepcopy(valid)
    for neighbour in cross_task.neighbours:
        neighbour["task"] = "cell_type"
    evaluate("cross_task_reference", cross_task, valid_validation, expected_personalised=False)

    proxy_truth = copy.deepcopy(valid)
    for neighbour in proxy_truth.neighbours:
        neighbour["ground_truth_kind"] = "cluster_proxy"
    evaluate(
        "cluster_proxy_ground_truth", proxy_truth, valid_validation, expected_personalised=False
    )

    missing_k = copy.deepcopy(valid)
    for neighbour in missing_k.neighbours:
        neighbour.pop("k_policy", None)
    evaluate("missing_k_policy", missing_k, valid_validation, expected_personalised=False)

    oracle_k = copy.deepcopy(valid)
    for neighbour in oracle_k.neighbours:
        neighbour["k_policy"] = "oracle"
        neighbour["oracle_k"] = True
    evaluate("oracle_k_reference", oracle_k, valid_validation, expected_personalised=False)

    missing_metric = copy.deepcopy(valid)
    missing_metric.evidence_contract.pop("metric", None)
    evaluate(
        "missing_metric_contract", missing_metric, valid_validation, expected_personalised=False
    )

    evaluate(
        "unverified_validation_json",
        valid,
        dict(valid_validation),
        expected_personalised=False,
    )
    task_mismatch = _write_validation(out, "task_mismatch", source_hash, task="cell_type")
    evaluate("validation_task_mismatch", valid, task_mismatch, expected_personalised=False)

    panel_mismatch = _write_validation(
        out,
        "panel_mismatch",
        source_hash,
        method_panel=["global"],
    )
    evaluate("validation_panel_mismatch", valid, panel_mismatch, expected_personalised=False)

    validation_oracle = _write_validation(
        out,
        "oracle_k",
        source_hash,
        k_policy="oracle",
    )
    evaluate("validation_oracle_k", valid, validation_oracle, expected_personalised=False)

    evaluate(
        "valid_dominated_candidate",
        valid,
        valid_validation,
        expected_personalised=True,
        dominated_local=True,
    )

    invalid = [row for row in cases if not row["expected_personalised"]]
    valid_rows = [row for row in cases if row["expected_personalised"]]
    dominated = [row for row in cases if row["dominated_local"]]

    def _rate(numerator: int, denominator: int) -> float | None:
        return numerator / denominator if denominator else None

    summary = {
        "protocol": PROTOCOL,
        "n_cases": len(cases),
        "invalid_cases": len(invalid),
        "invalid_admissions": sum(bool(row["personalised"]) for row in invalid),
        "incompatible_evidence_admission_rate": _rate(
            sum(bool(row["personalised"]) for row in invalid), len(invalid)
        ),
        "valid_cases": len(valid_rows),
        "valid_rejections": sum(not bool(row["personalised"]) for row in valid_rows),
        "valid_evidence_false_rejection_rate": _rate(
            sum(not bool(row["personalised"]) for row in valid_rows), len(valid_rows)
        ),
        "dominated_opportunities": len(dominated),
        "dominated_selections": sum(bool(row["dominated_selected"]) for row in dominated),
        "dominated_selection_rate": _rate(
            sum(bool(row["dominated_selected"]) for row in dominated), len(dominated)
        ),
        "all_cases_passed": all(bool(row["passed"]) for row in cases),
    }
    _write_json(out / "adversarial_corpus_results.json", {"cases": cases})
    _write_json(out / "audit_summary.json", summary)

    report = f"""# P0 evidence-admission audit

Protocol: `{PROTOCOL}`

- Adversarial cases: **{summary["invalid_cases"]}**
- Incompatible-evidence admission rate: **{summary["incompatible_evidence_admission_rate"]:.3f}**
- Valid-evidence false-rejection rate: **{summary["valid_evidence_false_rejection_rate"]:.3f}**
- Dominated-selection rate: **{summary["dominated_selection_rate"]:.3f}**
- All predeclared cases passed: **{summary["all_cases_passed"]}**

The corpus exercises the complete `build_decision_card` path. It includes
cross-task references, cluster-proxy ground truth, missing and oracle K policies,
missing metric declarations, unverified validation JSON, and validation bindings
with mismatched task, method panel, or K policy. The dominated-choice case uses
a matched Pareto table in which the locally ranked candidate is strictly dominated.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")

    artifacts = [
        path for path in sorted(out.iterdir()) if path.is_file() and path.name != "manifest.json"
    ]
    manifest = {
        "protocol": PROTOCOL,
        "artifacts": {
            path.name: {"bytes": path.stat().st_size, "sha256": _sha256(path)} for path in artifacts
        },
    }
    _write_json(out / "manifest.json", manifest)
    return summary
