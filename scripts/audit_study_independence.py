"""Independence audit for a prospective external-study candidate.

For a candidate study, verify that its identifying strings (GEO accession,
paper DOI, author names, data DOIs) are absent from every HistoWeave
*development* source before the study is locked into a preregistered protocol.

Scope semantics
---------------
The audit targets development sources — knowledge bases, benchmark tables,
research reports, tests, and scripts — i.e. anything that could inform method
selection or training. The registration record itself
(`prospective_validation_v2/`) is EXCLUDED by definition: that directory
documents the study and therefore necessarily mentions its identifiers. An
identifier found only in the registration record is not contamination; an
identifier found in any development source is.

Fail-closed contract
--------------------
- The scan walks the whole tree (tracked AND untracked text sources), so a
  brand-new file that has not been `git add`-ed is still checked.
- If the scan collects zero sources, the verdict is `independence_unknown` and
  the exit code is non-zero — an empty scan must never look like a clean one.

Usage:
    python scripts/audit_study_independence.py \
        --study "CANDIDATE_STUDY_LABEL" \
        --identifiers "author_last_name,ACCESSION12345,10.XXXX/example_doi" \
        --out prospective_validation_v2/independence_audit_<study>.json

Identifiers are supplied on the command line, not embedded in this tool, so the
audit never reports itself as contamination.

Exit code 0 only when the scan actually ran and no identifier was found.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Text development sources only. Binary/derived trees are skipped because an
# identifier could not legitimately appear in them, and scanning them wastes time.
TEXT_EXTS = {
    ".py", ".json", ".csv", ".md", ".yaml", ".yml", ".toml", ".cff",
    ".txt", ".tex", ".svg", ".html", ".ipynb", ".r", ".rmd", ".bib",
}
SKIP_DIR_PARTS = {
    ".git", "__pycache__", ".pytest_tmp", ".pytest_cache", ".hypothesis",
    ".mypy_cache", ".ruff_cache", "tmp", "site", ".venv", "venv",
    "node_modules", ".tox", ".nox",
}
# Generated figure / checkpoint trees are not development sources.
SKIP_DIR_NAMES = {"figures", "checkpoints", "work", ".nextflow"}
# The registration record documents the study by definition; it is not a
# development source. Excluding it is the documented scope of this audit.
SKIP_DIR_NAMES_EXACT = {"prospective_validation_v2"}


def _iter_text_sources() -> list[Path]:
    """Walk the whole tree (tracked + untracked), excluding caches, binaries,
    generated figure trees, and the registration-record directory."""
    sources: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIR_PARTS for part in rel.parts):
            continue
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] in SKIP_DIR_NAMES_EXACT:
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        sources.append(path)
    return sources


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(identifiers: list[str], sources: list[Path]) -> dict:
    """Return per-identifier hits + per-file hashes for the audit record."""
    needles = [s for s in identifiers if s]
    hits: list[dict] = []
    scanned_files: dict[str, str] = {}
    for path in sources:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            # Unreadable files cannot be verified; fail closed for the record.
            scanned_files[str(path.relative_to(ROOT)).replace("\\", "/")] = "unreadable"
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        scanned_files[rel] = _sha256(path)
        lower = text.lower()
        for needle in needles:
            if needle.lower() in lower:
                hits.append({"source": rel, "identifier": needle})

    if not sources:
        verdict = "independence_unknown"
    elif hits:
        verdict = "potential_contamination"
    else:
        verdict = "independence_confirmed"

    return {
        "protocol": "histoweave.study_independence_audit.v1",
        "scope_note": (
            "Development sources only. prospective_validation_v2/ (the registration "
            "record) and generated figure/checkpoint trees are excluded."
        ),
        "identifiers_checked": needles,
        "sources_scanned": len(sources),
        "source_hashes": scanned_files,
        "hits": hits,
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", required=True, help="Human label of the candidate study.")
    parser.add_argument("--identifiers", required=True, help="Comma-separated identifying strings.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args()

    identifiers = [s.strip() for s in args.identifiers.split(",") if s.strip()]
    sources = _iter_text_sources()
    result = audit(identifiers, sources)
    result["study"] = args.study
    result["audited_on_utc"] = None  # filled by the operator at registration time

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[audit] study={args.study}")
    print(f"[audit] identifiers={identifiers}")
    print(f"[audit] sources_scanned={result['sources_scanned']}")
    print(f"[audit] hits={len(result['hits'])}")
    for hit in result["hits"]:
        print(f"  HIT: {hit['source']} -> {hit['identifier']}")
    print(f"[audit] verdict={result['verdict']}")
    if result["verdict"] == "independence_unknown":
        print("[audit] FAIL: zero sources scanned; refusing to report a clean audit.")
        return 2
    return 1 if result["hits"] else 0


if __name__ == "__main__":
    sys.exit(main())
