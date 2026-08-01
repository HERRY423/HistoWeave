# Prospective validation v2 status

Status: **registration-ready, not publicly preregistered, execution blocked**.

This directory deliberately contains no outcome data and makes no claim of an independent timestamp. The protocol fixes the non-oracle task contract, grouped holdout requirements, primary endpoint, bootstrap procedure, and fail-closed decision rules.

Execution remains prohibited until all of the following are true:

1. one untouched study accession or DOI is selected without outcome inspection;
2. its absence from every development source is hash-audited;
3. the completed protocol hash is posted to an independent public timestamping service;
4. the public URL and UTC timestamp are recorded in `protocol.json`; and
5. `execution_permitted` is changed to `true` only after that timestamp is visible.

The current Wu et al. 2021 analysis cannot fill this role: it has already been executed, lacks an independent public timestamp, and uses oracle K.

This status is intentionally fail-closed. A local Git date or file modification time is not treated as preregistration evidence.

---

## Second study candidate (registration-ready, execution blocked)

- **Study:** Pelka et al. 2021 CRC Visium — GEO **GSE178341** (paper DOI
  [10.1016/j.cell.2021.08.003](https://doi.org/10.1016/j.cell.2021.08.003)).
- **Independence audit:** confirmed — 0 hits across 799 development sources
  (`independence_audit_pelka.json`; must be re-run at registration).
- **Protocol:** `protocol_pelka2021_crc_visium.json`;
  rationale: `README_pelka2021_crc_visium.md`.
- **Aligned meta-panel readiness:** `meta_panel_alignment/REPORT.md` —
  0/135 seed-complete cells under the three-seed non-oracle contract
  (6 partial-seed cells, seed 42 only); 135-cell backlog must be re-run under
  k_policy=estimate on all seeds before grouped validation can gate
  personalisation.
- Execution remains forbidden until the public-timestamp steps in the protocol
  are completed.
