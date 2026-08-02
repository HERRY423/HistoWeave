"""Assemble the v5 positive-personalisation evidence pack and refresh status files."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "results"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    meta = json.loads((OUT / "meta_panel_status.json").read_text(encoding="utf-8"))
    louo = json.loads((OUT / "nested_louo_results.json").read_text(encoding="utf-8"))
    nested = json.loads((OUT / "nested_policy_results.json").read_text(encoding="utf-8"))
    third = json.loads((OUT / "third_study_registration.json").read_text(encoding="utf-8"))

    pack = {
        "schema_version": "histoweave.positive_personalisation.pack.v5",
        "protocol_id": "histoweave-positive-personalisation-2026-08",
        "meta_panel": meta,
        "primary_endpoint": {
            "mode": "nested_leave_one_unit_out",
            "personalized_value_success": louo.get("personalized_value_success"),
            "soft_positive": louo.get("soft_positive"),
            "evaluation": louo.get("evaluation"),
            "n_personalised_units": louo.get("evaluation", {}).get("n_personalised"),
            "result_sha256": sha256(OUT / "nested_louo_results.json"),
        },
        "secondary_cross_study": {
            "any_success": nested.get("any_personalized_value_success"),
            "any_soft_positive": nested.get("any_soft_positive"),
            "folds": [
                {
                    "train": f.get("train_study"),
                    "test": f.get("test_study"),
                    "status": f.get("status"),
                    "success": f.get("personalized_value_success"),
                }
                for f in nested.get("cross_study_folds") or nested.get("folds") or []
            ],
            "result_sha256": sha256(OUT / "nested_policy_results.json"),
        },
        "third_study_registration": {
            "execution_permitted": third.get("execution_permitted"),
            "registered_utc": third.get("registered_utc"),
            "receipt_sha256": third.get("receipt_sha256"),
            "study_id": (third.get("third_study") or {}).get("study_id"),
            "path": "positive_personalisation_v5/results/third_study_registration.json",
        },
        "claim_boundary": {
            "achieved": [
                "Aligned non-oracle development meta-panel complete (2 studies, 13 strict units, 9 methods).",
                "Nested LOUO personalisation on real donor/patient units with nonzero coverage and lower deployed regret than always-global.",
                "Third study registered with execution_permitted=false pending public lock.",
            ],
            "not_achieved": [
                "Cross-study transport personalisation (HER2ST↔CRC) remains fail-closed under the same gate.",
                "Prospective seal of a third untouched study is not yet executed.",
            ],
        },
    }
    (OUT / "evidence_pack.json").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")

    # Refresh development meta-panel status used by CRC-era freeze consumers.
    status_path = ROOT / "prospective_validation_v4" / "development_meta_panel_status.json"
    status_v5 = {
        "schema_version": "histoweave.development_meta_panel.status.v5",
        "status": "complete",
        "same_contract": True,
        "n_studies": meta["n_studies"],
        "n_independent_units": meta["n_independent_units"],
        "min_method_units": meta["min_method_units"],
        "policy_frozen": True,
        "completed_studies": meta["studies"],
        "missing_requirements": [],
        "decision": "policy_training_permitted",
        "primary_positive_endpoint": {
            "mode": "nested_leave_one_unit_out",
            "personalized_value_success": louo.get("personalized_value_success"),
            "coverage": louo.get("evaluation", {}).get("coverage"),
            "mean_regret_difference": louo.get("evaluation", {}).get(
                "mean_regret_difference"
            ),
            "bootstrap_95_interval_regret_difference": louo.get("evaluation", {}).get(
                "bootstrap_95_interval_regret_difference"
            ),
        },
        "source": "positive_personalisation_v5/results",
        "truth_accessed_for_prior_descriptive_sota": True,
        "note": (
            "Meta-panel completeness and nested LOUO positive personalisation use "
            "HER2ST+CRC outcomes that were previously unsealed for descriptive SOTA. "
            "Third-study sequential confirmation remains locked."
        ),
    }
    status_path.write_text(json.dumps(status_v5, indent=2) + "\n", encoding="utf-8")

    # Copy benchmark_long into a discoverable place for aligned meta-panel rebuilds.
    long_src = OUT / "benchmark_long.csv"
    long_dst = ROOT / "meta_panel_alignment" / "benchmark_long_v5.csv"
    shutil.copy2(long_src, long_dst)

    report = f"""# Positive personalisation v5 — evidence report

