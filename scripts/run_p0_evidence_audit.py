#!/usr/bin/env python
"""Run the frozen P0 adversarial evidence-admission audit."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from histoweave.benchmark.evidence_audit import run_evidence_admission_audit  # noqa: E402

_LOGGER = logging.getLogger(__name__)
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "p0_validation_results" / "evidence_admission",
    )
    args = parser.parse_args()
    summary = run_evidence_admission_audit(args.out_dir)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    _LOGGER.info("%s", json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
