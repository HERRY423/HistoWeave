# Bioinformatics Original Paper: updated feasibility and risk assessment

## Decision

**Feasible only with a narrowed paper claim.** The new experiment removes the
largest prior credibility gap: HistoWeave now has a publicly time-stamped,
outcome-sealed, donor-level, non-oracle validation on a truly external study,
with an aligned nine-method panel and a direct policy comparison. It does not,
however, support the stronger claim that HistoWeave has validated personalised
method-selection advantage.

The defensible paper is an evidence-governance and selective-decision protocol
paper: HistoWeave prevents unsupported personalisation, records why it refuses,
and can personalise in a locked construct-validity setting when a reliable
target-free signal exists. It is not yet a demonstrated cross-study
meta-selector.

## What the new evidence establishes

1. Public registration preceded outcome-bearing HER2ST access.
2. Seven donors were independently evaluable after the locked exclusion of G2.
3. SpaGCN, STAGATE, GraphST, BayesSpace, BANKSY, spectral clustering,
   GaussianMixture, k-means, and agglomerative clustering used the same
   label-free estimated K, spot set, and seed grid.
4. The full-panel availability criterion passed: every method was available on
   at least five donors; GaussianMixture was unavailable on donor C.
5. HistoWeave selected the pre-registered SpaGCN global default for all seven
   donors because grouped, aligned full-panel development validation was
   unavailable. Its external personalisation coverage was zero at every locked
   threshold.
6. The existing ungated 3-NN rule was frozen before truth access and selected
   GaussianMixture for every donor. On the six-donor common availability mask,
   HistoWeave minus existing-rule deployed regret was 0.0002 (95% donor
   bootstrap CI -0.0893 to 0.0922): no detectable advantage in either
   direction.
7. The positive construct-validity scenario selected non-global STAGATE on
   23/60 independent test units and reduced regret versus always-global, so the
   implementation is not hard-coded to refuse. The malformed registered
   compound success predicate remains failed.

## Major submission risks

### Central efficacy claim remains negative

The primary HistoWeave-versus-global contrast is exactly zero because both
policies take the same action. Passing the 0.02 non-inferiority margin by action
identity is not evidence of better selection. The paper must not describe this
as personalised validation, superiority, or an improved risk–coverage frontier.

### Coverage–risk evidence is informative but degenerate externally

External HistoWeave coverage is zero across the whole threshold grid. The
positive synthetic scenario shows non-degeneracy of the implementation, but it
cannot substitute for biological personalisation. Reviewers may reasonably ask
for an aligned development meta-panel and a second untouched study on which
coverage is nonzero.

### One study and seven donors

HER2ST provides genuine independence but limited transport breadth. It is a
legacy Spatial Transcriptomics breast-cancer study, and pathologist regions are
only one ground-truth construct. Confidence intervals are wide; generalisation
to Visium, single-cell-resolution assays, other organs, or other annotation
semantics is untested.

### Algorithm-selection evidence is underpowered

The direct existing-rule comparison contains six common donors. The estimate is
near zero with a wide interval. BANKSY has the highest mean donor ARI in this
panel, but selecting it retrospectively would be oracle method selection and is
strictly descriptive.

### The positive-control registration contains an impossible condition

Coverage is defined as choosing a non-global method, while the success predicate
also requires the global spectral method among covered units. The condition was
correctly left unrepaired. This transparency is preferable to retrospective
editing, but reviewers may treat it as a protocol-design quality defect.

### Manuscript and journal-compliance work remains

The current manuscript working tree still describes the earlier Wu 2021 stress
test and must be reconciled with this new HER2ST validation. Human authors must
approve the revised claims, author metadata, AI-assistance disclosures, and
Bioinformatics machine-learning/validation-policy interpretation. The final OUP
template/Overleaf build and submission portal metadata still require human
verification.

## Recommended positioning

Lead with the executable evidence contract, outcome sealing, common non-oracle
K contract, backend fail-closed behavior, donor-level uncertainty, and explicit
risk–coverage accounting. Present the zero-coverage external result as a
falsifiable negative result: the available development evidence does not
justify personalised deployment. Use the positive scenario only to demonstrate
construct validity.

Do not lead with “method recommendation accuracy,” “personalised superiority,”
“state-of-the-art selection,” or “universally safer.” A suitable claim is:

> HistoWeave operationalizes evidence admissibility and selective
> method-decision rules for spatial transcriptomics; in a prospective external
> donor-level validation, it correctly retained the locked global action
> because the evidence needed to justify personalisation was absent.

## Go/no-go

- **Go for a carefully reframed Original Paper:** after manuscript integration,
  human policy review, metadata completion, and successful OUP compilation.
- **No-go for the stronger personalised-selector paper:** another prospective
  study is needed after building an aligned, grouped, non-oracle development
  meta-panel capable of validating nonzero personalisation coverage.

