from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.confidence_fitness import (
    AutomationControlEligibility,
    ConfidenceFitnessErrorCode,
    ConfidenceFitnessEvaluationError,
    ConfidenceFitnessProtocolConfig,
    RawConfidenceFitnessStatus,
    evaluate_raw_confidence_fitness,
)
from specsafe.contracts import TraceSplit
from specsafe.traces import load_synthetic_trace_fixture_set

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_trace_baselines"
)


def test_calibration_fixture_assets_are_loaded_with_governed_split_identity() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)

    calibration_cases = tuple(
        case
        for case in fixture_set.cases
        if case.runtime_input.split is TraceSplit.CALIBRATION
    )

    assert fixture_set.manifest.fixture_set_version == "1.1.0"
    assert tuple(case.runtime_input.case_id for case in calibration_cases) == (
        "STF-005",
        "STF-006",
    )
    assert all(len(case.runtime_input.contexts) == 4 for case in calibration_cases)


def test_default_raw_confidence_protocol_reports_unfit_without_authorizing_control() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)

    result = evaluate_raw_confidence_fitness(fixture_set)

    assert result.observation_count == 8
    assert result.calibration_case_ids == ("STF-005", "STF-006")
    assert result.status is RawConfidenceFitnessStatus.FAILS_PRECALIBRATION_SCREEN
    assert (
        result.automation_control_eligibility
        is AutomationControlEligibility.NOT_ELIGIBLE_PENDING_HELD_OUT_CALIBRATION
    )
    assert result.brier_score == pytest.approx(0.34)
    assert result.expected_calibration_error == pytest.approx(0.375)


def test_relaxed_diagnostic_thresholds_do_not_authorize_automated_scheduling() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)
    protocol = ConfidenceFitnessProtocolConfig(
        maximum_brier_score=0.5,
        maximum_expected_calibration_error=0.5,
    )

    result = evaluate_raw_confidence_fitness(fixture_set, protocol=protocol)

    assert result.status is RawConfidenceFitnessStatus.PASSES_PRECALIBRATION_SCREEN
    assert (
        result.automation_control_eligibility
        is AutomationControlEligibility.NOT_ELIGIBLE_PENDING_HELD_OUT_CALIBRATION
    )


def test_insufficient_calibration_data_status_precedes_threshold_assessment() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)
    protocol = ConfidenceFitnessProtocolConfig(
        minimum_observation_count=9,
        maximum_brier_score=0.5,
        maximum_expected_calibration_error=0.5,
    )

    result = evaluate_raw_confidence_fitness(fixture_set, protocol=protocol)

    assert result.status is RawConfidenceFitnessStatus.INSUFFICIENT_CALIBRATION_DATA


def test_protocol_rejects_unknown_fields_and_invalid_fixture_shape() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ConfidenceFitnessProtocolConfig(unapproved_threshold_source="final_evaluation")

    with pytest.raises(ConfidenceFitnessEvaluationError) as error:
        evaluate_raw_confidence_fitness(object())

    assert error.value.code is ConfidenceFitnessErrorCode.INVALID_FIXTURE_SET


def test_result_bins_account_for_only_calibration_observations() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)

    result = evaluate_raw_confidence_fitness(fixture_set)

    assert len(result.bins) == result.protocol.bin_count
    assert sum(bin_summary.observation_count for bin_summary in result.bins) == 8
    assert all(bin_summary.bin_index < result.protocol.bin_count for bin_summary in result.bins)
