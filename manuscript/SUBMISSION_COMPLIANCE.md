# Bioinformatics Original Paper compliance record

Checked against the official *Bioinformatics* author guidance on **2026-07-31**
(previous formal check: 2026-07-27; claim package re-aligned after HER2ST
integration and SI refresh).

Official sources:

- Author guidelines: <https://academic.oup.com/bioinformatics/pages/author-guidelines>
- Online submission preparation: <https://academic.oup.com/bioinformatics/pages/submission_online>

## Canonical package (single narrative source)

| Role | Path | Status |
|---|---|---|
| **Authoritative manuscript** | `manuscript/main.tex` | Use for all scientific claims |
| **Authoritative supplement** | `manuscript/supplementary.tex` | T0–T5 tables; HER2ST registration; DecisionCard fields |
| Cover letter draft | `manuscript/cover_letter.md` | Narrowed fail-closed protocol framing |
| Author metadata checklist | `manuscript/AUTHOR_METADATA_REQUIRED.md` | Pending human input |
| Figures | `manuscript/figures/` via `make_submission_assets.py` | Fig.4 = selective + HER2ST |
| HER2ST machine-readable | `manuscript/prospective_validation_v3/figure_data.json` | Locked into freeze |
| Protocol diagnostics | `manuscript/protocol_diagnostics/` | Action frequency, threshold sensitivity, risk–coverage, registration class |
| Install smoke | `tests/test_install_smoke.py` | CLI + DecisionCard without data download |
| Submission freeze | `submission_freeze_v3/` | SHA-256 package; not upload-ready alone |
| **Deprecated draft** | `manuscript/HistoWeave_manuscript (1).md` | **Do not submit or cite** |

Any divergence must be resolved in favour of `main.tex` + `supplementary.tex`.

## Requirements applied

| Item | Current official requirement | P1 implementation |
|---|---|---|
| Article type | Original Paper; new computational-biology research using biological data | Original Paper, Gene expression — **evidence-governance / selective decision protocol** |
| Length | Up to 7 template pages; ≈5,000 words excluding figures | Static audit enforces body ≤5,000; see latest `p1_validation_results/submission_audit.json` |
| Abstract | Motivation, Results, Availability and Implementation, Contact, Supplementary Information; ≤150 words recommended | Five headings; latest audit word count recorded in freeze REPORT |
| Initial format | Format-free allowed; ≥12 pt, double spacing, line numbers preferred | `article` 12 pt, double-spaced, `lineno` |
| Figures | Publication resolution; ≥350 dpi colour/halftone | Deterministic SVG, 400 dpi PNG, 350–400 dpi TIFF |
| Graphical abstract | File named `graphical_abstract` | Generated with figures |
| Data availability | Required; public data with persistent IDs | Main text + SI; HER2ST, Wu, and CRC Zenodo DOIs |
| Software | Functional, documented, free HTTPS URLs, test data, archive | GitHub, PyPI, BSD-3-Clause, tests, Zenodo DOI |
| Machine learning | Train/calibration/independent-test clarity; LOOCV normally rejected | **No LOOCV validation claim**; T2 is descriptive only; fixed development/calibration roles and registered external tests are explicit |
| Peer review | Single anonymized | Author metadata must be present for submission |
| ORCID | Submitting author required | Pending author input |
| Funding and conflicts | Complete declarations | Placeholders in TeX |
| LLM/AI use | Limited assistance disclosed; drafting from prompts unacceptable | **Critical blocker** |

## Critical submission blockers

1. **LLM-policy compliance.** Human authors must substantively rewrite and verify the manuscript/SI/cover letter and document only permitted AI use (or obtain Editorial Office guidance).
2. **Author metadata.** Names, affiliations, ORCID, corresponding email, CRediT, funding, acknowledgements, conflicts (see `AUTHOR_METADATA_REQUIRED.md`).
3. **OUP template compile.** Local freeze does not compile LaTeX; authors must build in the current official Overleaf/OUP environment and inspect pagination/figures.

## Scientific framing (current — not “resolved marketing claims”)

| Topic | Framing in `main.tex` / SI |
|---|---|
| Historical landscape (T2) | Oracle-\(K\) method-score heterogeneity only; **no cross-validation metric or selector claim** |
| Fixed-split selector | Development fit and calibration gate are disjoint; independent-test outcomes cannot tune actions |
| Selective (T3) | Always-personalise regret **higher** than always-global → policy `always_global_default` |
| HER2ST + CRC (T4) | Two registered non-oracle studies; 13 strict same-mask units; CRC actions **evidence_required**; **not** personalised superiority |
| Oracle-K (T1) | Dual-track reporting; SpaGCN large drop under estimated \(K\) on some sections |
| Wu | **Secondary** oracle-\(K\) stress only |
| Prospective CRC v4 | Prediction/action freeze complete before annotations; 7/7-patient nine-method mask; 15 disclosed runtime skips; descriptive SOTA only |
| 135-cell non-oracle backlog | Infrastructure gap for *future* positive personalisation claims; **not** a current efficacy claim |

## Claim boundary retained

The present evidence supports an implemented, fail-closed evidence-governance protocol and a global-default decision under the evaluated evidence. It does **not** support:

- superior personalised method selection on unseen studies;
- non-oracle deployment superiority over global defaults;
- transport of spatial-region results to cell-type labels; or
- a reliable ISUS predictor of method gain.

Evidence tiers: **T0** contract audit → **T1** oracle-K sensitivity → **T2** historical descriptive landscape → **T3** selective regret–coverage → **T4** two registered prospective external studies → **T5** fixed-split synthetic construct validity.

## Freeze and Zenodo sync checklist

- [x] `main.tex` / `supplementary.tex` / cover letter / compliance share claim boundary  
- [x] Fig.4 generated from selective JSON + HER2ST `figure_data.json`  
- [x] `python manuscript/audit_submission.py` static audit  
- [x] `python submission_freeze_v3/reproduce_submission_freeze.py` (+ `--check`)  
- [ ] Human AI rewrite + disclosure  
- [ ] Author metadata complete  
- [ ] OUP PDF compile  
- [ ] Re-deposit freeze-aligned archive to Zenodo (`doi:10.5281/zenodo.21586217` concept; new version notes must cite freeze date and HER2ST figure_data SHA)  
- [ ] Confirm `.zenodo.json` / `CITATION.cff` version notes match freeze REPORT  

## Regeneration commands

```powershell
python manuscript\make_submission_assets.py
python manuscript\audit_submission.py
python submission_freeze_v3\reproduce_submission_freeze.py
python submission_freeze_v3\reproduce_submission_freeze.py --check
```
