# Invalid synthetic v2.0 execution retained

The first v2 execution is excluded from evidence.  Training selected STAGATE
as the global method, while the null generator hard-coded spectral as the
uniformly best method.  Consequently the alleged no-signal panel actually
contained a method switch relative to the training-derived global action.

Observed invalid-run diagnostics are retained for provenance:

- selected threshold: 0.50;
- signal coverage: 0.4333;
- signal regret difference: -0.0896 (95% bootstrap CI -0.1213 to -0.0574);
- null coverage: 0.5083;
- null regret difference: -0.1575 (95% bootstrap CI -0.1860 to -0.1294).

The protocol and generator were advanced to v2.1, the global method is now
passed explicitly into the null generator, and all generator/bootstrap seeds
were changed before the v2.1 rerun.  This invalid run is not counted as a pass.
