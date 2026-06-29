from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.calibration import fit_frozen_histogram_calibrator
from specsafe.contracts import SyntheticTraceFixtureSet, TraceSplit
from specsafe.heldout_calibration import (
    AdaptivePolicyResearchEligibility,
    CalibrationPromotionDecision,
    HeldOutCalibrationFitnessError,
    HeldOutCalibrationFitnessProtocol,
    HeldOutCalibrationFitnessStatus,
    HeldOutFitnessErrorCode,
    evaluate_heldout_calibration_fitness,
    write_heldout_calibration_fitness_report,
)
from specsafe.traces import load_synthetic_trace_fixture_set

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_trace_baselines"
)


def load_fixture_set() -> SyntheticTraceFixtureSet:
    return load_synthetic_trace_fixture_set(FIXTURE_ROOT)


def test_heldout_assessment_retains_final_only_evidence_and_blocks_regression() -> None:
    fixture_set = load_fixture_set()
    artifact = fit_frozen_histogram_calibrator(fixture_set)

    result = evaluate_heldout_calibration_fitness(
        fixture_set,
        calibrator_artifact=artifact,
    )

    assert result.assessment_split is TraceSplit.FINAL_EVALUATION
    assert result.assessment_case_ids == ("STF-004",)
    assert result.assessment_trace_ids == ("synthetic-trace-004",)
    assert result.observation_count == 4
    assert result.raw_metrics.brier_score == pytest.approx(0.05685)
    assert result.calibrated_metrics.brier_score == pytest.approx(1 / 3)
    assert result.raw_metrics.expected_calibration_error == pytest.approx(0.235)
    assert result.calibrated_metrics.expected_calibration_error == pytest.approx(0.5)
    assert result.status is HeldOutCalibrationFitnessStatus.CALIBRATOR_REGRESSION
    assert (
        result.promotion_decision
        is CalibrationPromotionDecision.NOT_PROMOTED_CALIBRATOR_REGRESSION
    )
    assert (
        result.adaptive_policy_research_eligibility
        is AdaptivePolicyResearchEligibility.BLOCKED_HELD_OUT_CALIBRATION_REGRESSION
    )


def test_heldout_assessment_does_not_read_calibration_outcomes_after_artifact_freeze() -> None:
    fixture_set = load_fixture_set()
    artifact = fit_frozen_histogram_calibrator(fixture_set)
    original = evaluate_heldout_calibration_fitness(
        fixture_set,
        calibrator_artifact=artifact,
    )
    calibration_case_index = next(
        index
        for index, case in enumerate(fixture_set.cases)
        if case.runtime_input.split is TraceSplit.CALIBRATION
    )
    calibration_case = fixture_set.cases[calibration_case_index]
    altered_outcomes = tuple(
        outcome.model_copy(update={"observed_acceptance": not outcome.observed_acceptance})
        for outcome in calibration_case.expected_outcomes.outcomes
    )
    altered_calibration_case = calibration_case.model_copy(
        update={
            "expected_outcomes": calibration_case.expected_outcomes.model_copy(
                update={"outcomes": altered_outcomes}
            )
        }
    )
    altered_cases = list(fixture_set.cases)
    altered_cases[calibration_case_index] = altered_calibration_case
    fixture_with_altered_calibration = fixture_set.model_copy(
        update={"cases": tuple(altered_cases)}
    )

    unaffected = evaluate_heldout_calibration_fitness(
        fixture_with_altered_calibration,
        calibrator_artifact=artifact,
    )

    assert unaffected == original


