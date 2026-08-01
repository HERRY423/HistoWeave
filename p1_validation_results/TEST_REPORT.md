# HistoWeave P1 regression record

Final full-repository run on 2026-07-27:

- Command: `python -m pytest -q`
- Result: **832 passed, 8 skipped, 0 failed**
- Runtime: 306.50 seconds
- Warnings: 784

The eight skips are dependency- or environment-gated tests: three Harmony
tests without `harmonypy`, one nnSVG test without the required R bridge and
package, two R-bridge tests, and two network-gated real-data download tests.

Before the final run, seven DLPFC tests exposed one truncated temporary HDF5
cache. The test harness now structurally validates that cache, downloads to a
staging path, and atomically replaces invalid content. One P1 audit-script
logging-contract failure was also corrected. The final full run above was
performed after both corrections.
