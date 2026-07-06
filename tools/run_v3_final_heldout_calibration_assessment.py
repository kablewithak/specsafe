"""Run the governed one-time V3 final held-out calibration assessment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from specsafe.heldout_calibration.v3_final_assessment import (
    V3FinalHeldOutCalibrationAssessmentError,
    run_v3_final_heldout_calibration_assessment_once,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_FIXTURE_ROOT = (
    _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
)
_DEFAULT_OUTPUT = (
    _PROJECT_ROOT
    / "evidence"
    / "heldout-calibration"
    / "v3-final-heldout-calibration-assessment-v1"
    / "result.json"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Score the frozen V3 final corpus once using the frozen "
            "quantile-isotonic calibration artifact."
        )
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=_DEFAULT_FIXTURE_ROOT,
        help="Frozen V3 fixture root. Defaults to the repository V3 fixture directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help=(
            "Write-once JSON evidence destination. The command refuses to overwrite "
            "an existing file."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result, output_path = run_v3_final_heldout_calibration_assessment_once(
            args.fixture_root,
            args.output,
        )
    except V3FinalHeldOutCalibrationAssessmentError as error:
        print(f"{error.code}: {error}", file=sys.stderr)
        return 1

    print(f"V3 final held-out assessment written: {output_path}")
    print(f"status={result.status}")
    print(f"brier_score_improvement={result.brier_score_improvement:.12f}")
    print(
        "expected_calibration_error_improvement="
        f"{result.expected_calibration_error_improvement:.12f}"
    )
    print(
        "adaptive_policy_research_eligibility="
        f"{result.adaptive_policy_research_eligibility}"
    )
    print("runtime_control_eligible=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
