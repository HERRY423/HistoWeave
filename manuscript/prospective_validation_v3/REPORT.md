# HistoWeave prospective validation v3

## Outcome

This is a prospective, non-oracle external-study validation. The public
registration preceded access to HER2ST outcome-bearing files; predictions and
the existing-rule actions were frozen and hashed before a separate scorer
opened pathologist labels. The primary unit is the donor.

- Registration: https://github.com/HERRY423/HistoWeave/issues/19
- GitHub server time: `2026-07-29T05:34:31Z`
- Protocol commit: `a1ea59e2a8e305f86ef3bb3c118721786868fc60`
- Protocol SHA-256: `2fe030ddd11656bfd43a9f399bd1a82e361bc8b881a51c31fd7550a629c0c7dc`
- Study: HER2ST (paper DOI 10.1038/s41467-021-26271-2; data DOI
  10.5281/zenodo.5511762)
- Evaluable donors: 7 (A, B, C, D, E, F, H)
- Method/seed cells: 184 successful and
  5 retained failures
- Nine-method availability gate: PASS

## Aligned external panel

Every method received the same retained spots, raw-count starting data, three
seeds, and the same label-free estimated K. True K, histology, and pathologist
labels were unavailable during fitting. Official backend failures were not
silently substituted.

| method | donors | mean donor ARI | SD |
|---|---:|---:|---:|
| banksy | 7 | 0.2149 | 0.1226 |
| stagate | 7 | 0.1770 | 0.1085 |
| graphst | 7 | 0.1747 | 0.0991 |
| kmeans | 7 | 0.1529 | 0.1077 |
| gaussian_mixture | 6 | 0.1516 | 0.1428 |
| agglomerative | 7 | 0.1451 | 0.1378 |
| spagcn | 7 | 0.1337 | 0.0964 |
| spectral | 7 | 0.1190 | 0.1360 |
| bayesspace | 7 | 0.1115 | 0.1471 |

These scores concern agreement with source-study pathologist regions. Seven
donors cannot establish a universal ranking.

## Direct decision-protocol comparison

Registration-time development evidence selected SpaGCN as the global default
(donor-weighted non-oracle development ARI 0.2287 versus 0.2142 for STAGATE).
Before truth unsealing, the existing ungated 3-NN rule selected
`gaussian_mixture@sw0.8` on all seven samples. The 2025 SRTBenchmark
recommendation was undefined for the exact legacy-ST breast
biological-replicate scenario and therefore used the registered global
fallback. HistoWeave's grouped full-panel validation gate was unavailable, so
it also used the global fallback at every threshold.

- HistoWeave coverage at threshold 0.25: 0/7.
- Existing kNN coverage: 6/6 available donors; donor C was excluded from this pairwise contrast because all three GaussianMixture seeds failed.
- Always-global deployed regret: 0.1247 (95% donor
  bootstrap CI 0.0647 to
  0.1827).
- Existing-kNN deployed regret: 0.1190 (95% CI
  0.0237 to
  0.2311).
- HistoWeave minus existing-kNN deployed regret:
  0.0002 (95% CI
  -0.0893 to
  0.0922).
- HistoWeave minus always-global regret: 0.0000 (95% CI
  0.0000 to
  0.0000).

The primary 0.02 non-inferiority endpoint passes only because the actions are
identical; superiority does not pass. HistoWeave never reaches the ungated
rule's 100% coverage, so the prespecified matched-or-higher-coverage contrast is
NA. This validates fail-closed behavior, not personalised superiority.

## Positive reliable-signal scenario

In the separately locked synthetic construct-validity test, an independent
target-free feature truly switched the better method. At threshold 0.25 the
protocol selected non-global STAGATE on 23/60 test units (coverage
0.3833). Deployed regret was
0.0362 versus
0.1215 for always-global, a difference of
-0.0853 (95% CI -0.1294 to
-0.0415). The implementation is therefore not hard-coded to refuse.

The locked compound success flag remains `false`: observed coverage was below
0.50, and the predicate also required spectral (the global method) among
covered units even though coverage was defined as choosing a non-global action.
The malformed criterion was not repaired.

## Limitations and submission consequence

- G2 was excluded under the locked one-to-one rule because label coordinates
  were duplicated; no repair was performed.
- Five Gaussian-mixture cells failed and were retained without imputation.
- Initial dependency and BANKSY compatibility failures were retained; fixes
  changed interface arguments only.
- This is one external study with seven evaluable donors.
- The personalised-selection claim remains `evidence_required`. A defensible
  positive claim needs an aligned, grouped, non-oracle development meta-panel
  that validates the gate before another untouched study is opened.

The paper is materially stronger as a fail-closed protocol paper, but the data
do not support claiming validated personalised superiority. See
`deviations.md`, `LITERATURE_UPDATE_2025_2026.md`, `policy_actions.csv`,
`risk_coverage.csv`, and `bootstrap_intervals.json`.