def test_heldout_assessment_changes_when_final_outcomes_change() -> None:
    fixture_set = load_fixture_set()
    artifact = fit_frozen_histogram_calibrator(fixture_set)
    original = evaluate_heldout_calibration_fitness(
        fixture_set,
        calibrator_artifact=artifact,
    )
    final_case_index = next(
        index
        for index, case in enumerate(fixture_set.cases)
        if case.runtime_input.split is TraceSplit.FINAL_EVALUATION
    )
    final_case = fixture_set.cases[final_case_index]
    altered_outcomes = tuple(
        outcome.model_copy(update={"observed_acceptance": False})
        for outcome in final_case.expected_outcomes.outcomes
    )
    altered_final_case = final_case.model_copy(
        update={
            "expected_outcomes": final_case.expected_outcomes.model_copy(
                update={"outcomes": altered_outcomes}
            )
        }
    )
    altered_cases = list(fixture_set.cases)
    altered_cases[final_case_index] = altered_final_case
    fixture_with_altered_final = fixture_set.model_copy(update={"cases": tuple(altered_cases)})

    changed = evaluate_heldout_calibration_fitness(
        fixture_with_altered_final,
        calibrator_artifact=artifact,
    )

    assert changed != original
    assert changed.raw_metrics.brier_score != original.raw_metrics.brier_score


def test_heldout_assessment_blocks_promotion_when_observations_are_insufficient() -> None:
    fixture_set = load_fixture_set()
    artifact = fit_frozen_histogram_calibrator(fixture_set)

    result = evaluate_heldout_calibration_fitness(
        fixture_set,
        calibrator_artifact=artifact,
        protocol=HeldOutCalibrationFitnessProtocol(minimum_observation_count=5),
    )

    assert result.status is HeldOutCalibrationFitnessStatus.INSUFFICIENT_HELD_OUT_DATA
    assert (
        result.promotion_decision
        is CalibrationPromotionDecision.NOT_PROMOTED_INSUFFICIENT_HELD_OUT_DATA
    )
    assert (
        result.adaptive_policy_research_eligibility
        is AdaptivePolicyResearchEligibility.BLOCKED_INSUFFICIENT_HELD_OUT_FITNESS
    )


def test_heldout_assessment_rejects_invalid_inputs_and_artifact_mismatches() -> None:
    fixture_set = load_fixture_set()
    artifact = fit_frozen_histogram_calibrator(fixture_set)

    with pytest.raises(HeldOutCalibrationFitnessError) as invalid_fixture_error:
        evaluate_heldout_calibration_fitness(
            object(),
            calibrator_artifact=artifact,
        )
    assert invalid_fixture_error.value.code is HeldOutFitnessErrorCode.INVALID_FIXTURE_SET

    with pytest.raises(HeldOutCalibrationFitnessError) as invalid_artifact_error:
        evaluate_heldout_calibration_fitness(
            fixture_set,
            calibrator_artifact=object(),
        )
    assert (
        invalid_artifact_error.value.code
        is HeldOutFitnessErrorCode.INVALID_CALIBRATOR_ARTIFACT
    )

    mismatched_artifact = artifact.model_copy(update={"fixture_set_version": "other"})
    with pytest.raises(HeldOutCalibrationFitnessError) as mismatch_error:
        evaluate_heldout_calibration_fitness(
            fixture_set,
            calibrator_artifact=mismatched_artifact,
        )
    assert mismatch_error.value.code is HeldOutFitnessErrorCode.ARTIFACT_FIXTURE_MISMATCH


def test_heldout_protocol_is_schema_strict() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        HeldOutCalibrationFitnessProtocol(unapproved_final_threshold=0.8)


def test_heldout_report_persistence_is_deterministic(tmp_path: Path) -> None:
    fixture_set = load_fixture_set()
    artifact = fit_frozen_histogram_calibrator(fixture_set)
    result = evaluate_heldout_calibration_fitness(
        fixture_set,
        calibrator_artifact=artifact,
    )

    first_path = write_heldout_calibration_fitness_report(result, tmp_path / "first.json")
    second_path = write_heldout_calibration_fitness_report(result, tmp_path / "second.json")

    assert first_path.read_bytes() == second_path.read_bytes()
    assert '"assessment_split": "final_evaluation"' in first_path.read_text(encoding="utf-8")
