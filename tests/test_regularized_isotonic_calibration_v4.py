"""Regression tests for the frozen V4 regularized-isotonic calibration fit boundary."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pytest

from specsafe.traces.regularized_isotonic_calibration_v4 import (
    RegularizedIsotonicCalibrationV4FitError,
    RegularizedIsotonicCalibrationV4ViolationCode,
    fit_regularized_isotonic_calibration_v4,
    load_regularized_isotonic_calibration_v4_fit_result,
    load_regularized_isotonic_calibration_v4_fixture_set,
    write_regularized_isotonic_calibration_v4_fit,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_OUTPUT_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "calibration"
    / "regularized-isotonic-calibration-v4"
)


def _copied_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def _fixture_set(tmp_path: Path):
    return load_regularized_isotonic_calibration_v4_fixture_set(
        _copied_fixture_root(tmp_path)
    )


def test_fit_consumes_only_the_verified_v4_calibration_manifest(tmp_path: Path) -> None:
    result = fit_regularized_isotonic_calibration_v4(_fixture_set(tmp_path))

    assert result.artifact.artifact_id == "regularized-isotonic-calibration-v4"
    assert result.artifact.fixture_set_id == "synthetic-calibration-redesign-v4"
    assert result.artifact.sample_count == 192
    assert result.artifact.positive_label_count == 97
    assert result.artifact.negative_label_count == 95
    assert result.artifact.equal_count_group_count == 12
    assert result.artifact.equal_count_group_size == 16
    assert result.artifact.final_evaluation_accessed is False
    assert result.artifact.calibration_refit_performed is False
    assert result.artifact.scheduler_or_policy_execution_performed is False
    assert result.artifact.runtime_control_eligible is False
    assert result.report.fit_scope == "calibration_split_only"
    assert result.report.heldout_calibration_gate_status == "not_assessed"
    assert result.report.policy_comparison_status == "not_started"


def test_artifact_transform_is_monotonic_finite_and_clamps_to_outer_groups(
    tmp_path: Path,
) -> None:
    artifact = fit_regularized_isotonic_calibration_v4(_fixture_set(tmp_path)).artifact

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
    with pytest.raises(RegularizedIsotonicCalibrationV4FitError) as error:
        artifact.calibrate(-0.01)
    assert error.value.code is RegularizedIsotonicCalibrationV4ViolationCode.INVALID_RAW_CONFIDENCE


def test_weighted_pav_pools_known_v4_monotonicity_violations(tmp_path: Path) -> None:
    artifact = fit_regularized_isotonic_calibration_v4(_fixture_set(tmp_path)).artifact

    assert tuple(bin_.pooled_block_index for bin_ in artifact.bins) == (
        1,
        2,
        2,
        3,
        4,
        4,
        4,
        5,
        6,
        7,
        8,
        9,
    )
    assert artifact.bins[4].calibrated_confidence == artifact.bins[5].calibrated_confidence
    assert artifact.bins[5].calibrated_confidence == artifact.bins[6].calibrated_confidence
    assert artifact.raw_brier_score > artifact.calibrated_brier_score
    assert artifact.raw_ece_10_bin > artifact.calibrated_ece_10_bin


def test_writer_is_byte_deterministic_for_identical_verified_inputs(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"

    first = write_regularized_isotonic_calibration_v4_fit(fixture_root, first_directory)
    second = write_regularized_isotonic_calibration_v4_fit(fixture_root, second_directory)

    assert first == second
    assert (first_directory / "artifact.json").read_bytes() == (
        second_directory / "artifact.json"
    ).read_bytes()
    assert (first_directory / "fit_report.json").read_bytes() == (
        second_directory / "fit_report.json"
    ).read_bytes()


def test_writer_is_write_once_for_the_same_evidence_directory(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    output_directory = tmp_path / "evidence"
    write_regularized_isotonic_calibration_v4_fit(fixture_root, output_directory)

    with pytest.raises(RegularizedIsotonicCalibrationV4FitError) as error:
        write_regularized_isotonic_calibration_v4_fit(fixture_root, output_directory)

    expected_code = RegularizedIsotonicCalibrationV4ViolationCode.DESTINATION_ALREADY_EXISTS
    assert error.value.code is expected_code


def test_fitter_rejects_foreign_objects_before_evidence_is_read() -> None:
    class ForeignFixtureSet:
        @property
        def manifest(self) -> object:
            raise AssertionError("the fitter must reject foreign objects before reading manifests")

    with pytest.raises(RegularizedIsotonicCalibrationV4FitError) as error:
        fit_regularized_isotonic_calibration_v4(ForeignFixtureSet())  # type: ignore[arg-type]

    assert error.value.code is RegularizedIsotonicCalibrationV4ViolationCode.UNTRUSTED_FIXTURE_SET


def test_tampered_calibration_asset_is_rejected_before_fit(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    path = fixture_root / "inputs" / "cases" / "CRV4-101.json"
    path.write_bytes(path.read_bytes() + b" ")

    with pytest.raises(RegularizedIsotonicCalibrationV4FitError) as error:
        load_regularized_isotonic_calibration_v4_fixture_set(fixture_root)

    expected_code = RegularizedIsotonicCalibrationV4ViolationCode.MANIFEST_PROVENANCE_FAILURE
    assert error.value.code is expected_code


def test_retained_evidence_contains_no_runtime_action_or_promotion_field(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "evidence"
    write_regularized_isotonic_calibration_v4_fit(
        _copied_fixture_root(tmp_path),
        output_directory,
    )

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
    assert report_payload["heldout_calibration_gate_status"] == "not_assessed"
    assert report_payload["policy_comparison_status"] == "not_started"



def test_committed_fit_evidence_loads_only_when_registry_hashes_match() -> None:
    result = load_regularized_isotonic_calibration_v4_fit_result(
        _FIXTURE_ROOT,
        _OUTPUT_DIRECTORY,
    )

    assert result.artifact.artifact_id == "regularized-isotonic-calibration-v4"
    assert result.report.pooled_block_count == 9
    assert result.report.heldout_calibration_gate_status == "not_assessed"


def test_committed_fit_evidence_rejects_one_byte_artifact_change(tmp_path: Path) -> None:
    output_directory = tmp_path / "evidence"
    shutil.copytree(_OUTPUT_DIRECTORY, output_directory)
    artifact_path = output_directory / "artifact.json"
    artifact_path.write_bytes(artifact_path.read_bytes() + b" ")

    with pytest.raises(RegularizedIsotonicCalibrationV4FitError) as error:
        load_regularized_isotonic_calibration_v4_fit_result(
            _FIXTURE_ROOT,
            output_directory,
        )

    expected_code = RegularizedIsotonicCalibrationV4ViolationCode.FIT_EVIDENCE_HASH_MISMATCH
    assert error.value.code is expected_code

def test_committed_evidence_matches_deterministic_rebuild(tmp_path: Path) -> None:
    rebuilt_directory = tmp_path / "rebuilt"
    write_regularized_isotonic_calibration_v4_fit(
        _copied_fixture_root(tmp_path),
        rebuilt_directory,
    )

    assert (_OUTPUT_DIRECTORY / "artifact.json").read_bytes() == (
        rebuilt_directory / "artifact.json"
    ).read_bytes()
    assert (_OUTPUT_DIRECTORY / "fit_report.json").read_bytes() == (
        rebuilt_directory / "fit_report.json"
    ).read_bytes()
