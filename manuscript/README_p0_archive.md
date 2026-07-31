# HistoWeave Manuscript

Bioinformatics Original Paper submission materials.

## Files

| File | Description |
|------|-------------|
| `main.tex` | Main manuscript (LaTeX, bioinfo class) |
| `supplementary.tex` | Supplementary tables S1–S7 and reproducibility note |
| `bioinfo.cls` | Minimal class stub (replace with official OUP template for submission) |
| `Makefile` | Build instructions |

## Compilation

```bash
# Using the stub class (for drafting)
pdflatex main.tex
pdflatex supplementary.tex

# For final submission, download the official bioinfo.cls from:
# https://academic.oup.com/bioinformatics/pages/submission_online
```

## Before Submission Checklist

- [ ] Replace author placeholder names and affiliations
- [ ] Add corresponding author email
- [ ] Replace `bioinfo.cls` stub with official OUP template
- [ ] Insert Zenodo DOI (see `docs/zenodo_doi_guide.md`)
- [ ] Add funding information
- [ ] Add acknowledgements
- [ ] Review AI assistance disclosure
- [ ] Verify all figures are publication-ready (300 DPI, colorblind-friendly)
- [ ] Copy frozen figures from `benchmark_external_validation/figures/` into this directory
- [ ] Run `python submission_freeze_v2/reproduce_submission_freeze.py --check` to verify the P0 freeze

## Figures

The five legacy main figures remain locked in `submission_freeze_v1/main_figures.lock.json` and are referenced by the v2 freeze:

1. **Figure 1**: External spatial-domain performance heatmap (5 datasets × 15 methods)
2. **Figure 2**: Method ARI distribution across datasets and seeds
3. **Figure 3**: Dataset-feature landscape embedding
4. **Figure 4**: Recommender regret vs. global-best and random baselines
5. **Figure 5**: Selective regret-coverage (abstention prevents higher-regret personalisation)

Source: `benchmark_external_validation/figures/` (SVG + PNG)
