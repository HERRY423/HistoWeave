# HistoWeave v0.1.1 ? packaging hotfix

This release repairs the core runtime dependency contract discovered by a clean
install of the first public PyPI package.

## Fixed

- Declares `scikit-learn>=1.3` as a core dependency so `import histoweave` and
  the `histoweave` CLI work immediately after a standard installation.
- Adds a pre-upload release gate that installs the built wheel, runs
  `pip check`, imports the package, and executes `histoweave version`.
- Aligns citation and Zenodo metadata with
  `https://github.com/HERRY423/Histoweave`.

## Install

```bash
pip install --upgrade histoweave-spatial==0.1.1
histoweave version
```
