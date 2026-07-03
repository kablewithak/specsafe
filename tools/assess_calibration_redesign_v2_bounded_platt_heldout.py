"""Write the one read-only V2 held-out bounded-Platt assessment report."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces.bounded_platt_heldout_assessment import (
    write_bounded_platt_scaling_heldout_assessment,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _REPOSITORY_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"
_ARTIFACT_PATH = (
    _REPOSITORY_ROOT / "evidence" / "calibration" / "bounded-platt-scaling-v1" / "artifact.json"
)
_OUTPUT_PATH = (
    _REPOSITORY_ROOT
    / "evidence"
    / "calibration"
    / "bounded-platt-scaling-v1"
    / "heldout_assessment.json"
)


if __name__ == "__main__":
    result = write_bounded_platt_scaling_heldout_assessment(
        fixture_root=_FIXTURE_ROOT,
        artifact_path=_ARTIFACT_PATH,
        output_path=_OUTPUT_PATH,
    )
    print(
        "Wrote V2 held-out assessment: "
        f"status={result.status.value}; "
        f"promotion_decision={result.promotion_decision.value}"
    )
