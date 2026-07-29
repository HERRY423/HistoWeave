# Prospective HER2ST validation v3

This directory locks a donor-level, non-oracle external validation before any
HER2ST outcome-bearing file is accessed.

The confirmatory unit is the donor, not the section or spot. All 36 publicly
described sections are eligible, but section scores are first averaged within
the eight publicly described donors. Ground-truth labels stay sealed until
every method prediction has been written and hashed.

The common panel is fixed to official SpaGCN, STAGATE, GraphST, BayesSpace and
BANKSY plus spectral clustering, Gaussian mixture, k-means and agglomerative
clustering. Every method receives the same spots, raw counts, coordinates,
estimated non-oracle K, and three seeds. Histology and true K are prohibited.
Official backend failures are reported and never replaced by a look-alike
implementation.

The decision comparison is also fixed before outcome access: always-global,
the existing ungated three-nearest-neighbour recommendation, the published
Chen et al. 2025 SRTBenchmark recommendation rule, and the evidence-gated
HistoWeave policy. The main statistic is donor-level paired regret, accompanied
by the full risk-coverage curve.

The synthetic positive control tests only whether the decision implementation
can personalise when a reliable target-free signal is deliberately present. It
must not be described as independent biological validation.

Execution remains blocked until `registration_receipt.json` points to a public
GitHub issue that records the protocol commit SHA and protocol SHA-256.
