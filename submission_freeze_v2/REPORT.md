# HistoWeave P0 submission freeze v2

Local P0 engineering and verification are complete. The evidence gate is fail-closed for task, ground truth, K policy, metric, method panel, grouped holdout, and source hashes.

- Adversarial cases: 11 (9 invalid; 2 valid controls)
- Incompatible-evidence admission rate: 0.000
- Valid-evidence false-rejection rate: 0.000
- Dominated-selection rate: 0.000
- External panel: 15 prespecified methods, 13 fully finite, oracle K
- Public prospective registration: pending; execution remains blocked

Run `python submission_freeze_v2/reproduce_submission_freeze.py --check` to verify every locked source and generated artifact.
