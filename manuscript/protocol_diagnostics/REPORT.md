# Protocol diagnostics (auto-generated)

Source: `manuscript\protocol_diagnostics\action_frequency_and_sensitivity.json`

## Action frequency (n=20 study-grouped queries)

- Default policy: `{'abstain': 0, 'evidence_required': 13, 'global_default': 7, 'personalised_set': 0}`
- Ablation `require_heldout_validation=False`: `{'abstain': 0, 'evidence_required': 1, 'global_default': 7, 'personalised_set': 12}`

## Threshold sensitivity

- With held-out gate on, `personalised_set` remains 0 across the rank-support × min_support grid (held-out gate dominates).

## Risk–coverage

- Selective recommended policy: `always_global_default` at coverage 0.0
- HER2ST coverage: 0.0 (degenerate_zero_coverage)

## Registration strength

- Class: `public_repository_timestamp_not_osf`
- URL: https://github.com/HERRY423/HistoWeave/issues/19
- UTC: 2026-07-29T05:34:31Z
