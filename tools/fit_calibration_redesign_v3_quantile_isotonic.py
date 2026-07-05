"""Write the deterministic V3 calibration-only quantile-isotonic fit evidence."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces.quantile_isotonic_calibration import write_quantile_isotonic_calibration_fit

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPOSITORY_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
OUTPUT_DIRECTORY = REPOSITORY_ROOT / "evidence" / "calibration" / "quantile-isotonic-calibration-v1"


if __name__ == "__main__":
    write_quantile_isotonic_calibration_fit(FIXTURE_ROOT, OUTPUT_DIRECTORY)
