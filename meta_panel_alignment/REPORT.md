# Aligned non-oracle development meta-panel — readiness

Protocol: `histoweave.aligned_meta_panel.v1`

## Contract

- Task `spatial_domain`; ground-truth kind `spatial_domain` (pathology/anatomical);
  proxy/cluster/cell-type GT is inadmissible.
- Metric ARI (higher is better); k_policy **estimate** (oracle-K never admissible).
- Seeds `[42, 1, 2]`; aligned 9-method panel; split unit **study_or_donor**.
- Locked test set excluded: `wu2021_breast` (independent test only).

## Coverage

- Total aligned cells (units x methods): **135**
- Cells seed-complete under the contract (all of `[42, 1, 2]` on non-oracle ARI,
  admissible GT): **0** (0.0%)
- Cells with only partial estimate-K evidence: **6**
- Backlog (must be re-run under estimate-K): **135**
- Units with any seed-complete non-oracle cell: 0 / 15
- Units with evidence but no seed-complete non-oracle cell: 3
- Units with no in-repo evidence at all: 7 (10x_xenium_prime_lymph_node, Gut2018_4i, HER2ST, Hartmann2020_MIBI_TOF, Jackson2020_IMC, Lohoff2022_seqFISH_embryo, Stickels2021_SlideSeqV2)

## Interpretation

No aligned cell is seed-complete under the three-seed non-oracle contract. Any partial single-seed evidence is not sufficient for grouped study/donor-level validation. The meta-panel is a precise execution backlog: every method x dataset cell must be run under k_policy=estimate on all declared seeds before personalisation can be gated. Until then the fail-closed default stands.

## Backlog semantics

Tables without a `k_policy` column cannot certify non-oracle K and are treated
as undeclared. Tables with proxy/cell-type ground truth or a non-ARI metric are
marked inadmissible even if a k_policy column exists. Cells must be re-run under
the estimate-K contract on admissible ground truth for all three seeds before
they enter the panel. See `meta_panel_manifest.json` for the full per-unit /
per-method seed coverage.
