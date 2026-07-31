# HistoWeave P1 manuscript package

The canonical review files are:

- `main.tex` — format-free Bioinformatics Original Paper review manuscript
- `supplementary.tex` — methods, full tables, audit corpus, and reproduction details
- `cover_letter.md` — cover-letter draft
- `SUBMISSION_COMPLIANCE.md` — dated journal-rule audit and blockers
- `AUTHOR_METADATA_REQUIRED.md` — fields that only the authors can supply
- `make_submission_assets.py` — deterministic figure and graphical-abstract builder
- `figures/` — SVG, PNG, and TIFF submission artwork

Regenerate and verify:

```powershell
python manuscript\make_submission_assets.py
python submission_freeze_v3\reproduce_submission_freeze.py --check
```

The repository does not currently contain a LaTeX engine, so P1 performs
static TeX validation and artifact checks locally. Compile the source in the
official OUP/Overleaf environment before upload.

The file `bioinfo.cls` is a legacy drafting stub and is not used by P1.
Initial submission is format-free under the current journal guidance; if a
revision is requested, migrate the verified text and figures into the current
official OUP LaTeX template.

**Do not submit until every blocker in `SUBMISSION_COMPLIANCE.md` is resolved.**
