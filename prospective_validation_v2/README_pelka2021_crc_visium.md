# Second untouched prospective study — Pelka 2021 colorectal cancer Visium

Status: **registration-ready, not publicly timestamped, execution blocked.**

This is the second prospective external-study validation. The first (HER2ST,
v3) validated fail-closed behaviour but had zero personalisation coverage and
one study / seven donors. The v3 assessment named the blocker for a defensible
positive claim: *an aligned, grouped, non-oracle development meta-panel that
validates the gate before another untouched study is opened.* This bundle
addresses that blocker and locks the second study, without yet executing it.

## Study selection

- **Paper:** Pelka K. et al., "Spatially organized multicellular immune hubs in
  human colorectal cancer", *Cell* 184(18):4734–4752.e20 (2021).
  According to PubMed (PMID 34450029), paper DOI
  [10.1016/j.cell.2021.08.003](https://doi.org/10.1016/j.cell.2021.08.003).
- **Data series:** NCBI GEO **GSE178341** (BioProject **PRJNA738517**),
  "A Single Cell Atlas of MMRd and MMRp Colorectal Cancer" — Regev Lab, Broad.
- **Why CRC Visium:** the development landscape is DLPFC-heavy; the only CRC
  cell in dev is `visium_hd_crc` (Visium HD, a different platform/study). Pelka
  is classic 10x Visium, FFPE colorectal cancer, with multiple tumour donors —
  the right transport-breadth contrast (different study, platform generation,
  pathologist annotation semantics).

## Independence audit

`scripts/audit_study_independence.py` scans 799 text development sources
(tracked files + validation/submission evidence) for the identifiers
`pelka`, `GSE178341`, `PRJNA738517`, `10.1016/j.cell.2021.08.003`.

- Verdict at preparation: **independence_confirmed** (0 hits).
- Full per-file hashes: `prospective_validation_v2/independence_audit_pelka.json`.

The audit MUST be re-run at registration time against the then-current tree,
and its source hashes recorded in the public registration record.

## Aligned meta-panel (training basis)

`scripts/build_aligned_meta_panel.py` defines the aligned contract
(spatial_domain, pathology GT, ARI, k_policy=estimate, seeds 42/1/2, 9-method
panel, study/donor split) and measures in-repo compliance:

- 135 aligned cells; **0 seed-complete (0.0%)** under the three-seed contract.
  Six cells (STAGATE + SpaGCN on the three DLPFC donors) carry explicit
  non-oracle K for seed 42 only and are reported as partial-seed.
- **135-cell backlog** must be re-run under estimate-K on all three seeds
  (42/1/2) before grouped non-oracle validation can gate personalisation.
- Wu 2021 breast is excluded from the panel (locked independent test set).

`meta_panel_alignment/REPORT.md` and `meta_panel_alignment/meta_panel_manifest.json`
are the readiness record. The `compliant_non_oracle_cells` / `backlog_cells`
numbers in the protocol JSON are bound to that manifest.

## What this protocol permits and forbids

- **Forbidden until a public timestamp exists:** downloading or opening any
  Pelka outcome-bearing file, including pathology annotations.
- **Permitted now:** everything above (selection, audit, protocol drafting),
  plus running the meta-panel backlog on development data already in repo.
- After the timestamp: execute only per the locked task contract, seeds, method
  panel, and endpoints in `protocol_pelka2021_crc_visium.json`.

## Public timestamp procedure (operator action, not automatable here)

The v3 precedent used a public GitHub issue and recorded GitHub server time.
Follow the same pattern:

1. `git add` this directory + `meta_panel_alignment/` and commit.
2. Re-run `python scripts/audit_study_independence.py ... ` (same flags) and
   confirm verdict stays `independence_confirmed`.
3. Compute `sha256(protocol_pelka2021_crc_visium.json)`.
4. Create a public issue/release/Gist (or opentimestamps / Zenodo draft) that
   contains the protocol hash, the study accession, and the UTC time; record
   the URL.
5. Edit the four null `registration_gate` fields in the protocol JSON
   (URL, timestamp, protocol_sha256_at_registration) and set
   `execution_permitted=true`, then commit. Never change endpoints, thresholds,
   seeds, or the method panel.

## Honest expectation

The primary endpoint passes only if the action is justified; a zero-coverage
global-default result here would again be a valid negative finding, not a
failure. This study exists to give the aligned meta-panel a genuine second
transport target — not to manufacture a positive personalisation result.
