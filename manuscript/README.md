# HistoWeave P1 manuscript package

## Single narrative source of truth

| Role | File |
|------|------|
| **Main paper (authoritative)** | `main.tex` |
| **Supplement (authoritative)** | `supplementary.tex` |
| Cover letter draft | `cover_letter.md` |
| Journal compliance record | `SUBMISSION_COMPLIANCE.md` |
| Author-only fields | `AUTHOR_METADATA_REQUIRED.md` |
| HER2ST locked figure data | `prospective_validation_v3/figure_data.json` |
| Figure builder | `make_submission_assets.py` |
| Static audit | `audit_submission.py` |
| Artwork | `figures/` (SVG, PNG, TIFF) |

**Deprecated:** `HistoWeave_manuscript (1).md` — historical notes only; never upload.

Scientific claim: **fail-closed evidence governance + selective abstention**, not validated personalised method selection. Evidence tiers T0–T5 are defined in `main.tex` and expanded in `supplementary.tex`.

## Regenerate and verify

```powershell
python manuscript\make_submission_assets.py
python manuscript\audit_submission.py
python submission_freeze_v4\reproduce_submission_freeze.py
python submission_freeze_v4\reproduce_submission_freeze.py --check
```

The repository may not contain a LaTeX engine; P1 uses static TeX validation
and artefact hashes locally. Compile in the official OUP/Overleaf environment
before upload.

**Do not submit until every blocker in `SUBMISSION_COMPLIANCE.md` is resolved.**

## Zenodo sync

Software concept DOI: `https://doi.org/10.5281/zenodo.21586217`  
Metadata templates: repo-root `.zenodo.json`, `CITATION.cff`  
After freeze changes, mint a new Zenodo version whose notes cite
`submission_freeze_v4/REPORT.md` freeze date and the registered HER2ST/CRC
evidence hashes. Version 3 is retained as a historical freeze and must not be
regenerated from the current manuscript paths.
