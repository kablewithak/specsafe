"""Write the frozen V2 bounded-Platt calibration artifact and fit report."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces import write_bounded_platt_scaling_fit

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPOSITORY_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"
OUTPUT_DIRECTORY = REPOSITORY_ROOT / "evidence" / "calibration" / "bounded-platt-scaling-v1"


if __name__ == "__main__":
    write_bounded_platt_scaling_fit(FIXTURE_ROOT, OUTPUT_DIRECTORY)
