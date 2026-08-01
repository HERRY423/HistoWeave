# Prospective CRC patient-level validation v4

This directory executes the publicly registered second external validation
from GitHub issue 20. The 14 Visium sections are two technical replicates from
seven patients; the patient is the independent unit.

Completed evidence state:

- public registration preceded all CRC data access;
- all 14 Space Ranger archives match their locked Zenodo MD5 values;
- 14 label-free H5AD inputs cover all seven patients;
- one non-oracle K is estimated per section and shared by all nine methods;
- prediction attempts are written and hashed per sample/method/seed;
- all 378 attempts and policy actions were frozen before pathology annotations
  were downloaded and imported;
- 361 attempts succeeded and 17 failed; 15 A120838 deep-method cells are
  user-authorized runtime skips, with one GraphST memory failure and one
  Gaussian-mixture numerical failure; no failure was imputed;
- all seven patients remain on the strict nine-method mask under the registered
  replicate-failure rule;
- the registered development meta-panel minimum was not met, so the
  policy action is `evidence_required`; this is not an efficacy result.

The fixed method panel is SpaGCN, STAGATE, GraphST, official BayesSpace,
official BANKSY, spectral clustering, Gaussian mixture, k-means, and
agglomerative clustering. Missing results are never imputed. The strict SOTA
summary uses one nine-method complete patient mask within each study.

```powershell
python prospective_validation_v4\prepare_crc_v4.py `
  --source datasets_cache\raw_sources\crc_v4 `
  --output datasets_cache\crc_v4_prepared

python prospective_validation_v4\run_panel.py `
  --prepared datasets_cache\crc_v4_prepared `
  --output datasets_cache\crc_v4_results `
  --r-lib "C:\Spatial Transcriptomics\histoweave-r-lib-v3"

python prospective_validation_v4\freeze_policy_actions.py `
  --prepared datasets_cache\crc_v4_prepared `
  --development-status prospective_validation_v4\development_meta_panel_status.json `
  --output datasets_cache\crc_v4_results\policy_actions.json

python prospective_validation_v4\freeze_predictions.py `
  --prepared datasets_cache\crc_v4_prepared `
  --results datasets_cache\crc_v4_results

python prospective_validation_v4\authorize_truth_unseal.py `
  --prediction-freeze datasets_cache\crc_v4_results\prediction_freeze.json `
  --policy-actions datasets_cache\crc_v4_results\policy_actions.json `
  --output datasets_cache\crc_v4_results\truth_unseal_authorization.json
```

The annotation archive was opened only after joint
`truth_unseal_authorization.json` creation from both one-time freezes. A
completed method matrix alone does not
support personalised selection if the development-policy gate remains unmet.
