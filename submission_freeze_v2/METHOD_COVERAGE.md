# P0 method and evidence coverage ledger

Panels are not pooled when task, K policy, method coverage, or split unit differs.

| Panel | Units/cases | Methods/configurations | K policy | Source |
|---|---:|---:|---|---|
| `dlpfc_oracle_5x20` | 5 | 20 | oracle | `5x15_spatial_aware/performance_matrix_mean_full.csv` |
| `external_oracle_5x15` | 5 | 15 prespecified / 13 fully finite | oracle | `benchmark_external_validation/benchmark_long.csv` |
| `strict_task_stratified_v2` | 9 | 7 | oracle_derived_source_landscape | `benchmark_external_validation/strict_external_panel_v2/loocv_summary.json` |
| `dlpfc_dual_k_sota` | 5 | 2 | oracle_and_three_estimated_tracks | `non_oracle_k_sota/summary.json` |
| `p0_adversarial_evidence_admission` | 11 | -- | -- | `p0_validation_results/evidence_admission/audit_summary.json` |

The five-dataset external panel is not a full aligned SOTA comparison: SpaGCN, STAGATE, GraphST, and BayesSpace are missing; only BANKSY overlaps. All external results are spatial-region, oracle-K evidence and cannot establish cell-type performance or unlock non-oracle personalisation.
