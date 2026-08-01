# HistoWeave Bioinformatics P1 submission freeze v4

The scientific narrative, evidence boundaries, supplementary material, cover letter, references, and deterministic artwork are frozen at editorial review quality. The package is not represented as immediately uploadable.

- Freeze date: 2026-08-01
- Structured abstract: 139 words (recommended maximum 150)
- Main body: 4649 words (target maximum 5,000)
- Main figures: 4; Fig.4 includes HER2ST primary external panels; all PNG review copies are at least 350 dpi
- Citation-key gaps: 0
- Evidence assertions passed: True
- Author-required placeholders: 9
- LaTeX compile: not run because no TeX engine is installed locally
- Freeze-critical pytest: 38 passed, 0 skipped, 0 failed (ok)
- Full repository regression: not re-run at freeze (set HISTOWEAVE_FREEZE_FULL_PYTEST=1); critical suite recorded below
- Canonical narrative: `manuscript/main.tex` + `manuscript/supplementary.tex` (Markdown drafts deprecated)
- Zenodo concept DOI: https://doi.org/10.5281/zenodo.21586217 (re-deposit after freeze changes)

Blocking actions before journal upload:

1. Human authors must resolve Bioinformatics AI-policy compliance, substantively verify/rewrite the text as required, and make an accurate disclosure.
2. Authors must supply names, affiliations, ORCID, corresponding-author details, CRediT roles, funding, acknowledgements, and conflicts.
3. Compile and visually inspect the sources in the current official OUP template.
4. Publish a Zenodo version whose notes match this freeze date and HER2ST `figure_data.json` hash.

Scientific risks remain explicit: the real-study policies still do not show improved personalised selection (HER2ST uses the global default and CRC returns evidence_required); the strict same-mask panel contains 13 units across two studies; 15 CRC attempts were user-authorised runtime skips without imputation; and the positive selection result is synthetic construct validity only.

Run `python submission_freeze_v4/reproduce_submission_freeze.py --check` to verify the complete locked package.
