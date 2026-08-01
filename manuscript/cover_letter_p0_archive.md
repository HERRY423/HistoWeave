# Cover letter -- HistoWeave submission to Bioinformatics

**To:** The Editor, *Bioinformatics* (Oxford Academic)

**From:** [Author 1 -- corresponding author], [Affiliation]

**Date:** [submission date]

**Re:** Original Paper submission -- "HistoWeave: evidence-governed method decisions with structured abstention for spatial transcriptomics"

Dear Editor,

We submit HistoWeave as an Original Paper for consideration by *Bioinformatics*. HistoWeave is an open-source decision protocol for determining which spatial-transcriptomics method set is supported by the available evidence and when a workflow must return a global default, request further evidence, or abstain. Its contribution is the executable coupling of task, ground-truth, oracle-K, metric, source-integrity, grouped-holdout, and Pareto-admissibility rules; it is not a new clustering algorithm.

The submission makes deliberately bounded claims:

- The five-slice DLPFC oracle-K track contains 20 method configurations. The separate five-dataset external oracle-K panel prespecified 15 methods, 13 of which produced finite ARI results; only BANKSY overlaps the full set of five DLPFC spatial-aware families across that external panel.
- External five-dataset LOOCV ties the training-fold global-best comparator (both mean regret 0.006) and therefore does not support superiority or personalised deployment.
- A prospectively specified in-repository Wu et al. breast-cancer stress test failed its locked 0.02-ARI regret margin (mean regret 0.1313; 95% bootstrap CI 0.0340--0.2363). The study was absent from audited training sources, but the protocol has no independent public timestamp and uses oracle K. We therefore do not call it a public preregistration or admissible validation for non-oracle personalisation.
- A study-grouped selective analysis (n=20) favours zero personalisation coverage and `global_default`; this is abstention from personalisation, distinct from the `abstain` action used when no task-valid evidence remains.
- An 11-case adversarial audit produced zero incompatible-evidence admissions and zero false rejections among the two valid controls.

These negative and boundary results are retained as first-class artefacts. The manuscript does not claim that a personalised policy transports to unseen studies, that the external panel is a full aligned SOTA comparison, or that spatial-region results establish performance on cell-type labels.

The P0 manuscript, method-coverage ledger, evidence-admission audit, validation source hashes, and freeze report are regenerated and SHA-256-locked by `submission_freeze_v2/reproduce_submission_freeze.py`. Existing v1 figure locks are referenced rather than silently rewritten. HistoWeave is distributed as `histoweave-spatial` on PyPI under BSD-3-Clause.

Before formal submission, the placeholder author list, affiliations, corresponding-author details, funding, acknowledgements, and the repository-to-Zenodo release metadata must be verified by the authors.

We confirm that the manuscript has not been published elsewhere and is not under consideration by another journal. All authors must approve the final submitted version.

Sincerely,

[Author 1 -- corresponding author]
[Affiliation]
[email] | [ORCID]

*Enclosures: `manuscript/main.tex`; `submission_freeze_v2/REPORT.md`; `submission_freeze_v2/submission_freeze_manifest.json`; `submission_freeze_v1/main_figures.lock.json`.*
