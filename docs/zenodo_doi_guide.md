# HistoWeave Zenodo DOI Minting Guide

This guide details the step-by-step process for obtaining a Zenodo DOI for the HistoWeave project by integrating with GitHub.

## Part 1: Zenodo-GitHub Integration Setup
1. Go to [Zenodo](https://zenodo.org) and log in (or create an account) using your GitHub OAuth.
2. Navigate to **Settings → GitHub**.
3. Locate the repository `HERRY423/Histoweave` and toggle the switch to **Enable** it. *(Screenshot description: Toggle switch next to repository name turns green)*
4. Once enabled, Zenodo will automatically create a DOI for each new GitHub release.

## Part 2: Prepare the Release
The repository is already configured with a `.zenodo.json` file containing the correct metadata. The target version for this release is `0.1.1`.

Before creating the release, ensure consistency across versioning files:
- **`CITATION.cff`**: Ensure the version matches (`0.1.1`) and `date-released` is correct (e.g., `2026-07-25`).
- **`pyproject.toml`**: Ensure the version is consistent (`0.1.1`).
- **`.zenodo.json`**: Ensure the version field is exactly `"0.1.1"`.

## Part 3: Create GitHub Release
First, tag the release locally and push to GitHub:
```bash
git tag -a v0.1.1 -m "HistoWeave v0.1.1: Bioinformatics submission freeze"
git push origin v0.1.1
```

Next, create the release on GitHub:
1. Go to the **GitHub Repository → Releases → Draft a new release**.
2. **Choose a tag**: Select the `v0.1.1` tag you just pushed.
3. **Release title**: "HistoWeave v0.1.1: Bioinformatics Submission Freeze"
4. **Description**: Include key highlights for this release (e.g., finalizing code for Bioinformatics journal submission).
5. Click **Publish release**.

## Part 4: After DOI is Minted
Once the release is published, Zenodo will archive it and mint a DOI. This may take a few moments.
1. Copy the new DOI from the Zenodo badge/page (format: `10.5281/zenodo.XXXXXXX`).
2. Update `CITATION.cff` at line 14: replace `# doi: 10.5281/zenodo.XXXXXXX` with your actual DOI `doi: 10.5281/zenodo.XXXXXXX`.
3. Update `DATA_CODE_AVAILABILITY.md` with the new DOI link.
4. Update the manuscript LaTeX source files with the new DOI.
5. Commit and push these documentation updates.

### Automated Update Script
To automate steps 2 and 3, you can use the provided helper script:
```bash
python scripts/update_zenodo_doi.py 10.5281/zenodo.1234567
```
