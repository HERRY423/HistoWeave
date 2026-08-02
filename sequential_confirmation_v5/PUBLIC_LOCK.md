# Public lock checklist — DLPFC sequential confirmation v5

**Protocol ID:** `histoweave-dlpfc-sequential-confirmation-2026-08`

## Objects required before DLPFC outcome scoring

1. Public git commit on `origin` containing:
   - `sequential_confirmation_v5/protocol.json`
   - `sequential_confirmation_v5/results/frozen_policy.json`
   - `positive_personalisation_v5/` evidence pack
2. Public GitHub issue citing:
   - commit SHA
   - protocol ID
   - `frozen_policy.json` SHA-256
   - statement that DLPFC ARI scoring must not begin until this issue is visible

## Frozen policy (pre-outcome)

- Model: 1-NN (`k=1`)
- Neighbour bank: HER2ST + CRC_V4 only (13 units)
- Global method: `banksy`
- Deployment threshold: `0.08`
- Feature subset: `library_cv`, `spatial_autocorrelation`, `effective_rank_90`, `effective_rank_95`, `sv_entropy`

Compute SHA-256 after freeze:

```powershell
python -c "import hashlib,pathlib; p=pathlib.Path('sequential_confirmation_v5/results/frozen_policy.json'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

## Unlock rule

Label-free preparation and method runs may proceed after the lock is public.
**Scoring ARI against laminar labels and writing confirmation_results.json
must wait until the issue and commit are independently visible.**

## Independence disclosure

DLPFC layer annotations and dual-track oracle-K SpaGCN/STAGATE scores were
previously used for manuscript T1. The frozen policy was fit only on
HER2ST+CRC. DLPFC is sequential confirmation with that disclosure, not a
fully naive first touch of the tissue.
