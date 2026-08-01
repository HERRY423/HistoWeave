"""Independent installability / import smoke for submission packages.

These tests intentionally avoid heavy data downloads. They verify that a
standard environment can import the decision protocol, construct a
DecisionCard, and expose the CLI entrypoint.
"""

from __future__ import annotations

import subprocess
import sys

from histoweave.benchmark import (
    DecisionAction,
    DecisionPolicy,
    MethodScore,
    Recommendation,
    build_decision_card,
)


def test_import_decision_surface() -> None:
    from histoweave import DecisionPolicy as PublicPolicy
    from histoweave.benchmark.decision import DecisionCard

    assert PublicPolicy is DecisionPolicy
    assert DecisionCard is not None


def test_decision_card_smoke_evidence_required_without_holdout_pack() -> None:
    """With default policy and no validation pack, local advantage → evidence_required."""
    rec = Recommendation(
        task="spatial_domain",
        dataset_name="smoke_query",
        ranked_methods=[
            MethodScore(
                method="local@sw0.8",
                score=0.82,
                confidence=0.80,
                wins=2,
                neighbour_scores={"a": 0.8, "b": 0.84},
                uncertainty=0.02,
                support=2,
                coverage=1.0,
            ),
            MethodScore(
                method="global_method",
                score=0.70,
                confidence=0.50,
                wins=0,
                neighbour_scores={"a": 0.7, "b": 0.7},
                uncertainty=0.02,
                support=2,
                coverage=1.0,
            ),
        ],
        neighbours=[
            {
                "name": "a",
                "similarity": 0.9,
                "task": "spatial_domain",
                "ground_truth_kind": "spatial_domain",
                "k_policy": "estimate",
                "oracle_k": False,
            },
            {
                "name": "b",
                "similarity": 0.8,
                "task": "spatial_domain",
                "ground_truth_kind": "spatial_domain",
                "k_policy": "estimate",
                "oracle_k": False,
            },
        ],
        global_best_method="global_method",
        beats_global_best_baseline=True,
        evidence_contract={
            "task": "spatial_domain",
            "ground_truth_kind": "spatial_domain",
            "k_policy": "estimate",
            "metric": "ari",
            "higher_is_better": True,
            "method_panel": ["local@sw0.8", "global_method"],
        },
    )
    card = build_decision_card(rec, policy=DecisionPolicy())
    assert card.action is DecisionAction.EVIDENCE_REQUIRED


def test_cli_entrypoint_help() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "histoweave", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "histoweave" in (proc.stdout + proc.stderr).lower()
