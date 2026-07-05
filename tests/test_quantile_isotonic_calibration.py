"""Regression tests for the frozen V3 quantile-isotonic calibration-only fit boundary."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pytest

from specsafe.traces import (
    QuantileIsotonicCalibrationFitError,
    QuantileIsotonicCalibrationViolationCode,
    fit_quantile_isotonic_calibration,
    load_calibration_redesign_v3_calibration_manifested_fixture_set,
    write_quantile_isotonic_calibration_fit,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v3"
)
OUTPUT_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "calibration"
    / "quantile-isotonic-calibration-v1"
)


def _copied_fixture_root(tmp_path: Path) -> Path:
    """Copy governed V3 inputs so fit tests never mutate committed evidence."""

    copied_root = tmp_path / "synthetic_calibration_redesign_v3"
    shutil.copytree(FIXTURE_ROOT, copied_root)
    return copied_root


def _manifested_fixture_set(tmp_path: Path):
    """Load one independently verified V3 calibration corpus for a fit test."""

    return load_calibration_redesign_v3_calibration_manifested_fixture_set(
        _copied_fixture_root(tmp_path)
    )


def test_fit_consumes_only_verified_v3_calibration_manifest(tmp_path: Path) -> None:
    result = fit_quantile_isotonic_calibration(_manifested_fixture_set(tmp_path))

    assert result.artifact.artifact_id == "quantile-isotonic-calibration-v1"
    assert result.artifact.fixture_set_id == "synthetic-calibration-redesign-v3"
    assert result.artifact.sample_count == 144
    assert result.artifact.positive_label_count == 76
    assert result.artifact.negative_label_count == 68
    assert result.artifact.quantile_group_count == 8
    assert result.artifact.equal_count_group_size == 18
    assert result.artifact.final_evaluation_accessed is False
    assert result.artifact.runtime_control_eligible is False
    assert result.report.fit_scope == "calibration_split_only"
    assert result.report.heldout_calibration_gate_status == "not_assessed"
    assert result.report.promotion_status == "not_assessed"


def test_artifact_transform_is_monotonic_finite_and_clamps_to_outer_quantiles(
    tmp_path: Path,
) -> None:
    artifact = fit_quantile_isotonic_calibration(_manifested_fixture_set(tmp_path)).artifact

    probabilities = (0.0, 0.1, 0.34, 0.55, 0.69, 0.77, 0.87, 1.0)
    calibrated = tuple(artifact.calibrate(probability) for probability in probabilities)

    assert all(math.isfinite(value) for value in calibrated)
    assert all(
        artifact.output_lower_bound <= value <= artifact.output_upper_bound
        for value in calibrated
    )
    assert all(left <= right for left, right in zip(calibrated, calibrated[1:]))
    assert calibrated[0] == artifact.bins[0].calibrated_confidence
    assert calibrated[-1] == artifact.bins[-1].calibrated_confidence
    with pytest.raises(QuantileIsotonicCalibrationFitError) as error:
        artifact.calibrate(-0.01)
    assert error.value.code is QuantileIsotonicCalibrationViolationCode.INVALID_RAW_CONFIDENCE


def test_weighted_pav_pools_the_last_two_monotonicity_violating_groups(tmp_path: Path) -> None:
    artifact = fit_quantile_isotonic_calibration(_manifested_fixture_set(tmp_path)).artifact

    assert tuple(bin_.pooled_block_index for bin_ in artifact.bins) == (1, 2, 3, 4, 5, 6, 7, 7)
    assert artifact.bins[6].calibrated_confidence == artifact.bins[7].calibrated_confidence
    assert artifact.raw_brier_score > artifact.calibrated_brier_score
    assert artifact.raw_ece_10_bin > artifact.calibrated_ece_10_bin


def test_writer_is_byte_deterministic_for_identical_verified_inputs(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"

    first = write_quantile_isotonic_calibration_fit(fixture_root, first_directory)
    second = write_quantile_isotonic_calibration_fit(fixture_root, second_directory)

    assert first == second
    assert (first_directory / "artifact.json").read_bytes() == (
        second_directory / "artifact.json"
    ).read_bytes()
    assert (first_directory / "fit_report.json").read_bytes() == (
        second_directory / "fit_report.json"
    ).read_bytes()


def test_fitter_rejects_foreign_objects_before_outcomes_are_read() -> None:
    class ForeignFixtureSet:
        @property
        def manifest(self) -> object:
            raise AssertionError("the fitter must reject foreign objects before reading manifests")

    with pytest.raises(QuantileIsotonicCalibrationFitError) as error:
        fit_quantile_isotonic_calibration(ForeignFixtureSet())  # type: ignore[arg-type]

    assert error.value.code is QuantileIsotonicCalibrationViolationCode.UNTRUSTED_FIXTURE_SET


def test_retained_evidence_contains_no_runtime_action_or_promotion_field(tmp_path: Path) -> None:
    output_directory = tmp_path / "evidence"
    write_quantile_isotonic_calibration_fit(_copied_fixture_root(tmp_path), output_directory)

    artifact_payload = json.loads((output_directory / "artifact.json").read_text(encoding="utf-8"))
    report_payload = json.loads((output_directory / "fit_report.json").read_text(encoding="utf-8"))
    prohibited_runtime_fields = {
        "verification_action",
        "scheduler_action",
        "policy_configuration",
        "capacity_action",
        "utility_score",
        "promotion_decision",
    }

    assert prohibited_runtime_fields.isdisjoint(artifact_payload)
    assert prohibited_runtime_fields.isdisjoint(report_payload)
    assert report_payload["promotion_status"] == "not_assessed"


def test_committed_evidence_matches_deterministic_rebuild(tmp_path: Path) -> None:
    rebuilt_directory = tmp_path / "rebuilt"
    write_quantile_isotonic_calibration_fit(_copied_fixture_root(tmp_path), rebuilt_directory)

    assert (OUTPUT_DIRECTORY / "artifact.json").read_bytes() == (
        rebuilt_directory / "artifact.json"
    ).read_bytes()
    assert (OUTPUT_DIRECTORY / "fit_report.json").read_bytes() == (
        rebuilt_directory / "fit_report.json"
    ).read_bytes()
