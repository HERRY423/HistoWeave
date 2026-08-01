# Prospective validation v3: final execution addendum

This addendum extends `deviations.md`. It was written after aggregate scoring;
it does not change any method, parameter, threshold, exclusion, or claim rule.

## Existing-rule action-freeze input-directory retry

The first target-free kNN action-freeze invocation looked for
`label_free_h5ad/`, while the prepared directory is named `inputs/`; it produced
an empty action file. The path was corrected before truth was unsealed. The
replacement frozen file contains all seven samples, declares
`truth_accessed=false`, and has SHA-256
`3790e0b2c347dc6a28fae3523bc8644e469d99cddc9176875e55efadc6bb1c39`.

## GaussianMixture donor C unavailable

All three GaussianMixture seeds failed on donor C with a singular-covariance
error. Five GaussianMixture cells failed in total; donor A retained one
successful seed. No covariance regularization or imputation was added after
outcome access. The method remains available on six donors, so the registered
nine-method minimum (at least five donors per method) passes. Comparisons with
the existing kNN rule, which selected GaussianMixture for all samples before
truth access, use the six-donor common availability mask.

## Accidental repeat-run terminated before scoring

After all 189 checkpoints completed, the panel runner was invoked with the full
method list to rebuild a combined manifest. Its checkpoint key included the
requested-run configuration, so it began recomputing completed cells. The
repeat process was terminated. A dedicated manifest-only script then assembled
the 189 existing checkpoint records and verified every successful CSV against
its stored SHA-256. The resulting pre-scoring manifest contained 184 successes
and five failures and had SHA-256
`e03d2f5d2e0973c94572b43e07db0482574cdb4454656443502108926db55ecc`.
Only after that verification passed was truth unsealed.

