"""Update only the HistoWeave software DOI in submission metadata.

Atomic: every substitution is staged in memory first; files are written only
when ALL markers resolve exactly once. A failed pattern leaves the tree
untouched, so a mid-run crash cannot partially mutate CITATION.cff or the
submission documents.

The LaTeX DOI/Archive DOI markers currently live in the archived P0 source
(`manuscript/main_p0_archive.tex`), not the live review manuscript
(`manuscript/main.tex`). The script searches both candidates for each marker and
warns when the live manuscript has no markers, so a future move of the markers
does not silently break the update.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

_LOGGER = logging.getLogger(__name__)
_DOI_PATTERN = re.compile(r"10\.5281/zenodo\.[0-9]+")


def _apply_once(text: str, pattern: str, replacement: str) -> tuple[str, int]:
    """Apply one regex on text normalised to LF so `^`/`$` anchors are CRLF-safe."""
    normalised = text.replace("\r\n", "\n")
    updated, count = re.subn(
        pattern, lambda _match: replacement, normalised, count=1, flags=re.MULTILINE
    )
    if count == 1 and "\r\n" in text:
        updated = updated.replace("\n", "\r\n")
    return updated, count


def _stage(path: Path, pattern: str, replacement: str, staged: list[tuple[Path, bytes]]) -> None:
    """Apply one regex on a file; stage the new bytes without writing."""
    raw = path.read_bytes()
    updated, count = _apply_once(raw.decode("utf-8"), pattern, replacement)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one marker in {path.relative_to(Path(__file__).resolve().parents[1])}"
        )
    staged.append((path, updated.encode("utf-8")))


def update_doi(new_doi: str) -> None:
    """Replace software DOI markers without touching third-party dataset DOIs."""
    if _DOI_PATTERN.fullmatch(new_doi) is None:
        raise ValueError("DOI must match 10.5281/zenodo.<digits>")

    project_root = Path(__file__).resolve().parents[1]
    citation_file = project_root / "CITATION.cff"
    data_code_file = project_root / "submission_freeze_v1" / "DATA_CODE_AVAILABILITY.md"
    manuscript_candidates = [
        project_root / "manuscript" / "main.tex",
        project_root / "manuscript" / "main_p0_archive.tex",
    ]

    staged: list[tuple[Path, bytes]] = []
    _stage(citation_file, r"^doi:\s*10\.5281/zenodo\.[0-9]+$", f"doi: {new_doi}", staged)
    _stage(
        data_code_file,
        r"^- Software archive DOI:\s*10\.5281/zenodo\.[0-9]+$",
        f"- Software archive DOI: {new_doi}",
        staged,
    )

    doi_marker_patterns = [
        (r"^DOI:\s*\\url\{https://doi\.org/10\.5281/zenodo\.[0-9]+\}$",
         rf"DOI: \url{{https://doi.org/{new_doi}}}"),
        (r"^Archive DOI:\s*\\url\{https://doi\.org/10\.5281/zenodo\.[0-9]+\}$",
         rf"Archive DOI: \url{{https://doi.org/{new_doi}}}"),
    ]

    # Group manuscript patterns by file so multiple patterns on one file combine.
    manuscript_tasks: dict[Path, list[tuple[str, str]]] = {}
    for pattern, replacement in doi_marker_patterns:
        matched = False
        for candidate in manuscript_candidates:
            if not candidate.is_file():
                continue
            text = candidate.read_bytes().decode("utf-8").replace("\r\n", "\n")
            count = len(re.findall(pattern, text, flags=re.MULTILINE))
            if count == 1:
                manuscript_tasks.setdefault(candidate, []).append((pattern, replacement))
                matched = True
                break
        if not matched:
            raise RuntimeError("No exactly-one DOI marker found in any manuscript candidate")

    for path, tasks in manuscript_tasks.items():
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        for pattern, replacement in tasks:
            text, count = _apply_once(text, pattern, replacement)
            if count != 1:
                raise RuntimeError(f"Marker disappeared while staging {path.name}")
        staged.append((path, text.encode("utf-8")))

    if manuscript_candidates[0] not in manuscript_tasks:
        _LOGGER.warning(
            "Live manuscript/main.tex has no software-DOI markers; updated the archived "
            "P0 source instead."
        )

    # All patterns resolved: write everything atomically.
    for path, content in staged:
        path.write_bytes(content)
        _LOGGER.info("[OK] Updated %s", path.name)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        _LOGGER.error("Usage: python update_zenodo_doi.py <DOI>")
        _LOGGER.error("Example: python update_zenodo_doi.py 10.5281/zenodo.1234567")
        return 1
    update_doi(args[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
