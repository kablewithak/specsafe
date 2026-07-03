"""Regression tests for the frozen V2 calibration-only bounded-Platt fit boundary."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pytest

from specsafe.traces import (
    BoundedPlattScalingFitError,
    BoundedPlattScalingViolationCode,
    fit_bounded_platt_scaling,
    load_calibration_redesign_v2_calibration_manifested_fixture_set,
    project_bounded_platt_parameters,
    write_bounded_platt_scaling_fit,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_redesign_v2"
)


def _copied_fixture_root(tmp_path: Path) -> Path:
    """Copy governed inputs so fit tests never mutate committed V2 evidence."""

    copied_root = tmp_path / "synthetic_calibration_redesign_v2"
    shutil.copytree(FIXTURE_ROOT, copied_root)
    return copied_root


def _manifested_fixture_set(tmp_path: Path):
    """Load one independently verified V2 calibration corpus for a fit test."""

    return load_calibration_redesign_v2_calibration_manifested_fixture_set(
        _copied_fixture_root(tmp_path)
    )


def test_fit_consumes_only_verified_v2_calibration_manifest(tmp_path: Path) -> None:
    result = fit_bounded_platt_scaling(_manifested_fixture_set(tmp_path))

    assert result.artifact.artifact_id == "bounded-platt-scaling-v1"
    assert result.artifact.fixture_set_id == "synthetic-calibration-redesign-v2"
    assert result.artifact.sample_count == 48
    assert result.artifact.positive_label_count > 0
    assert result.artifact.negative_label_count > 0
    assert result.artifact.final_evaluation_accessed is False
    assert result.artifact.runtime_control_eligible is False
    assert result.report.fit_scope == "calibration_split_only"
    assert result.report.promotion_status == "not_assessed"
    assert result.report.failure_status == "none"


def test_artifact_transform_is_monotonic_finite_and_clips_zero_and_one(tmp_path: Path) -> None:
    artifact = fit_bounded_platt_scaling(_manifested_fixture_set(tmp_path)).artifact

    probabilities = (0.0, 0.000001, 0.2, 0.5, 0.8, 0.999999, 1.0)
    calibrated = tuple(artifact.calibrate(probability) for probability in probabilities)

    assert all(math.isfinite(value) for value in calibrated)
    assert all(0.0 < value < 1.0 for value in calibrated)
    assert all(left <= right for left, right in zip(calibrated, calibrated[1:]))
    assert calibrated[0] == calibrated[1]
    assert calibrated[-2] == calibrated[-1]


def test_projection_keeps_parameters_inside_predeclared_bounds() -> None:
    projected = project_bounded_platt_parameters(slope=-10.0, intercept=10.0)

    assert projected == (0.25, 4.0)


def test_writer_is_byte_deterministic_for_identical_verified_inputs(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"

    first = write_bounded_platt_scaling_fit(fixture_root, first_directory)
    second = write_bounded_platt_scaling_fit(fixture_root, second_directory)

    assert first == second
    assert (first_directory / "artifact.json").read_bytes() == (
        second_directory / "artifact.json"
    ).read_bytes()
    assert (first_directory / "fit_report.json").read_bytes() == (
        second_directory / "fit_report.json"
    ).read_bytes()


def test_fitter_rejects_final_like_or_v1_objects_before_outcomes_are_read() -> None:
    class FinalLikeFixtureSet:
        @property
        def manifest(self) -> object:
            raise AssertionError("the fitter must reject foreign objects before reading manifests")

    with pytest.raises(BoundedPlattScalingFitError) as error:
        fit_bounded_platt_scaling(FinalLikeFixtureSet())  # type: ignore[arg-type]

    assert error.value.code is BoundedPlattScalingViolationCode.UNTRUSTED_FIXTURE_SET


def test_retained_evidence_contains_no_runtime_action_or_promotion_field(tmp_path: Path) -> None:
    output_directory = tmp_path / "evidence"
    write_bounded_platt_scaling_fit(_copied_fixture_root(tmp_path), output_directory)

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


def test_writer_emits_lf_evidence_bytes_on_every_platform(tmp_path: Path) -> None:
    """Prevent platform newline conversion from changing retained evidence bytes.

    Do not monkeypatch ``Path.write_text`` globally here: pytest's cache provider uses that
    method while the test is active. The retained byte assertion is the boundary that matters.
    """

    output_directory = tmp_path / "evidence"

    write_bounded_platt_scaling_fit(_copied_fixture_root(tmp_path), output_directory)

    for filename in ("artifact.json", "fit_report.json"):
        evidence_bytes = (output_directory / filename).read_bytes()
        assert evidence_bytes.endswith(b"\n")
        assert b"\r\n" not in evidence_bytes


def test_committed_evidence_matches_deterministic_rebuild(tmp_path: Path) -> None:
    rebuilt_directory = tmp_path / "rebuilt"
    write_bounded_platt_scaling_fit(_copied_fixture_root(tmp_path), rebuilt_directory)
    committed_directory = (
        Path(__file__).resolve().parents[1]
        / "evidence"
        / "calibration"
        / "bounded-platt-scaling-v1"
    )

    assert (committed_directory / "artifact.json").read_bytes() == (
        rebuilt_directory / "artifact.json"
    ).read_bytes()
    assert (committed_directory / "fit_report.json").read_bytes() == (
        rebuilt_directory / "fit_report.json"
    ).read_bytes()
