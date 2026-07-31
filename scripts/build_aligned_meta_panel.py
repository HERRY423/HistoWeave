"""Assemble the aligned, grouped, non-oracle development meta-panel.

The v3 prospective-validation report states that a defensible positive
personalisation claim requires "an aligned, grouped, non-oracle development
meta-panel that validates the gate before another untouched study is opened."
This script defines that contract and measures how much of it is already
satisfied by in-repo evidence.

Aligned contract
----------------
- Task:            spatial_domain only
- Ground-truth:    spatial_domain (pathology/anatomical), never cluster_proxy
- Metric:          ARI, higher is better
- K policy:        estimate (non-oracle); every cell must declare k_policy=estimate
- Seeds:           [42, 1, 2]
- Method panel:    9 methods (the v3 aligned panel)
- Split unit:      study or donor (never slice-level LOOCV)

A cell (dataset x method) is *compliant* only if it has a row with an explicit
non-oracle K declaration. In-repo tables without a k_policy column are marked
k_policy_undeclared and are a backlog: they must be re-run under estimate-K
before they can enter the panel. The Wu 2021 cohort is excluded from this
panel because it is locked as an independent test set (prohibited from training
or threshold selection).

Outputs
-------
- meta_panel_alignment/meta_panel_manifest.json  (machine-readable)
- meta_panel_alignment/REPORT.md                  (readiness + backlog)

Usage:
    python scripts/build_aligned_meta_panel.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "meta_panel_alignment"

ALIGNED_METHODS = [
    "banksy",
    "spagcn",
    "graphst",
    "stagate",
    "bayesspace",
    "spectral",
    "kmeans",
    "gaussian_mixture",
    "agglomerative",
]
SEEDS = [42, 1, 2]
K_POLICY = "estimate"

# Development datasets that may enter the aligned panel. Donor-level collapse:
# DLPFC slices -> donors; external studies -> one unit each. Wu 2021 is excluded
# by lock (independent test set). Synthetic landscapes are excluded (not real).
META_PANEL_UNITS = [
    # DLPFC donors (Maynard 2021)
    "dlpfc_donor_Br5595",
    "dlpfc_donor_Br8100",
    "dlpfc_donor_Br5292",
    # External validation studies (benchmark_external_validation)
    "visium_hd_crc",
    "xenium_lung_cancer",
    "xenium_ovarian_cancer",
    "visium_mouse_brain",
    "allen_merfish_brain_section",
    # Cross-tissue / independent-unit studies already in dev
    "HER2ST",
    "10x_xenium_prime_lymph_node",
    "Gut2018_4i",
    "Hartmann2020_MIBI_TOF",
    "Jackson2020_IMC",
    "Lohoff2022_seqFISH_embryo",
    "Stickels2021_SlideSeqV2",
]

# Canonicalise raw evidence dataset labels to meta-panel units. DLPFC slices are
# collapsed to their donor (the split unit for grouped validation).
SLICE_TO_DONOR = {
    "151507": "dlpfc_donor_Br5595",
    "151508": "dlpfc_donor_Br5595",
    "151509": "dlpfc_donor_Br5595",
    "151510": "dlpfc_donor_Br5595",
    "151669": "dlpfc_donor_Br8100",
    "151670": "dlpfc_donor_Br8100",
    "151671": "dlpfc_donor_Br8100",
    "151672": "dlpfc_donor_Br8100",
    "151673": "dlpfc_donor_Br5292",
    "151674": "dlpfc_donor_Br5292",
    "151675": "dlpfc_donor_Br5292",
    "151676": "dlpfc_donor_Br5292",
}
# Aliases between raw labels in evidence tables and canonical unit names.
LABEL_ALIASES = {
    "xenium_human_lymph_node": "10x_xenium_prime_lymph_node",
    "lymph_node_xenium": "10x_xenium_prime_lymph_node",
    "dlpfc": "dlpfc_donor_Br5595",
    "slideseq": "Stickels2021_SlideSeqV2",
    "slideseq_puck_200115_08": "Stickels2021_SlideSeqV2",
}


def _canonical_unit(raw: str) -> str:
    raw = str(raw).strip()
    if raw in SLICE_TO_DONOR:
        return SLICE_TO_DONOR[raw]
    if raw in LABEL_ALIASES:
        return LABEL_ALIASES[raw]
    return raw


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_long_tables() -> list[dict]:
    """Load every benchmark_long.csv under the repo with its path."""
    rows: list[dict] = []
    for csv_path in sorted(ROOT.rglob("benchmark_long.csv")):
        if any(part.startswith(".") for part in csv_path.relative_to(ROOT).parts):
            continue
        try:
            with csv_path.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    row["_source"] = str(csv_path.relative_to(ROOT)).replace("\\", "/")
                    rows.append(row)
        except OSError:
            continue
    return rows


def _normalise_method(raw: str) -> str:
    method = str(raw).split("@")[0].strip().lower().replace("-", "_")
    # banksy_py is the aligned-panel banksy implementation used in-repo.
    if method == "banksy_py":
        return "banksy"
    return method


# Ground-truth kinds admissible for the spatial_domain task. proxy_* / cluster
# / cell_* labels are inadmissible even if a table declares a k_policy.
ADMISSIBLE_GT_TOKENS = ("domain", "region", "anatomy", "pathology")
INADMISSIBLE_GT_TOKENS = ("proxy", "leiden", "louvain", "cluster", "cell", "type", "class")


def _ground_truth_admissible(raw: str) -> bool:
    value = str(raw or "").strip().lower()
    if not value:
        return True  # undeclared GT cannot certify; handled as undeclared
    if any(tok in value for tok in INADMISSIBLE_GT_TOKENS):
        return False
    return any(tok in value for tok in ADMISSIBLE_GT_TOKENS) or value in {"spatial_domain"}


def main() -> int:
    rows = _load_long_tables()

    # Dataset column name differs across tables.
    def dataset_of(row: dict) -> str:
        for key in ("dataset", "sample"):
            if row.get(key):
                return str(row[key])
        return ""

    def k_policy_of(row: dict) -> str:
        kp = str(row.get("k_policy") or "").strip().lower()
        if kp in {"estimate", "estimated", "non_oracle"}:
            return "estimate"
        oracle_k = str(row.get("oracle_k") or "").strip().lower()
        if kp in {"oracle", "fixed_oracle", "dual"} or oracle_k in {"true", "1", "yes"}:
            return "oracle"
        return "undeclared"

    # Compliant cells: explicit non-oracle rows on an aligned method that also
    # pass the ground-truth and metric contract.
    compliant: dict[str, dict[str, set]] = {}  # unit -> method -> seeds
    undeclared: dict[str, dict[str, set]] = {}
    oracle: dict[str, dict[str, set]] = {}
    inadmissible: dict[str, dict[str, set]] = {}
    by_source: dict[str, int] = {}

    for row in rows:
        method = _normalise_method(str(row.get("method") or ""))
        if method not in ALIGNED_METHODS:
            continue
        unit = _canonical_unit(dataset_of(row))
        seed = str(row.get("seed") or "")
        kp = k_policy_of(row)

        # Ground-truth and metric contract (S3): a proxy/cluster/cell GT label or
        # a non-ARI metric is inadmissible even if a k_policy column exists.
        gt = str(row.get("ground_truth") or row.get("ground_truth_kind") or "")
        if not _ground_truth_admissible(gt):
            inadmissible.setdefault(unit, {}).setdefault(method, set()).add(seed)
            continue
        declared_metric = str(row.get("metric") or "").strip().lower()
        if declared_metric and declared_metric != "ari":
            inadmissible.setdefault(unit, {}).setdefault(method, set()).add(seed)
            continue
        if "score" in row and "ari" not in row:  # figure3 uses `score`, not ARI
            inadmissible.setdefault(unit, {}).setdefault(method, set()).add(seed)
            continue

        table = {"estimate": compliant, "undeclared": undeclared, "oracle": oracle}[kp]
        table.setdefault(unit, {}).setdefault(method, set()).add(seed)
        src = row["_source"]
        by_source[src] = by_source.get(src, 0) + 1

    # Coverage matrix over the aligned panel for the meta-panel units.
    # A cell is seed-complete only when all three declared seeds (42, 1, 2) have
    # explicit non-oracle evidence; anything less is partial.
    coverage: list[dict] = []
    total_cells = len(META_PANEL_UNITS) * len(ALIGNED_METHODS)
    compliant_cells = 0
    partial_cells = 0
    units_with_seed_complete: set[str] = set()
    units_with_any_evidence: set[str] = set()
    for unit in META_PANEL_UNITS:
        for method in ALIGNED_METHODS:
            seeds_est = sorted(compliant.get(unit, {}).setdefault(method, set()))
            seeds_und = sorted(undeclared.get(unit, {}).get(method, set()))
            seeds_oracle = sorted(oracle.get(unit, {}).get(method, set()))
            seeds_inadmissible = sorted(inadmissible.get(unit, {}).get(method, set()))
            seed_set = set(seeds_est)
            seed_complete = set(SEEDS) <= seed_set
            if seed_set:
                units_with_any_evidence.add(unit)
            if seed_complete:
                compliant_cells += 1
                units_with_seed_complete.add(unit)
            elif seed_set:
                partial_cells += 1
            coverage.append(
                {
                    "unit": unit,
                    "method": method,
                    "estimate_seeds": seeds_est,
                    "seed_complete": seed_complete,
                    "partial_seeds": sorted(seed_set),
                    "undeclared_seeds": seeds_und,
                    "oracle_seeds": seeds_oracle,
                    "inadmissible_seeds": seeds_inadmissible,
                }
            )

    compliance = compliant_cells / total_cells if total_cells else 0.0
    backlog = total_cells - compliant_cells

    manifest = {
        "protocol": "histoweave.aligned_meta_panel.v1",
        "contract": {
            "task": "spatial_domain",
            "ground_truth_kind": "spatial_domain",
            "metric": "ARI",
            "higher_is_better": True,
            "k_policy": K_POLICY,
            "oracle_k_allowed": False,
            "seeds": SEEDS,
            "method_panel": ALIGNED_METHODS,
            "split_unit": "study_or_donor",
            "excluded_locked_test_set": ["wu2021_breast"],
        },
        "units": META_PANEL_UNITS,
        "total_cells": total_cells,
        "seed_complete_cells": compliant_cells,
        "partial_seed_cells": partial_cells,
        "compliance_fraction": round(compliance, 4),
        "backlog_cells": backlog,
        "compliance_definition": "cell is seed-complete only when all three declared estimate-K seeds (42,1,2) have explicit non-oracle ARI evidence on admissible ground truth",
        "evidence_sources": {src: n for src, n in sorted(by_source.items())},
        "coverage": coverage,
        "source_hashes": {
            str(p.relative_to(ROOT)).replace("\\", "/"): _sha256(p)
            for p in ROOT.rglob("benchmark_long.csv")
            if not any(part.startswith(".") for part in p.relative_to(ROOT).parts)
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "meta_panel_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # Readiness report (restricted to the aligned meta-panel universe).
    units_with_evidence = sorted(
        set(META_PANEL_UNITS) & (set(compliant) | set(undeclared) | set(oracle) | set(inadmissible))
    )
    missing_units = sorted(set(META_PANEL_UNITS) - set(units_with_evidence))
    report = f"""# Aligned non-oracle development meta-panel — readiness

