"""Regression tests for the one read-only V2 bounded-Platt held-out assessment."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from specsafe.traces import (
    BoundedPlattHeldOutAssessmentError,
    BoundedPlattHeldOutAssessmentStatus,
    BoundedPlattHeldOutAssessmentViolationCode,
    BoundedPlattHeldOutPromotionDecision,
    assess_bounded_platt_scaling_heldout,
    load_bounded_platt_scaling_artifact,
    load_calibration_redesign_v2_final_evaluation_manifested_fixture_set,
    write_bounded_platt_scaling_heldout_assessment,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_redesign_v2"
)
ARTIFACT_PATH = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "calibration"
    / "bounded-platt-scaling-v1"
    / "artifact.json"
)
COMMITTED_ASSESSMENT_PATH = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "calibration"
    / "bounded-platt-scaling-v1"
    / "heldout_assessment.json"
)


def _copied_fixture_root(tmp_path: Path) -> Path:
    """Copy final evidence so assessment tests never mutate committed fixture bytes."""

    copied_root = tmp_path / "synthetic_calibration_redesign_v2"
    shutil.copytree(FIXTURE_ROOT, copied_root)
    return copied_root


def _assessment_inputs(tmp_path: Path):
    """Load one verified final corpus and frozen artifact for a test-only assessment."""

    fixture_set = load_calibration_redesign_v2_final_evaluation_manifested_fixture_set(
        _copied_fixture_root(tmp_path)
    )
    return fixture_set, load_bounded_platt_scaling_artifact(ARTIFACT_PATH)


def test_assessment_retains_the_predeclared_v2_negative_result(tmp_path: Path) -> None:
    fixture_set, (artifact, artifact_sha256, artifact_byte_count) = _assessment_inputs(tmp_path)

    result = assess_bounded_platt_scaling_heldout(
        fixture_set,
        artifact,
        artifact_sha256=artifact_sha256,
        artifact_byte_count=artifact_byte_count,
    )

    assert result.observation_count == 36
    assert result.status is BoundedPlattHeldOutAssessmentStatus.CALIBRATOR_REGRESSION
    assert (
        result.promotion_decision
        is BoundedPlattHeldOutPromotionDecision.NOT_PROMOTED_CALIBRATOR_REGRESSION
    )
    assert result.raw_metrics.brier_score == pytest.approx(0.28777777777777774)
    assert result.calibrated_metrics.brier_score == pytest.approx(0.33919030111111326)
    assert result.raw_metrics.expected_calibration_error == pytest.approx(0.29222222222222227)
    assert result.calibrated_metrics.expected_calibration_error == pytest.approx(0.3584753301794393)
    assert result.brier_improvement < 0.0
    assert result.expected_calibration_error_improvement < 0.0
    assert result.final_evaluation_accessed is True
    assert result.artifact_refit is False
    assert result.artifact_mutated is False
    assert result.assessment_attempt_count == 1


def test_assessment_rejects_foreign_final_fixture_set_before_labels_are_read() -> None:
    class FinalLikeFixtureSet:
        @property
        def manifest(self) -> object:
            raise AssertionError("assessment must reject foreign objects before reading manifests")

    artifact, artifact_sha256, artifact_byte_count = load_bounded_platt_scaling_artifact(
        ARTIFACT_PATH
    )

    with pytest.raises(BoundedPlattHeldOutAssessmentError) as error_info:
        assess_bounded_platt_scaling_heldout(
            FinalLikeFixtureSet(),  # type: ignore[arg-type]
            artifact,
            artifact_sha256=artifact_sha256,
            artifact_byte_count=artifact_byte_count,
        )

    assert (
        error_info.value.code
        is BoundedPlattHeldOutAssessmentViolationCode.UNTRUSTED_FINAL_FIXTURE_SET
    )


def test_assessment_rejects_artifact_with_held_out_case_overlap(tmp_path: Path) -> None:
    fixture_set, (artifact, artifact_sha256, artifact_byte_count) = _assessment_inputs(tmp_path)
    overlapping_artifact = artifact.model_copy(update={"fit_case_ids": ("CRV2-201",)})

    with pytest.raises(BoundedPlattHeldOutAssessmentError) as error_info:
        assess_bounded_platt_scaling_heldout(
            fixture_set,
            overlapping_artifact,
            artifact_sha256=artifact_sha256,
            artifact_byte_count=artifact_byte_count,
        )

    assert (
        error_info.value.code
        is BoundedPlattHeldOutAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH
    )


def test_writer_is_byte_deterministic_and_preserves_lf_bytes(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    first_output = tmp_path / "first" / "heldout_assessment.json"
    second_output = tmp_path / "second" / "heldout_assessment.json"

    first = write_bounded_platt_scaling_heldout_assessment(
        fixture_root,
        ARTIFACT_PATH,
        first_output,
    )
    second = write_bounded_platt_scaling_heldout_assessment(
        fixture_root,
        ARTIFACT_PATH,
        second_output,
    )

    assert first == second
    assert first_output.read_bytes() == second_output.read_bytes()
    assert first_output.read_bytes().endswith(b"\n")
    assert b"\r\n" not in first_output.read_bytes()


def test_committed_assessment_matches_deterministic_rebuild(tmp_path: Path) -> None:
    rebuilt_output = tmp_path / "rebuilt" / "heldout_assessment.json"

    write_bounded_platt_scaling_heldout_assessment(
        _copied_fixture_root(tmp_path),
        ARTIFACT_PATH,
        rebuilt_output,
    )

    assert COMMITTED_ASSESSMENT_PATH.read_bytes() == rebuilt_output.read_bytes()
