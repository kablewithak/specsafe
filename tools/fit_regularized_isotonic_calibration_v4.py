"""Write the deterministic V4 regularized-isotonic calibration evidence once."""

from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.traces.regularized_isotonic_calibration_v4 import (
    RegularizedIsotonicCalibrationV4FitError,
    write_regularized_isotonic_calibration_v4_fit,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write V4 regularized-isotonic calibration evidence exactly once."
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=Path("data/fixtures/synthetic_calibration_redesign_v4"),
        help="Path to the V4 frozen calibration fixture root.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("evidence/calibration/regularized-isotonic-calibration-v4"),
        help="Directory for immutable V4 calibration artifact and fit report JSON.",
    )
    arguments = parser.parse_args()

    try:
        result = write_regularized_isotonic_calibration_v4_fit(
            arguments.fixture_root.resolve(),
            arguments.output_directory.resolve(),
        )
    except RegularizedIsotonicCalibrationV4FitError as error:
        raise SystemExit(f"Stop: V4 regularized-isotonic fit failed: {error}") from error

    artifact = result.artifact
    report = result.report
    print("V4 regularized-isotonic calibration fit: PASS")
    print(f"Artifact: {(arguments.output_directory / 'artifact.json').as_posix()}")
    print(f"Fit report: {(arguments.output_directory / 'fit_report.json').as_posix()}")
    print(f"Samples: {artifact.sample_count}")
    print(f"Positive labels: {artifact.positive_label_count}")
    print(f"Negative labels: {artifact.negative_label_count}")
    print(f"Pooled blocks: {report.pooled_block_count}")
    print(f"Fit-data Brier improvement: {report.brier_score_improvement_on_fit_data:.12f}")
    print(f"Fit-data ECE improvement: {report.ece_10_bin_improvement_on_fit_data:.12f}")
    print(f"Fit-data AUROC delta: {report.auroc_delta_on_fit_data:.12f}")
    print("Held-out calibration gate: not assessed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