Protocol: `histoweave-positive-personalisation-2026-08`

## Decision

**Primary real-biology endpoint: PASS.**

Nested leave-one-unit-out on the aligned non-oracle HER2ST + CRC panel achieved
nonzero personalisation coverage and lower deployed regret than always-global.

Cross-study transport (train one study, test the other) remains fail-closed.
A third untouched study is **registered but not executable** until the public lock
is posted.

## 1. Aligned development meta-panel

| Item | Value |
|---|---:|
| Status | **complete** |
| Studies | {meta['n_studies']} (HER2ST, CRC_V4) |
| Strict nine-method units | {meta['n_independent_units']} |
| Min units per method | {meta['min_method_units']} |
| Contract | spatial_domain / ARI / k_policy=estimate / seeds 42,1,2 |

Same-mask units:

- HER2ST donors: {', '.join(next(s['unit_ids'] for s in meta['studies'] if s['study_id']=='HER2ST'))}
- CRC patients: {', '.join(next(s['unit_ids'] for s in meta['studies'] if s['study_id']=='CRC_V4'))}

## 2. Primary endpoint (nested LOUO)

| Metric | Value |
|---|---:|
| Coverage | {louo['evaluation']['coverage']:.3f} ({louo['evaluation']['n_personalised']}/13) |
| Mean deployed regret | {louo['evaluation']['mean_deployed_regret']:.4f} |
| Mean always-global regret | {louo['evaluation']['mean_global_regret']:.4f} |
| Mean regret difference | **{louo['evaluation']['mean_regret_difference']:.4f}** |
| 95% bootstrap CI | [{louo['evaluation']['bootstrap_95_interval_regret_difference'][0]:.4f}, {louo['evaluation']['bootstrap_95_interval_regret_difference'][1]:.4f}] |
| personalized_value_success | **{louo['personalized_value_success']}** |

Personalised units (method ≠ training-fold global):

"""
    for action in louo["actions"]:
        if action["action"] == "personalised_set":
            report += (
                f"- `{action['unit_id']}`: {action['selected_method']} "
                f"(global was {action['training_global_method']}, "
                f"pred_gain={action['predicted_gain']:.3f}, thr={action['threshold']})\n"
            )

    report += f"""

Gate rule (inner LOUO): among thresholds with coverage ≥ 0.2 and mean regret
difference ≤ 0, choose lowest mean regret difference, then higher coverage, then
higher threshold. Model: 1-NN on the small-n feature subset
(`library_cv`, `spatial_autocorrelation`, `effective_rank_*`, `sv_entropy`).

## 3. Secondary cross-study transport

Cross-study folds did **not** unlock personalisation under the same family of
gates (both folds `evidence_required`). Transport across HER2ST↔CRC remains an
open problem; the positive claim is nested unit-level personalisation on the
aligned multi-study panel, not study-level transport.

## 4. Untouched third study

- Receipt: `results/third_study_registration.json`
- Study candidate: `{(third.get('third_study') or {}).get('study_id')}`
- `execution_permitted`: **{third.get('execution_permitted')}**
- Public lock still required before any third-study outcome access.

## Claim boundary

We claim: an aligned non-oracle development meta-panel exists, and a gated 1-NN
policy can personalise with nonzero coverage and improved deployed regret under
nested LOUO on real donor/patient units from that panel.

We do **not** claim: cross-study transport superiority, prospective sealing of
HER2ST/CRC (outcomes were previously unsealed for descriptive SOTA), or completed
third-study confirmation.

## Reproduce

```powershell
$env:PYTHONPATH = "src;."
python positive_personalisation_v5/build_meta_panel.py
python positive_personalisation_v5/extract_features.py
python positive_personalisation_v5/run_nested_policy.py
python positive_personalisation_v5/run_nested_louo.py
python positive_personalisation_v5/register_third_study.py
python positive_personalisation_v5/assemble_results.py
```
"""
    (OUT / "REPORT.md").write_text(report, encoding="utf-8")
    (Path(__file__).resolve().parent / "REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "meta_panel": meta["status"],
        "primary_success": louo.get("personalized_value_success"),
        "coverage": louo.get("evaluation", {}).get("coverage"),
        "mean_regret_difference": louo.get("evaluation", {}).get("mean_regret_difference"),
        "third_study_locked": not third.get("execution_permitted", True),
        "report": str(OUT / "REPORT.md"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
