# HistoWeave Bioinformatics P1 submission freeze v3

The scientific narrative, evidence boundaries, supplementary material, cover letter, references, and deterministic artwork are frozen at editorial review quality. The package is not represented as immediately uploadable.

- Freeze date: 2026-07-31
- Structured abstract: 130 words (recommended maximum 150)
- Main body: 4291 words (target maximum 5,000)
- Main figures: 4; Fig.4 includes HER2ST primary external panels; all PNG review copies are at least 350 dpi
- Citation-key gaps: 0
- Evidence assertions passed: True
- Author-required placeholders: 9
- LaTeX compile: not run because no TeX engine is installed locally
- Freeze-critical pytest: 23 passed, 0 skipped, 0 failed (ok)
- Full repository regression: not re-run at freeze (set HISTOWEAVE_FREEZE_FULL_PYTEST=1); critical suite recorded below
- Canonical narrative: `manuscript/main.tex` + `manuscript/supplementary.tex` (Markdown drafts deprecated)
- Zenodo concept DOI: https://doi.org/10.5281/zenodo.21586217 (re-deposit after freeze changes)

Blocking actions before journal upload:

1. Human authors must resolve Bioinformatics AI-policy compliance, substantively verify/rewrite the text as required, and make an accurate disclosure.
2. Authors must supply names, affiliations, ORCID, corresponding-author details, CRediT roles, funding, acknowledgements, and conflicts.
3. Compile and visually inspect the sources in the current official OUP template.
4. Publish a Zenodo version whose notes match this freeze date and HER2ST `figure_data.json` hash.

Scientific risks remain explicit: HER2ST personalisation coverage is zero (fail-closed global default; not personalised superiority), LOOCV is editorially vulnerable and diagnostic-only, the diagnostic external panel is not a complete aligned SOTA comparison, and Wu remains a secondary oracle-K stress test only.

Run `python submission_freeze_v3/reproduce_submission_freeze.py --check` to verify the complete locked package.
