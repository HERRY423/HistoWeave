"""Register an untouched third study after meta-panel + policy freeze.

This script does not open expression matrices or labels. It writes a lock
receipt that must be posted publicly before any third-study outcome access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "results"

# Candidate: Maynard/LIBD DLPFC held as sequential external confirmation only
# after independence from the frozen v5 policy artefacts is documented.
THIRD_STUDY = {
    "study_id": "LIBD_DLPFC_SEQUENTIAL_CONFIRMATION",
    "paper_doi": "10.1038/s41593-020-00787-0",
    "technology": "10x Visium",
    "species": "human",
    "organ": "dorsolateral prefrontal cortex",
    "unit": "donor",
    "expected_units": 3,
    "donor_ids": ["Br5595", "Br8100", "Br5292"],
    "ground_truth": "manual laminar annotations from the source study",
    "k_policy": "estimate",
    "method_panel": [
        "spagcn",
        "stagate",
        "graphst",
        "bayesspace",
        "banksy",
        "spectral",
        "gaussian_mixture",
        "kmeans",
        "agglomerative",
    ],
    "independence_requirements": [
        "frozen v5 policy parameters must not have been fit on DLPFC outcomes",
        "DLPFC may not enter feature scaling, global-default selection, or gate calibration for the sequential confirmation fold",
        "if DLPFC was used in any prior descriptive landscape, report that limitation and prefer a fully external cohort when available",
    ],
    "forbidden_before_public_lock": [
        "re-using DLPFC ARI tables to choose thresholds",
        "opening pathologist/manual labels for policy tuning",
        "selective exclusion of difficult donors after seeing method rankings",
    ],
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meta-status", type=Path, default=OUT / "meta_panel_status.json")
    parser.add_argument("--policy-results", type=Path, default=OUT / "nested_policy_results.json")
    parser.add_argument("--louo-results", type=Path, default=OUT / "nested_louo_results.json")
    parser.add_argument("--output", type=Path, default=OUT / "third_study_registration.json")
    args = parser.parse_args()

    meta = json.loads(args.meta_status.read_text(encoding="utf-8"))
    policy = json.loads(args.policy_results.read_text(encoding="utf-8"))
    louo = (
        json.loads(args.louo_results.read_text(encoding="utf-8"))
        if args.louo_results.exists()
        else {}
    )
    if meta.get("status") != "complete":
        raise SystemExit("meta-panel is incomplete; refuse third-study registration")

    if louo.get("personalized_value_success") or louo.get("soft_positive"):
        # Freeze the LOUO-derived operating characteristics for sequential application.
        thresholds = [
            a.get("threshold")
            for a in louo.get("actions") or []
            if a.get("threshold") is not None
        ]
        globals_ = [
            a.get("training_global_method")
            for a in louo.get("actions") or []
            if a.get("training_global_method")
        ]
        frozen_policy = {
            "status": "policy_frozen_from_nested_louo",
            "source": {"kind": "nested_leave_one_unit_out"},
            "model": "1nn",
            "k": 1,
            "feature_subset": louo.get("feature_subset"),
            "threshold_median": float(sorted(thresholds)[len(thresholds) // 2])
            if thresholds
            else None,
            "threshold_set": sorted({float(t) for t in thresholds}),
            "global_method_mode": max(set(globals_), key=globals_.count) if globals_ else None,
            "personalized_value_success_on_source": louo.get("personalized_value_success"),
            "soft_positive_on_source": louo.get("soft_positive"),
            "source_evaluation": louo.get("evaluation"),
        }
    else:
        folds = list(policy.get("cross_study_folds") or policy.get("folds") or [])
        unit_split = policy.get("unit_fixed_split") or {}
        candidates: list[dict] = []
        for fold in folds:
            if fold.get("status") == "scored" and fold.get("chosen"):
                candidates.append({"kind": "cross_study", **fold})
        if unit_split.get("status") == "scored" and unit_split.get("chosen"):
            candidates.append({"kind": "unit_fixed_split", **unit_split})
        usable = [f for f in candidates if (f.get("chosen") or {}).get("threshold") is not None]
        if not usable:
            frozen_policy = {
                "status": "fail_closed_no_calibrated_personalisation",
                "action": "evidence_required_or_global_default",
                "note": "Third study remains informative for descriptive same-mask SOTA and fail-closed behaviour.",
            }
        else:
            usable.sort(
                key=lambda f: (
                    not f.get("personalized_value_success", False),
                    not f.get("soft_positive", False),
                    -float((f.get("evaluation") or {}).get("coverage") or 0.0),
                    float((f.get("evaluation") or {}).get("mean_regret_difference") or 0.0),
                )
            )
            chosen = usable[0]
            chosen_cfg = chosen.get("chosen") or {}
            frozen_policy = {
                "status": "policy_frozen_from_fixed_split",
                "source": {
                    "kind": chosen.get("kind"),
                    "train_study": chosen.get("train_study"),
                    "test_study": chosen.get("test_study"),
                    "mode": chosen.get("mode"),
                },
                "model": chosen_cfg.get("model"),
                "k": chosen_cfg.get("k"),
                "alpha": chosen_cfg.get("alpha"),
                "threshold": chosen_cfg.get("threshold"),
                "global_method": chosen.get("global_method"),
                "personalized_value_success_on_source": chosen.get(
                    "personalized_value_success"
                ),
                "soft_positive_on_source": chosen.get("soft_positive"),
            }

    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "schema_version": "histoweave.third_study_registration.v5",
        "protocol_id": "histoweave-positive-personalisation-2026-08",
        "registered_utc": now,
        "execution_permitted": False,
        "public_lock": {
            "required": True,
            "required_objects": [
                "commit containing this receipt on a public branch",
                "public GitHub issue citing protocol_id, receipt SHA-256, and meta-panel/policy hashes",
            ],
            "unlock_rule": "Both objects must be visible before any third-study labels or method ARI outcomes are used to update the policy.",
        },
        "third_study": THIRD_STUDY,
        "meta_panel_status_sha256": sha256_file(args.meta_status),
        "policy_results_sha256": sha256_file(args.policy_results),
        "louo_results_sha256": sha256_file(args.louo_results)
        if args.louo_results.exists()
        else None,
        "frozen_policy": frozen_policy,
        "claim_boundary": (
            "Registration opens a sequential confirmation study. It does not "
            "retroactively convert prior fixed-split evaluations into prospective seals."
        ),
    }
    body = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    receipt["receipt_sha256"] = sha256_text(body)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "registered_utc": now,
        "execution_permitted": False,
        "receipt_path": str(args.output),
        "receipt_sha256": receipt["receipt_sha256"],
        "frozen_policy_status": frozen_policy["status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
