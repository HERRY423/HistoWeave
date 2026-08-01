# Targeted literature update: 2025–2026

Search date: 2026-07-28. Scope: spatial-transcriptomics clustering benchmarks,
algorithm selection/meta-learning, selective prediction, and abstention.
Primary papers and official repositories were preferred. Search terms combined
`spatial transcriptomics clustering benchmark 2025 2026`, `algorithm selection
meta-learning dataset characteristics 2025`, `selective prediction abstention
2025 2026`, and the names of candidate papers. This was a targeted update, not a
PRISMA systematic review.

## Spatial clustering benchmarks

Chen et al. (2025) evaluated 14 spatial clustering methods on approximately 600
real and simulated datasets across ten technologies and eight organs. Their
results emphasize method-specific preferences, data characteristics, spatial
patterns, preprocessing, and biological replicates rather than a universal
winner. Their official recommendation table is scenario-specific. For 10x
Visium breast tissue it lists stLearn, PRECAST, and BayesSpace; it does not
define a complete recommendation rule for the exact HER2ST donor-level setting
or for the complete HistoWeave candidate panel. HistoWeave therefore treats the
published recommendation as out-of-scope/ambiguous and falls back rather than
silently extrapolating it.

Pentimalli et al. (2025 preprint) benchmarked multi-slice spatial clustering
using simulation and real datasets. It is relevant because it moves evaluation
away from isolated sections toward slide/study structure, but a preprint alone
does not validate HistoWeave's selector.

STCC (2025) combines multiple spatial clustering outputs by consensus. Its
reported gains motivate ensemble baselines, while its setting is distinct from
pre-execution algorithm selection: consensus observes candidate outputs,
whereas HistoWeave must select or abstain without outcome labels.

## Algorithm selection and meta-learning

Jiang and Teney (ICML 2025) formulate OOD algorithm selection as multi-label
prediction from dataset characteristics and evaluate ranking on unseen shifts
and datasets. This supports the general feasibility of dataset-level
meta-selection, but also highlights the required evidence HistoWeave currently
lacks: a sufficiently diverse training collection of datasets, aligned
candidate methods, and genuinely unseen dataset-level evaluation.

## Selective prediction and abstention

Casacuberta and Kanade (NeurIPS 2025) study selective classifiers that may
abstain at a cost and extend guarantees to global and intersecting-group
coverage. The distinction between risk conditional on action and coverage is
directly relevant to HistoWeave; reporting only accuracy on accepted cases is
insufficient.

Yu and Blanchard (COLT 2026) study distribution-free sequential prediction with
abstentions under contaminated streams and derive error–abstention trade-offs.
This provides modern theoretical context, but its online adversarial setting is
not evidence for HistoWeave's offline spatial-clustering claims.

Lopez, Shamout, and Rudner (CHIL 2026) show empirically that uncertainty-based
selective prediction can worsen performance under class-dependent
miscalibration, despite good aggregate metrics. This is an especially important
caution: HistoWeave must validate risk–coverage externally and cannot infer
safety from a confidence score alone.

## Claim implications

The literature supports positioning HistoWeave as a fail-closed research
protocol for dataset-level method selection, not as a demonstrated universal
personalized selector. A defensible claim requires:

1. a donor/study-level split with no outcome access before predictions freeze;
2. the same non-oracle K estimator and preprocessing contract for every method;
3. risk–coverage curves against an always-global action;
4. direct comparison with applicable published recommendation rules, with
explicit fallback for undefined scenarios; and
5. a positive scenario showing nonzero coverage without using the independent
test outcomes to tune the gate.

## References

- Chen R, et al. *A comprehensive benchmarking for spatially resolved
  transcriptomics clustering methods across variable technologies, organs, and
  replicates.* iMeta. 2025;4:e70084. doi:10.1002/imt2.70084.
- Pentimalli TM, et al. *A comprehensive benchmark of multi-slice spatial
  clustering methods.* bioRxiv. 2025. doi:10.1101/2025.01.19.633631.
- *STCC: a robust spatial transcriptomics clustering method based on
  consensus clustering.* Genome Research. 2025.
  doi:10.1101/gr.280031.124.
- Jiang L, Teney D. *OOD-Chameleon: Is Algorithm Selection for OOD
  Generalization Learnable?* ICML. 2025;PMLR 267:27624–27648.
- Casacuberta S, Kanade V. *Selective Omniprediction and Fair Abstention.*
  NeurIPS. 2025.
- Yu J, Blanchard M. *Distribution-Free Sequential Prediction with
  Abstentions.* COLT. 2026;PMLR 336:6976–7011.
- Lopez LJL, Shamout FE, Rudner TGJ. *An Empirical Analysis of Calibration and
  Selective Prediction in Multimodal Clinical Condition Classification.* CHIL.
  2026;PMLR 333:794–833.

