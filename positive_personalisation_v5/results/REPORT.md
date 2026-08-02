# Positive personalisation v5 — evidence report

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
| Studies | 2 (HER2ST, CRC_V4) |
| Strict nine-method units | 13 |
| Min units per method | 13 |
| Contract | spatial_domain / ARI / k_policy=estimate / seeds 42,1,2 |

Same-mask units:

- HER2ST donors: A, B, D, E, F, H
- CRC patients: A120838, A121573, A416371, A551763, A595688, A798015, A938797

## 2. Primary endpoint (nested LOUO)

| Metric | Value |
|---|---:|
| Coverage | 0.385 (5/13) |
| Mean deployed regret | 0.0428 |
| Mean always-global regret | 0.0543 |
| Mean regret difference | **-0.0115** |
| 95% bootstrap CI | [-0.0215, -0.0029] |
| personalized_value_success | **True** |

Personalised units (method ≠ training-fold global):

- `HER2ST:E`: spagcn (global was banksy, pred_gain=0.098, thr=0.08)
- `CRC_V4:A120838`: spagcn (global was banksy, pred_gain=0.098, thr=0.08)
- `CRC_V4:A121573`: kmeans (global was banksy, pred_gain=0.104, thr=0.1)
- `CRC_V4:A595688`: spagcn (global was banksy, pred_gain=0.098, thr=0.08)
- `CRC_V4:A938797`: kmeans (global was banksy, pred_gain=0.104, thr=0.08)


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
- Study candidate: `LIBD_DLPFC_SEQUENTIAL_CONFIRMATION`
- `execution_permitted`: **False**
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
