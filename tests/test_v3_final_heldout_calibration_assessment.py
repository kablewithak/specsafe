"""Unit tests for V3 final held-out assessment logic without scoring frozen final fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from specsafe.heldout_calibration import v3_final_assessment
from specsafe.heldout_calibration.v3_final_assessment import (
    DEFAULT_V3_FINAL_HELDOUT_CALIBRATION_ASSESSMENT_PROTOCOL,
    V3FinalAdaptivePolicyResearchEligibility,
    V3FinalHeldOutCalibrationAssessmentError,
    V3FinalHeldOutCalibrationAssessmentErrorCode,
    V3FinalHeldOutCalibrationAssessmentResult,
    V3FinalHeldOutCalibrationAssessmentStatus,
    _build_probability_metrics,
    _derive_assessment_status,
    run_v3_final_heldout_calibration_assessment_once,
    write_v3_final_heldout_calibration_assessment,
)


def _result() -> V3FinalHeldOutCalibrationAssessmentResult:
    raw_metrics = _build_probability_metrics(
        probabilities=(0.10, 0.20, 0.80, 0.90) * 24,
        labels=(False, False, True, True) * 24,
        bin_count=10,
    )
    calibrated_metrics = _build_probability_metrics(
        probabilities=(0.01, 0.01, 0.99, 0.99) * 24,
        labels=(False, False, True, True) * 24,
        bin_count=10,
    )
    position_metrics = tuple(
        {
            "block_position_index": position,
            "observation_count": 24,
            "raw_metrics": raw_metrics,
            "calibrated_metrics": calibrated_metrics,
            "brier_score_improvement": (
                raw_metrics.brier_score - calibrated_metrics.brier_score
            ),
            "expected_calibration_error_improvement": (
                raw_metrics.expected_calibration_error
                - calibrated_metrics.expected_calibration_error
            ),
        }
        for position in range(1, 5)
    )
    return V3FinalHeldOutCalibrationAssessmentResult(
        protocol=DEFAULT_V3_FINAL_HELDOUT_CALIBRATION_ASSESSMENT_PROTOCOL,
        fixture_set_id="synthetic-calibration-redesign-v3",
        fixture_set_version="1.0.0",
        final_manifest_aggregate_sha256="a" * 64,
        final_evidence_index_sha256="b" * 64,
        calibration_registry_sha256="c" * 64,
        calibration_manifest_sha256="d" * 64,
        calibration_manifest_aggregate_sha256="e" * 64,
        calibration_artifact_sha256="f" * 64,
        calibration_fit_report_sha256="0" * 64,
        calibration_artifact_id="quantile-isotonic-calibration-v1",
        calibration_artifact_version="1.0.0",
        assessment_case_ids=tuple(f"CRV3-{number:03d}" for number in range(201, 225)),
        assessment_trace_ids=tuple(f"trace-{number:03d}" for number in range(201, 225)),
        observation_count=96,
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        position_metrics=position_metrics,
        brier_score_improvement=(
            raw_metrics.brier_score - calibrated_metrics.brier_score
        ),
        expected_calibration_error_improvement=(
            raw_metrics.expected_calibration_error
            - calibrated_metrics.expected_calibration_error
        ),
        status=V3FinalHeldOutCalibrationAssessmentStatus.PASSES_HELD_OUT_FITNESS,
        adaptive_policy_research_eligibility=(
            V3FinalAdaptivePolicyResearchEligibility.ELIGIBLE_PENDING_EXPLICIT_AUTHORIZATION
        ),
    )


def test_probability_metrics_keep_fixed_ten_bins_and_count_all_observations() -> None:
    metrics = _build_probability_metrics(
        probabilities=(0.00, 0.15, 0.50, 0.95, 1.00),
        labels=(False, False, True, True, True),
        bin_count=10,
    )

    assert len(metrics.bins) == 10
    assert sum(item.observation_count for item in metrics.bins) == 5
    assert metrics.brier_score >= 0.0
    assert metrics.expected_calibration_error >= 0.0


@pytest.mark.parametrize(
    ("brier_improvement", "ece_improvement", "expected_status", "expected_eligibility"),
    [
        (
            0.01,
            0.02,
            V3FinalHeldOutCalibrationAssessmentStatus.PASSES_HELD_OUT_FITNESS,
            V3FinalAdaptivePolicyResearchEligibility.ELIGIBLE_PENDING_EXPLICIT_AUTHORIZATION,
        ),
        (
            -0.01,
            0.02,
            V3FinalHeldOutCalibrationAssessmentStatus.CALIBRATOR_REGRESSION,
            V3FinalAdaptivePolicyResearchEligibility.BLOCKED_HELD_OUT_CALIBRATION_REGRESSION,
        ),
        (
            0.01,
            0.00,
            V3FinalHeldOutCalibrationAssessmentStatus.NO_MATERIAL_HELD_OUT_IMPROVEMENT,
            V3FinalAdaptivePolicyResearchEligibility.BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT,
        ),
    ],
)
def test_gate_status_is_predeclared_and_does_not_authorize_runtime(
    brier_improvement: float,
    ece_improvement: float,
    expected_status: V3FinalHeldOutCalibrationAssessmentStatus,
    expected_eligibility: V3FinalAdaptivePolicyResearchEligibility,
) -> None:
    status, eligibility = _derive_assessment_status(
        observation_count=96,
        brier_improvement=brier_improvement,
        expected_calibration_error_improvement=ece_improvement,
        protocol=DEFAULT_V3_FINAL_HELDOUT_CALIBRATION_ASSESSMENT_PROTOCOL,
    )

    assert status is expected_status
    assert eligibility is expected_eligibility


def test_assessment_result_remains_runtime_ineligible() -> None:
    result = _result()

    assert result.runtime_control_eligible is False
    assert result.calibration_refit_performed is False
    assert result.scheduler_or_policy_execution_performed is False
    assert result.write_mode == "write_once"


def test_report_persistence_is_write_once(tmp_path: Path) -> None:
    destination = tmp_path / "result.json"

    written = write_v3_final_heldout_calibration_assessment(_result(), destination)

    assert written == destination
    assert destination.is_file()
    with pytest.raises(V3FinalHeldOutCalibrationAssessmentError) as error:
        write_v3_final_heldout_calibration_assessment(_result(), destination)

    assert (
        error.value.code
        is V3FinalHeldOutCalibrationAssessmentErrorCode.DESTINATION_ALREADY_EXISTS
    )


def test_once_runner_refuses_existing_destination_before_scoring(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "result.json"
    destination.write_text("already assessed\n", encoding="utf-8")

    def _unexpected_evaluation(_: Path) -> V3FinalHeldOutCalibrationAssessmentResult:
        raise AssertionError(
            "existing output must block scoring before fixture evaluation"
        )

    monkeypatch.setattr(
        v3_final_assessment,
        "evaluate_v3_final_heldout_calibration",
        _unexpected_evaluation,
    )

    with pytest.raises(V3FinalHeldOutCalibrationAssessmentError) as error:
        run_v3_final_heldout_calibration_assessment_once(tmp_path, destination)

    assert (
        error.value.code
        is V3FinalHeldOutCalibrationAssessmentErrorCode.DESTINATION_ALREADY_EXISTS
    )
