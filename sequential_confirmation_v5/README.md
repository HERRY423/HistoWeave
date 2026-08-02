# DLPFC sequential confirmation v5

Public-lock-gated sequential confirmation of the frozen nested unit-holdout
policy from `positive_personalisation_v5` on three LIBD DLPFC donors.

## Public lock (required before outcome scoring)

1. Commit this directory + frozen policy artefacts.
2. Open a GitHub issue citing:
   - `protocol_id`: `histoweave-dlpfc-sequential-confirmation-2026-08`
   - commit SHA
   - `results/frozen_policy.json` SHA-256
3. Only then score DLPFC ARI / apply the policy contrast.

## Commands

```powershell
$env:PYTHONPATH = "src;."
python sequential_confirmation_v5\prepare_dlpfc.py
python sequential_confirmation_v5\freeze_policy.py

# After public lock is visible:
python sequential_confirmation_v5\run_panel.py `
  --methods spectral,gaussian_mixture,kmeans,agglomerative
# then deep methods as compute permits:
python sequential_confirmation_v5\run_panel.py `
  --methods spagcn,stagate,graphst,bayesspace,banksy

python sequential_confirmation_v5\score_and_apply_policy.py
```

## Claim boundary

- Neighbor bank = HER2ST + CRC only.
- DLPFC outcomes never enter gate or global-default selection.
- DLPFC was previously used for T1 oracle-K dual-track reporting; sequential
  confirmation discloses that prior descriptive use.
- n=3 donors: bootstrap intervals are descriptive.