Protocol: `{manifest["protocol"]}`

## Contract

- Task `spatial_domain`; ground-truth kind `spatial_domain` (pathology/anatomical);
  proxy/cluster/cell-type GT is inadmissible.
- Metric ARI (higher is better); k_policy **estimate** (oracle-K never admissible).
- Seeds `{SEEDS}`; aligned 9-method panel; split unit **study_or_donor**.
- Locked test set excluded: `wu2021_breast` (independent test only).

## Coverage

- Total aligned cells (units x methods): **{total_cells}**
- Cells seed-complete under the contract (all of `{SEEDS}` on non-oracle ARI,
  admissible GT): **{compliant_cells}** ({compliance*100:.1f}%)
- Cells with only partial estimate-K evidence: **{partial_cells}**
- Backlog (must be re-run under estimate-K): **{backlog}**
- Units with any seed-complete non-oracle cell: {len(units_with_seed_complete)} / {len(META_PANEL_UNITS)}
- Units with evidence but no seed-complete non-oracle cell: {len(units_with_any_evidence) - len(units_with_seed_complete)}
- Units with no in-repo evidence at all: {len(missing_units)} ({", ".join(missing_units) or "none"})

## Interpretation

{_interpretation(compliance, len(META_PANEL_UNITS), total_cells)}

