# P0 evidence-admission audit

Protocol: `histoweave.evidence_admission_audit.v1`

- Adversarial cases: **9**
- Incompatible-evidence admission rate: **0.000**
- Valid-evidence false-rejection rate: **0.000**
- Dominated-selection rate: **0.000**
- All predeclared cases passed: **True**

The corpus exercises the complete `build_decision_card` path. It includes
cross-task references, cluster-proxy ground truth, missing and oracle K policies,
missing metric declarations, unverified validation JSON, and validation bindings
with mismatched task, method panel, or K policy. The dominated-choice case uses
a matched Pareto table in which the locally ranked candidate is strictly dominated.
