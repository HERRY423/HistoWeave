# Cover letter draft — HistoWeave Original Paper

**To:** The Editors, *Bioinformatics*  
**From:** [CORRESPONDING AUTHOR, AFFILIATION]  
**Date:** [SUBMISSION DATE]

Dear Editors,

We submit “HistoWeave: evidence-governed method decisions with structured abstention for spatial transcriptomics” for consideration as an Original Paper in the Gene expression category.

HistoWeave addresses a practical computational-biology problem that is not solved by another clustering algorithm: how to decide which benchmark evidence can support a method choice for a declared spatial-analysis task, and when the system must retain a global comparator, request further evidence, or abstain. Its main contribution is an executable evidence contract that binds task and ground-truth semantics, cluster-count policy, metric direction, method coverage, grouped holdout design, source hashes, and matched Pareto trade-offs to a versioned decision card.

The evaluation uses real spatial-transcriptomics data and deliberately preserves negative results. An 11-case adversarial audit admitted no incompatible evidence. In an oracle-\(K\) five-dataset external panel, leave-one-dataset-out candidate selection tied rather than beat the training-fold global comparator (mean regret 0.0059 for both). Across 20 grouped queries, the minimum selective regret occurred at zero personalisation coverage. A separately locked six-section breast-cancer stress test failed its 0.02-ARI regret margin (mean regret 0.1313; 95% bootstrap CI 0.0340–0.2363). The manuscript therefore does not claim validated non-oracle personalisation or superiority over an aligned state-of-the-art panel.

We recognize the journal’s machine-learning policy concerning leave-one-out validation. The five-dataset analysis is retained only as a diagnostic test of whether the evidence gate detects a failure to beat the global comparator; it is not the independent performance claim. The manuscript separates development, grouped selective evaluation, and the one-shot external stress test in a dedicated Methods subsection. We also state that the stress test uses oracle \(K\), comes from one study, and cannot unlock the non-oracle action. If this bounded diagnostic use is nevertheless considered outside the journal’s policy, we welcome editorial guidance.

The software, documentation, test data, unit and adversarial tests, figure-generation code, and SHA-256-locked submission artefacts are freely available under BSD-3-Clause at <https://github.com/HERRY423/Histoweave> and archived at <https://doi.org/10.5281/zenodo.21586217>. Public source datasets are cited with persistent identifiers; raw data are not redistributed.

**Mandatory author completion before this letter can be submitted:** This working draft received OpenAI Codex assistance. Current *Bioinformatics* guidance permits disclosed limited assistance but states that drafting papers from prompts is unacceptable. The human authors must substantively rewrite and verify the manuscript and describe only the final permitted use, or obtain written guidance from the Editorial Office. Replace this paragraph with an accurate, policy-compliant disclosure only after that action is complete.

The authors confirm that the final work is original, is not under consideration elsewhere, and has been approved by every listed author. [DISCLOSE ANY RELATED PREPRINTS, REPORTS, DISSERTATIONS, OR MANUSCRIPTS, OR STATE “NONE”.] [DISCLOSE ALL COMPETING INTERESTS.]

Sincerely,

[CORRESPONDING AUTHOR]  
[AFFILIATION]  
[EMAIL] | [ORCID]

