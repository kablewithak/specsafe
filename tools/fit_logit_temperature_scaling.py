"""Fit the predeclared calibration-only logit-temperature-scaling artifact."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces import write_logit_temperature_scaling_fit

FIXTURE_ROOT = Path("data/fixtures/synthetic_calibration_redesign")
OUTPUT_DIRECTORY = Path("evidence/calibration/logit-temperature-scaling-v1")


def main() -> None:
    """Fit from the immutable calibration manifest and write retained non-promotion evidence."""

    result = write_logit_temperature_scaling_fit(FIXTURE_ROOT, OUTPUT_DIRECTORY)
    print(f"Wrote calibration artifact: {OUTPUT_DIRECTORY / 'artifact.json'}")
    print(f"Wrote calibration fit report: {OUTPUT_DIRECTORY / 'fit_report.json'}")
    print(f"Temperature: {result.artifact.temperature:.12f}")


if __name__ == "__main__":
    main()
