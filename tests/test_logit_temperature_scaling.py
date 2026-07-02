"""Regression tests for the calibration-only logit-temperature-scaling boundary."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pytest

from specsafe.traces import (
    CalibrationRedesignManifestedFixtureSet,
    LogitTemperatureScalingFitError,
    LogitTemperatureScalingViolationCode,
    build_calibration_redesign_manifest,
    fit_logit_temperature_scaling,
    load_calibration_redesign_manifested_fixture_set,
    write_logit_temperature_scaling_fit,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign"
)


def _copied_fixture_root(tmp_path: Path) -> Path:
    """Copy governed inputs so fitting tests never mutate committed fixture evidence."""

    copied_root = tmp_path / "synthetic_calibration_redesign"
    shutil.copytree(FIXTURE_ROOT, copied_root)
    return copied_root


def _manifested_fixture_set(tmp_path: Path) -> CalibrationRedesignManifestedFixtureSet:
    """Build and load one isolated immutable calibration fixture set for a test."""

    fixture_root = _copied_fixture_root(tmp_path)
    build_calibration_redesign_manifest(fixture_root)
    return load_calibration_redesign_manifested_fixture_set(fixture_root)


def test_fit_consumes_only_verified_calibration_manifest(tmp_path: Path) -> None:
    fixture_set = _manifested_fixture_set(tmp_path)

    result = fit_logit_temperature_scaling(fixture_set)

    assert result.artifact.artifact_id == "logit-temperature-scaling-v1"
    assert result.artifact.fixture_set_id == "synthetic-calibration-redesign-v1"
    assert result.artifact.sample_count == 24
    assert result.artifact.positive_label_count > 0
    assert result.artifact.negative_label_count > 0
    assert result.artifact.final_evaluation_accessed is False
    assert result.artifact.runtime_control_eligible is False
    assert result.report.fit_scope == "calibration_split_only"
    assert result.report.promotion_status == "not_assessed"
    assert result.artifact.calibrated_negative_log_likelihood <= (
        result.artifact.raw_negative_log_likelihood + 1e-12
    )


def test_fitter_rejects_untrusted_object() -> None:
    with pytest.raises(LogitTemperatureScalingFitError) as error:
        fit_logit_temperature_scaling(object())  # type: ignore[arg-type]

    assert error.value.code is LogitTemperatureScalingViolationCode.UNTRUSTED_FIXTURE_SET


def test_fitter_rejects_manifest_case_count_mismatch(tmp_path: Path) -> None:
    fixture_set = _manifested_fixture_set(tmp_path)
    invalid_manifest = fixture_set.manifest.model_copy(
        update={"case_count": fixture_set.manifest.case_count + 1}
    )
    invalid_fixture_set = fixture_set.model_copy(update={"manifest": invalid_manifest})

    with pytest.raises(LogitTemperatureScalingFitError) as error:
        fit_logit_temperature_scaling(invalid_fixture_set)

    assert error.value.code is LogitTemperatureScalingViolationCode.UNTRUSTED_FIXTURE_SET


def test_artifact_calibration_is_monotonic_and_finite(tmp_path: Path) -> None:
    artifact = fit_logit_temperature_scaling(_manifested_fixture_set(tmp_path)).artifact

    probabilities = (0.0, 0.2, 0.5, 0.8, 1.0)
    calibrated = tuple(artifact.calibrate(probability) for probability in probabilities)

    assert all(math.isfinite(value) for value in calibrated)
    assert all(left <= right for left, right in zip(calibrated, calibrated[1:]))
    assert all(0.0 < value < 1.0 for value in calibrated)


def test_writer_retains_artifact_and_non_promotion_report(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    build_calibration_redesign_manifest(fixture_root)
    output_directory = tmp_path / "evidence"

    result = write_logit_temperature_scaling_fit(fixture_root, output_directory)

    artifact_payload = json.loads((output_directory / "artifact.json").read_text(encoding="utf-8"))
    report_payload = json.loads((output_directory / "fit_report.json").read_text(encoding="utf-8"))
    assert artifact_payload["artifact_id"] == result.artifact.artifact_id
    assert artifact_payload["final_evaluation_accessed"] is False
    assert report_payload["promotion_status"] == "not_assessed"
    assert report_payload["runtime_control_eligible"] is False
