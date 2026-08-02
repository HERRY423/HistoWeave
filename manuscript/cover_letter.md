# Cover letter draft — HistoWeave Original Paper (narrowed claim)

**To:** The Editors, *Bioinformatics*  
**From:** [CORRESPONDING AUTHOR, AFFILIATION]  
**Date:** [SUBMISSION DATE]

Dear Editors,

We submit “HistoWeave: evidence-governed method decisions with structured abstention for spatial transcriptomics” for consideration as an Original Paper in the Gene expression category.

HistoWeave addresses a practical computational-biology problem that is not solved by another clustering algorithm: how to decide which benchmark evidence can support a method choice for a declared spatial-analysis task, and when the system must retain a global comparator, request further evidence, or abstain. Its main contribution is an executable evidence contract that binds task and ground-truth semantics, cluster-count policy, metric direction, method coverage, grouped holdout design, source hashes, and matched Pareto trade-offs to a versioned decision card.

The evaluation is deliberately claim-bounded and preserves negative results. An 11-case adversarial audit admitted no incompatible evidence. On DLPFC, oracle access to domain count \(K\) changed SpaGCN ARI by more than half on one section, motivating dual-track oracle versus estimated-\(K\) reporting. A historical five-study oracle-\(K\) landscape is descriptive only. Across 20 grouped queries, always-personalising incurred higher regret than always-global (0.047 versus 0.029). In a registered non-oracle HER2ST study, personalisation coverage was zero. A second outcome-sealed CRC study completed a seven-patient, nine-method common mask with all actions frozen as `evidence_required`. After assembling the aligned HER2ST+CRC non-oracle panel (13 strict units), nested unit-holdout gated 1-NN personalisation covered 5/13 units and lowered deployed regret versus always-global (−0.0115; 95% CI −0.0215 to −0.0029). Cross-study transport between HER2ST and CRC remained fail-closed and is **not** claimed. A sequential DLPFC three-donor confirmation is public-lock gated. A repaired fixed-split synthetic construct test shows improved selection under an identifiable switch and zero coverage under no signal. We do **not** claim universal personalised superiority, HER2ST↔CRC transport, or transport of spatial-region results to cell-type labels.

Development fitting, gate calibration, and final testing have non-overlapping roles. The two registered prospective studies contribute 13 strict common-mask donor/patient units and remain study-stratified. Fifteen CRC runtime skips are disclosed and not imputed. The historical five-study landscape contributes no model-validation metric.

The software, documentation, test data, unit and adversarial tests, figure-generation code, and SHA-256-locked submission artefacts are freely available under BSD-3-Clause at <https://github.com/HERRY423/Histoweave> and archived at <https://doi.org/10.5281/zenodo.21586217>. Public source datasets are cited with persistent identifiers; raw data are not redistributed. Protocol registrations: HER2ST <https://github.com/HERRY423/HistoWeave/issues/19>; CRC <https://github.com/HERRY423/HistoWeave/issues/20>.

**Mandatory author completion before this letter can be submitted:** This working draft received OpenAI Codex assistance. Current *Bioinformatics* guidance permits disclosed limited assistance but states that drafting papers from prompts is unacceptable. The human authors must substantively rewrite and verify the manuscript and describe only the final permitted use, or obtain written guidance from the Editorial Office. Replace this paragraph with an accurate, policy-compliant disclosure only after that action is complete.

The authors confirm that the final work is original, is not under consideration elsewhere, and has been approved by every listed author. [DISCLOSE ANY RELATED PREPRINTS, REPORTS, DISSERTATIONS, OR MANUSCRIPTS, OR STATE “NONE”.] [DISCLOSE ALL COMPETING INTERESTS.]

Sincerely,

[CORRESPONDING AUTHOR]  
[AFFILIATION]  
[EMAIL] | [ORCID]