## Backlog semantics

Tables without a `k_policy` column cannot certify non-oracle K and are treated
as undeclared. Tables with proxy/cell-type ground truth or a non-ARI metric are
marked inadmissible even if a k_policy column exists. Cells must be re-run under
the estimate-K contract on admissible ground truth for all three seeds before
they enter the panel. See `meta_panel_manifest.json` for the full per-unit /
per-method seed coverage.
"""
    (OUT_DIR / "REPORT.md").write_text(report, encoding="utf-8")

    print(f"[meta-panel] aligned cells: {compliant_cells}/{total_cells} "
          f"({compliance*100:.1f}% compliant), backlog {backlog}")
    print(f"[meta-panel] units with seed-complete non-oracle cells: {len(units_with_seed_complete)}/{len(META_PANEL_UNITS)}")
    print(f"[meta-panel] wrote {OUT_DIR}")
    return 0


def _interpretation(compliance: float, n_units: int, total: int) -> str:
    if compliance == 0.0:
        return (
            "No aligned cell is seed-complete under the three-seed non-oracle "
            "contract. Any partial single-seed evidence is not sufficient for grouped "
            "study/donor-level validation. The meta-panel is a precise execution "
            "backlog: every method x dataset cell must be run under k_policy=estimate "
            "on all declared seeds before personalisation can be gated. Until then "
            "the fail-closed default stands."
        )
    if compliance < 0.5:
        return (
            f"Partial coverage ({compliance*100:.0f}%). Non-oracle personalisation "
            "cannot yet be validated on a grouped panel of at least five independent "
            "units; continue expanding the estimate-K grid."
        )
    if n_units < 5:
        return "High method coverage but too few independent units for grouped validation."
    return "The aligned meta-panel meets the grouped non-oracle validation bar for the covered units."


if __name__ == "__main__":
    sys.exit(main())
