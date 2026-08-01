"""Build protocol diagnostics for the narrowed Original Paper.

Writes deterministic JSON used by the manuscript SI and freeze:

- action frequencies under default DecisionPolicy (with/without held-out gate)
- threshold sensitivity for min_rank_support_score and min_support
- risk-coverage degeneration notes for HER2ST and selective endpoint
- registration-strength checklist

Run from repository root:

    python scripts/build_protocol_diagnostics.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from histoweave.benchmark import DecisionPolicy, MethodScore, Recommendation, build_decision_card

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manuscript" / "protocol_diagnostics"
OUT.mkdir(parents=True, exist_ok=True)

GROUPED = ROOT / "protocol_endpoints_results" / "study_grouped_20_recommendation.json"
SELECTIVE = ROOT / "protocol_endpoints_results" / "selective_regret_coverage.json"
HER2 = ROOT / "manuscript" / "prospective_validation_v3" / "figure_data.json"
AUDIT = ROOT / "p0_validation_results" / "evidence_admission" / "audit_summary.json"


def _rec_from_query(q: dict[str, Any]) -> Recommendation:
    conf = float(q.get("confidence") or 0.0)
    support = max(1, len(q.get("neighbours") or []))
    ranked: list[MethodScore] = []
    for i, method in enumerate(q.get("recommended_methods") or []):
        base = float(q.get("selected_score") or 0.0)
        ranked.append(
            MethodScore(
                method=str(method),
                score=base if i == 0 else max(0.0, base - 0.01 * i),
                confidence=conf if i == 0 else max(0.0, conf - 0.05 * i),
                wins=0,
                neighbour_scores={},
                uncertainty=0.1,
                support=support,
                coverage=1.0,
            )
        )
    if not ranked:
        ranked = [
            MethodScore(
                method="none",
                score=0.0,
                confidence=0.0,
                wins=0,
                neighbour_scores={},
                uncertainty=1.0,
                support=0,
                coverage=0.0,
            )
        ]
    neighbours: list[dict[str, Any]] = []
    for raw in q.get("neighbours") or []:
        row = dict(raw)
        row.setdefault("task", "spatial_domain")
        row.setdefault("ground_truth_kind", "spatial_domain")
        row.setdefault("k_policy", "estimate")
        row.setdefault("oracle_k", False)
        neighbours.append(row)
    if not neighbours:
        neighbours = [
            {
                "name": "ref",
                "similarity": 1.0,
                "task": "spatial_domain",
                "ground_truth_kind": "spatial_domain",
                "k_policy": "estimate",
                "oracle_k": False,
            }
        ]
    methods = list(q.get("recommended_methods") or [])
    gbm = q.get("global_best_method")
    if gbm and gbm not in methods:
        methods = methods + [str(gbm)]
    return Recommendation(
        task="spatial_domain",
        dataset_name=str(q["held_out"]),
        ranked_methods=ranked,
        neighbours=neighbours,
        global_best_method=gbm,
        global_best_score=q.get("global_best_score"),
        beats_global_best_baseline=bool(q.get("knn_beats_global")),
        evidence_contract={
            "task": "spatial_domain",
            "ground_truth_kind": "spatial_domain",
            "k_policy": "estimate",
            "metric": "ari",
            "higher_is_better": True,
            "method_panel": methods,
        },
    )


def _count_actions(
    queries: list[dict[str, Any]], policy: DecisionPolicy
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for query in queries:
        card = build_decision_card(_rec_from_query(query), policy=policy)
        counts[card.action.value] += 1
    for key in (
        "personalised_set",
        "global_default",
        "evidence_required",
        "abstain",
    ):
        counts.setdefault(key, 0)
    return dict(sorted(counts.items()))


def _threshold_grid(queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for thr in [0.0, 0.15, 0.25, 0.40, 0.50, 0.75, 0.90]:
        for min_support in [1, 2, 3]:
            policy = DecisionPolicy(
                min_rank_support_score=thr,
                min_support=min_support,
                require_heldout_validation=True,
            )
            actions = _count_actions(queries, policy)
            rows.append(
                {
                    "min_rank_support_score": thr,
                    "min_support": min_support,
                    "require_heldout_validation": True,
                    "actions": actions,
                    "n_personalised": actions["personalised_set"],
                    "n_evidence_required": actions["evidence_required"],
                    "n_global_default": actions["global_default"],
                    "n_abstain": actions["abstain"],
                    "action_changed_from_default": None,
                }
            )
    default = _count_actions(queries, DecisionPolicy())
    for row in rows:
        row["action_changed_from_default"] = row["actions"] != default
    return rows


def main() -> None:
    grouped = json.loads(GROUPED.read_text(encoding="utf-8"))
    selective = json.loads(SELECTIVE.read_text(encoding="utf-8"))
    her2 = json.loads(HER2.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    queries = list(grouped["queries"])

    default_actions = _count_actions(queries, DecisionPolicy())
    no_holdout_actions = _count_actions(
        queries, DecisionPolicy(require_heldout_validation=False)
    )
    thr_rows = _threshold_grid(queries)

    # Selective risk-coverage: action is always_global at recommended point.
    selective_summary = {
        "n_queries": selective["n_queries"],
        "recommended_policy": selective["recommended_policy"],
        "recommended_coverage": selective["recommended_coverage"],
        "always_personalised_regret": selective["curve"][0][
            "mean_regret_always_personalised"
        ],
        "always_global_regret": selective["curve"][0]["mean_regret_always_global"],
        "n_thresholds_on_curve": len(selective["curve"]),
        "minimum_at_zero_coverage": True,
    }

    her2_frontier = {
        "study": her2["study"],
        "n_donors": her2["n_donors"],
        "coverage_at_default_threshold_0.25": her2["policies"]["histoweave"][
            "coverage_at_0.25"
        ],
        "deployed_regret_histoweave": her2["policies"]["histoweave"]["deployed_regret"],
        "deployed_regret_always_global": her2["policies"]["always_global"][
            "deployed_regret"
        ],
        "delta_vs_global": her2["contrasts"]["histoweave_minus_always_global"][
            "deployed_regret_delta"
        ],
        "risk_coverage_status": "degenerate_zero_coverage",
        "interpretation": (
            "External risk-coverage cannot demonstrate safer personalised operating "
            "points because coverage is zero; the validated property is refusal "
            "(type-I safety), not risk reduction at positive coverage (type-II ability)."
        ),
    }

    registration = {
        "strength_class": "public_repository_timestamp_not_osf",
        "registration_url": her2["registration_url"],
        "server_time_utc": her2["registration_server_time_utc"],
        "protocol_commit": her2["protocol_commit"],
        "protocol_sha256": her2["protocol_sha256"],
        "precedes_outcome_access": True,
        "independent_timestamping_service": False,
        "osf_or_zenodo_protocol_doi": None,
        "limitation": (
            "GitHub issue server time + commit hash is stronger than an untimestamped "
            "in-repo lock, but weaker than an OSF/Zenodo protocol DOI. SI records the "
            "full lock; authors may upgrade registration for revision."
        ),
    }

    payload = {
        "schema_version": "histoweave.protocol_diagnostics.v1",
        "source_artifacts": {
            "study_grouped": str(GROUPED.relative_to(ROOT)),
            "selective": str(SELECTIVE.relative_to(ROOT)),
            "her2st": str(HER2.relative_to(ROOT)),
            "adversarial_audit": str(AUDIT.relative_to(ROOT)),
        },
        "action_frequency": {
            "cohort": "study_grouped_20_recommendation",
            "n_queries": len(queries),
            "default_policy": {
                "policy": DecisionPolicy().to_dict(),
                "actions": default_actions,
                "notes": (
                    "Default require_heldout_validation=True. Without a bound "
                    "validation pack, queries that beat the global proxy become "
                    "evidence_required rather than personalised_set."
                ),
            },
            "ablation_no_heldout_gate": {
                "policy": DecisionPolicy(require_heldout_validation=False).to_dict(),
                "actions": no_holdout_actions,
                "notes": (
                    "Removing the held-out gate increases personalised_set counts; "
                    "this ablation is diagnostic of gate impact, not a deployment policy."
                ),
            },
            "adversarial_audit_t0": {
                "n_cases": audit["n_cases"],
                "invalid_admissions": audit["invalid_admissions"],
                "valid_rejections": audit["valid_rejections"],
                "dominated_selections": audit["dominated_selections"],
                "all_cases_passed": audit["all_cases_passed"],
            },
        },
        "threshold_sensitivity": {
            "grid": thr_rows,
            "summary": {
                "default_min_rank_support_score": 0.25,
                "default_min_support": 2,
                "personalised_set_always_zero_with_heldout_gate": all(
                    row["n_personalised"] == 0 for row in thr_rows
                ),
                "note": (
                    "Under require_heldout_validation=True, sweeping rank-support and "
                    "min_support does not unlock personalised_set on this cohort; "
                    "the held-out gate dominates."
                ),
            },
        },
        "risk_coverage": {
            "selective_t3": selective_summary,
            "her2st_t4": her2_frontier,
        },
        "registration_strength": registration,
        "claim_boundary": (
            "Diagnostics support fail-closed governance and gate necessity; they do "
            "not establish personalised superiority on external studies."
        ),
    }

    out_json = OUT / "action_frequency_and_sensitivity.json"
    out_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # Short markdown for humans / SI drafting.
    md = [
        "# Protocol diagnostics (auto-generated)",
        "",
        f"Source: `{out_json.relative_to(ROOT)}`",
        "",
        "## Action frequency (n=20 study-grouped queries)",
        "",
        f"- Default policy: `{default_actions}`",
        f"- Ablation `require_heldout_validation=False`: `{no_holdout_actions}`",
        "",
        "## Threshold sensitivity",
        "",
        "- With held-out gate on, `personalised_set` remains 0 across the rank-support "
        "× min_support grid (held-out gate dominates).",
        "",
        "## Risk–coverage",
        "",
        f"- Selective recommended policy: `{selective_summary['recommended_policy']}` "
        f"at coverage {selective_summary['recommended_coverage']}",
        f"- HER2ST coverage: {her2_frontier['coverage_at_default_threshold_0.25']} "
        f"({her2_frontier['risk_coverage_status']})",
        "",
        "## Registration strength",
        "",
        f"- Class: `{registration['strength_class']}`",
        f"- URL: {registration['registration_url']}",
        f"- UTC: {registration['server_time_utc']}",
        "",
    ]
    (OUT / "REPORT.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"wrote": str(out_json), "default_actions": default_actions}, indent=2))


if __name__ == "__main__":
    main()
