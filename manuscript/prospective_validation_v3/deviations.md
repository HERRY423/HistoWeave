# Prospective validation v3: deviations and execution incidents

This log is append-only in spirit: every incident is retained, including failed
attempts. None of the changes below used HER2ST outcome labels to select a
method, parameter, threshold, or analytic rule.

## Locked-protocol deviations

### HER2ST G2 excluded by the locked one-to-one matching rule

The G2 pathologist-label table contains duplicated spatial coordinates. The
pre-registered preparation rule required a one-to-one coordinate join and
forbade ambiguous repair. G2 was therefore excluded. Seven independently
labelled donors (A, B, C, D, E, F, and H) remain evaluable, exceeding the
pre-registered minimum of five.

### Positive-control success predicate is internally inconsistent

The locked positive-control predicate required both (i) personalization
coverage of at least 0.50 and (ii) both spectral clustering and STAGATE to be
selected among covered units. Coverage was simultaneously defined as choosing
a method different from the always-global default, and the locked global
default is spectral clustering. Spectral clustering therefore cannot occur on
a covered unit. The primary pre-registered positive-control success flag remains
`false`; it is not retrospectively repaired.

The descriptive non-degeneracy result is retained separately: at threshold
0.25, the protocol selected the non-global STAGATE action for 23/60 held-out
units (coverage 0.3833) and improved mean loss relative to always-global by
-0.0853 (95% bootstrap CI -0.1294 to -0.0415). This supports only the claim that
the implementation can personalize when a reliable signal exists; it does not
satisfy the malformed compound success predicate.

## Execution incidents that did not change scientific parameters

### Python boolean typo

The panel runner initially used the JSON token `false` in Python rather than
`False`. Baseline prediction files had already completed. The typo was corrected
before rebuilding the manifest; no prediction or score was changed.

### R/HDF5 dependency retry

The first BayesSpace/BANKSY bridge attempt lacked `HDF5Array`, required by the
H5AD conversion path. The isolated R library was completed and the failed
attempt was archived before rerunning.

### BANKSY 1.6.0 API compatibility retries

Two BANKSY bridge attempts failed before scoring: the first because the current
API interpreted the legacy `M=1` path as AGF, and the second because the default
clustering call requested 20 PCs after the locked preprocessing created 15.
The bridge was made explicit with `use_agf=FALSE`, `compute_agf=FALSE`, and a
matching 15-PC clustering call. These are interface-compatibility corrections;
the locked lambda, feature count, PC count, K estimator, seed grid, and
clustering family were unchanged. All failed-attempt records are preserved.

