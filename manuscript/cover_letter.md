# Cover letter draft — HistoWeave Original Paper (narrowed claim)

**To:** The Editors, *Bioinformatics*  
**From:** [CORRESPONDING AUTHOR, AFFILIATION]  
**Date:** [SUBMISSION DATE]

Dear Editors,

We submit “HistoWeave: evidence-governed method decisions with structured abstention for spatial transcriptomics” for consideration as an Original Paper in the Gene expression category.

HistoWeave addresses a practical computational-biology problem that is not solved by another clustering algorithm: how to decide which benchmark evidence can support a method choice for a declared spatial-analysis task, and when the system must retain a global comparator, request further evidence, or abstain. Its main contribution is an executable evidence contract that binds task and ground-truth semantics, cluster-count policy, metric direction, method coverage, grouped holdout design, source hashes, and matched Pareto trade-offs to a versioned decision card.

The evaluation is deliberately claim-bounded and preserves negative results. An 11-case adversarial audit admitted no incompatible evidence. On DLPFC, oracle access to domain count \(K\) changed SpaGCN ARI by more than half on one section, motivating dual-track oracle versus estimated-\(K\) reporting. A five-dataset leave-one-out ranking is retained only as a diagnostic of the candidate generator and tied the training-fold global comparator (mean regret 0.0059 for both). Across 20 grouped queries, always-personalising incurred higher regret than always-global (0.047 versus 0.029), so the protocol retained the global default. In a publicly time-stamped, non-oracle, donor-level HER2ST external validation, personalisation coverage was zero and actions matched the locked global default. A synthetic construct-validity panel shows the implementation is not hard-coded to refuse when a reliable target-free switch signal exists. We do **not** claim validated personalised superiority, non-oracle deployment advantage over global defaults, or transport of spatial-region results to cell-type labels.

We recognize the journal’s machine-learning policy concerning leave-one-out validation. The five-dataset analysis is retained strictly as a non-predictive diagnostic of the ranking proxy, not as independent confirmation of personalised selection. The primary external claim rests on the registered HER2ST donor-level study and the selective regret–coverage analysis. If the bounded diagnostic use of leave-one-out is nevertheless considered outside the journal’s policy, we welcome editorial guidance and can move that analysis to the Supplement.

The software, documentation, test data, unit and adversarial tests, figure-generation code, and SHA-256-locked submission artefacts are freely available under BSD-3-Clause at <https://github.com/HERRY423/Histoweave> and archived at <https://doi.org/10.5281/zenodo.21586217>. Public source datasets are cited with persistent identifiers; raw data are not redistributed. HER2ST protocol registration: <https://github.com/HERRY423/HistoWeave/issues/19>.

**Mandatory author completion before this letter can be submitted:** This working draft received OpenAI Codex assistance. Current *Bioinformatics* guidance permits disclosed limited assistance but states that drafting papers from prompts is unacceptable. The human authors must substantively rewrite and verify the manuscript and describe only the final permitted use, or obtain written guidance from the Editorial Office. Replace this paragraph with an accurate, policy-compliant disclosure only after that action is complete.

The authors confirm that the final work is original, is not under consideration elsewhere, and has been approved by every listed author. [DISCLOSE ANY RELATED PREPRINTS, REPORTS, DISSERTATIONS, OR MANUSCRIPTS, OR STATE “NONE”.] [DISCLOSE ALL COMPETING INTERESTS.]

Sincerely,

[CORRESPONDING AUTHOR]  
[AFFILIATION]  
[EMAIL] | [ORCID]
