# Aligned non-oracle development meta-panel — readiness

Protocol: `histoweave.aligned_meta_panel.v1` + **v5 sequential completion**

## Contract

- Task `spatial_domain`; ground-truth kind `spatial_domain` (pathology/anatomical);
  proxy/cluster/cell-type GT is inadmissible.
- Metric ARI (higher is better); k_policy **estimate** (oracle-K never admissible).
- Seeds `[42, 1, 2]`; aligned 9-method panel; split unit **study_or_donor**.
- Locked test set excluded: `wu2021_breast` (independent test only).

## v5 completed core panel (policy-training permitted)

Source: `positive_personalisation_v5/results/meta_panel_status.json` and
`positive_personalisation_v5/results/benchmark_long.csv`.

| Item | Value |
|---|---:|
| Status | **complete** |
| Studies | 2 (HER2ST, CRC_V4) |
| Strict nine-method units | **13** |
| Min units per method | **13** |
| Same contract | yes (estimate-K, ARI, 9 methods) |

These 13 units come from the registered non-oracle same-mask matrices already
scored under seeds `[42,1,2]`. They satisfy the minimum for gated policy training
(≥2 studies, ≥12 units, every method on ≥10 units).

Primary personalisation endpoint on this panel (nested LOUO): see
`positive_personalisation_v5/REPORT.md`.

## Historical 15-unit landscape scan (still incomplete)

The original 15-unit × 9-method = 135-cell scan over DLPFC donors + external
assays remains largely incomplete as a *broad* landscape:

- Total aligned cells (units x methods): **135**
- Cells seed-complete under the contract outside the v5 HER2ST/CRC bank: still
  sparse (legacy tables often lack `k_policy`)
- Broad backlog remains for DLPFC re-runs and multi-platform estimate-K cells

## Interpretation

**Policy training is no longer blocked.** The v5 HER2ST+CRC same-mask bank is a
complete aligned non-oracle development meta-panel for the nine-method contract.
Broader multi-platform estimate-K coverage is still desirable but is not required
to gate the nested LOUO positive endpoint or to register a third sequential study.

## Backlog semantics

Tables without a `k_policy` column cannot certify non-oracle K and are treated
as undeclared. Tables with proxy/cell-type ground truth or a non-ARI metric are
marked inadmissible even if a k_policy column exists. Cells must be re-run under
the estimate-K contract on admissible ground truth for all three seeds before
they enter the *broad* panel. See `meta_panel_manifest.json` for the historical
scan and `positive_personalisation_v5/results/` for the completed v5 bank.
