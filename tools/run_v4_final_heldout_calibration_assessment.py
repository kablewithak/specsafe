"""Run the one permitted V4 held-out calibration assessment."""

from __future__ import annotations

from pathlib import Path

from specsafe.heldout_calibration.v4_final_assessment_runner import (
    run_v4_final_heldout_calibration_assessment_once,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = (
    _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v4"
)
_DESTINATION = (
    _PROJECT_ROOT
    / "evidence"
    / "heldout-calibration"
    / "v4-final-heldout-calibration-assessment-v1"
    / "result.json"
)


def main() -> None:
    """Persist one frozen V4 held-out assessment and print its governed gate result."""

    result, destination = run_v4_final_heldout_calibration_assessment_once(
        _FIXTURE_ROOT,
        _DESTINATION,
    )
    print("V4 final held-out calibration assessment: COMPLETE")
    print(f"Result: {destination}")
    print(f"Status: {result.status.value}")
    print(f"Brier improvement: {result.brier_score_improvement:.12f}")
    print(f"ECE improvement: {result.ece_10_bin_improvement:.12f}")
    print(f"AUROC delta: {result.auroc_delta:.12f}")
    print(f"Policy research eligibility: {result.adaptive_policy_research_eligibility.value}")


if __name__ == "__main__":
    main()
