"""Non-final tests for V4 held-out assessment contracts and gate semantics."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.heldout_calibration.v4_final_assessment import (
    DEFAULT_V4_FINAL_ASSESSMENT_PROTOCOL,
    V4AdaptivePolicyResearchEligibility,
    V4ConservativeFallbackRecord,
    V4FinalAssessmentError,
    V4FinalAssessmentErrorCode,
    V4FinalAssessmentGateChecks,
    V4FinalHeldOutAssessmentResult,
    V4FinalHeldOutAssessmentStatus,
    V4FinalPositionMetrics,
    V4FinalProbabilityMetrics,
    calculate_tie_aware_auroc,
    canonical_v4_final_assessment_json,
    reject_unsafe_retrospective_control,
    run_v4_final_assessment_once,
)


def _metrics(*, brier: float, ece: float, auroc: float) -> V4FinalProbabilityMetrics:
    return V4FinalProbabilityMetrics(brier_score=brier, ece_10_bin=ece, auroc=auroc)


def _position_metrics(
    *,
    observation_counts: tuple[int, int, int, int],
    raw_metrics: V4FinalProbabilityMetrics,
    calibrated_metrics: V4FinalProbabilityMetrics,
) -> tuple[V4FinalPositionMetrics, ...]:
    return tuple(
        V4FinalPositionMetrics(
            block_position_index=position,
            observation_count=observation_counts[position - 1],
            raw_metrics=raw_metrics,
            calibrated_metrics=calibrated_metrics,
            brier_score_improvement=raw_metrics.brier_score
            - calibrated_metrics.brier_score,
            ece_10_bin_improvement=raw_metrics.ece_10_bin
            - calibrated_metrics.ece_10_bin,
            auroc_delta=calibrated_metrics.auroc - raw_metrics.auroc,
        )
        for position in range(1, 5)
    )


def _result(
    *,
    case_count: int = 36,
    observation_counts: tuple[int, int, int, int] = (36, 36, 36, 36),
    raw_auroc: float = 0.800,
    calibrated_auroc: float = 0.799,
    manifest_integrity_passed: bool = True,
    provenance_alignment_passed: bool = True,
    write_once_precheck_passed: bool = True,
    canonical_serialization_passed: bool = True,
    calibration_refit_performed: bool = False,
    scheduler_or_policy_execution_performed: bool = False,
    status: V4FinalHeldOutAssessmentStatus | None = None,
) -> V4FinalHeldOutAssessmentResult:
    raw_metrics = _metrics(brier=0.200, ece=0.200, auroc=raw_auroc)
    calibrated_metrics = _metrics(brier=0.150, ece=0.150, auroc=calibrated_auroc)
    position_metrics = _position_metrics(
        observation_counts=observation_counts,
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
    )
    observation_count = sum(observation_counts)
    brier_improvement = raw_metrics.brier_score - calibrated_metrics.brier_score
    ece_improvement = raw_metrics.ece_10_bin - calibrated_metrics.ece_10_bin
    auroc_delta = calibrated_metrics.auroc - raw_metrics.auroc
    gate_checks = V4FinalAssessmentGateChecks(
        manifest_integrity_passed=manifest_integrity_passed,
        provenance_alignment_passed=provenance_alignment_passed,
        observation_coverage_passed=(case_count == 36 and observation_count == 144),
        per_position_coverage_passed=all(count == 36 for count in observation_counts),
        brier_improvement_passed=brier_improvement >= 0.010,
        ece_improvement_passed=ece_improvement >= 0.020,
        ranking_safety_passed=calibrated_auroc >= raw_auroc - 0.002,
        no_refit_passed=not calibration_refit_performed,
        no_policy_execution_passed=not scheduler_or_policy_execution_performed,
        write_once_precheck_passed=write_once_precheck_passed,
        canonical_serialization_passed=canonical_serialization_passed,
    )
    expected_status = {
        (True, True, True, True, True, True, True, True, True, True, True): (
            V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
        )
    }.get(
        (
            gate_checks.manifest_integrity_passed,
            gate_checks.provenance_alignment_passed,
            gate_checks.observation_coverage_passed,
            gate_checks.per_position_coverage_passed,
            gate_checks.brier_improvement_passed,
            gate_checks.ece_improvement_passed,
            gate_checks.ranking_safety_passed,
            gate_checks.no_refit_passed,
            gate_checks.no_policy_execution_passed,
            gate_checks.write_once_precheck_passed,
            gate_checks.canonical_serialization_passed,
        )
    )
    if expected_status is None:
        if not (
            gate_checks.manifest_integrity_passed
            and gate_checks.provenance_alignment_passed
        ):
            expected_status = V4FinalHeldOutAssessmentStatus.INVALID_PROVENANCE
        elif not (
            gate_checks.no_refit_passed
            and gate_checks.no_policy_execution_passed
            and gate_checks.write_once_precheck_passed
            and gate_checks.canonical_serialization_passed
        ):
            expected_status = V4FinalHeldOutAssessmentStatus.INCOMPLETE_GATE_EVIDENCE
        elif not (
            gate_checks.observation_coverage_passed
            and gate_checks.per_position_coverage_passed
        ):
            expected_status = (
                V4FinalHeldOutAssessmentStatus.INSUFFICIENT_HELD_OUT_COVERAGE
            )
        elif not gate_checks.ranking_safety_passed:
            expected_status = V4FinalHeldOutAssessmentStatus.RANKING_SAFETY_REGRESSION
        else:
            expected_status = V4FinalHeldOutAssessmentStatus.CALIBRATOR_REGRESSION
    resolved_status = status or expected_status
    is_pass = (
        resolved_status
        is V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
    )
    return V4FinalHeldOutAssessmentResult(
        protocol=DEFAULT_V4_FINAL_ASSESSMENT_PROTOCOL,
        fixture_set_id="synthetic-calibration-redesign-v4",
        fixture_set_version="1.0.0",
        final_manifest_aggregate_sha256="a" * 64,
        final_evidence_index_sha256="b" * 64,
        calibration_registry_sha256="c" * 64,
        calibration_manifest_sha256="d" * 64,
        calibration_manifest_aggregate_sha256="e" * 64,
        calibration_artifact_sha256="f" * 64,
        calibration_fit_report_sha256="0" * 64,
        calibration_artifact_id="regularized-isotonic-calibration-v4",
        calibration_artifact_version="1.0.0",
        assessment_case_ids=tuple(
            f"CRV4-{number:03d}" for number in range(1, case_count + 1)
        ),
        assessment_trace_ids=tuple(
            f"v4-nonfinal-trace-{number:03d}" for number in range(1, case_count + 1)
        ),
        case_count=case_count,
        observation_count=observation_count,
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        position_metrics=position_metrics,
        brier_score_improvement=brier_improvement,
        ece_10_bin_improvement=ece_improvement,
        auroc_delta=auroc_delta,
        gate_checks=gate_checks,
        status=resolved_status,
        adaptive_policy_research_eligibility=(
            V4AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
            if is_pass
            else V4AdaptivePolicyResearchEligibility.BLOCKED
        ),
        fallback=None if is_pass else V4ConservativeFallbackRecord(),
        calibration_refit_performed=calibration_refit_performed,
        scheduler_or_policy_execution_performed=scheduler_or_policy_execution_performed,
    )


def test_probability_metrics_reject_missing_auroc() -> None:
    with pytest.raises(ValidationError):
        V4FinalProbabilityMetrics.model_validate(
            {"brier_score": 0.2, "ece_10_bin": 0.1}
        )


def test_ranking_safety_failure_wins_after_brier_and_ece_pass() -> None:
    result = _result(raw_auroc=0.800, calibrated_auroc=0.790)

    assert result.gate_checks.brier_improvement_passed is True
    assert result.gate_checks.ece_improvement_passed is True
    assert result.gate_checks.ranking_safety_passed is False
    assert result.status is V4FinalHeldOutAssessmentStatus.RANKING_SAFETY_REGRESSION
    assert (
        result.adaptive_policy_research_eligibility
        is V4AdaptivePolicyResearchEligibility.BLOCKED
    )
    assert result.fallback == V4ConservativeFallbackRecord()


@pytest.mark.parametrize(
    ("case_count", "observation_counts"),
    [
        (35, (35, 35, 35, 35)),
        (36, (36, 36, 36, 35)),
    ],
)
def test_insufficient_aggregate_or_position_coverage_is_not_a_pass(
    case_count: int,
    observation_counts: tuple[int, int, int, int],
) -> None:
    result = _result(case_count=case_count, observation_counts=observation_counts)

    assert (
        result.status is V4FinalHeldOutAssessmentStatus.INSUFFICIENT_HELD_OUT_COVERAGE
    )
    assert (
        result.adaptive_policy_research_eligibility
        is V4AdaptivePolicyResearchEligibility.BLOCKED
    )


def test_false_gate_evidence_cannot_be_declared_a_complete_pass() -> None:
    with pytest.raises(ValidationError, match="status must match"):
        _result(
            canonical_serialization_passed=False,
            status=(
                V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
            ),
        )


def test_provenance_mismatch_is_invalid_provenance() -> None:
    result = _result(provenance_alignment_passed=False)

    assert result.status is V4FinalHeldOutAssessmentStatus.INVALID_PROVENANCE
    assert (
        result.adaptive_policy_research_eligibility
        is V4AdaptivePolicyResearchEligibility.BLOCKED
    )


@pytest.mark.parametrize(
    ("calibration_refit_performed", "scheduler_or_policy_execution_performed"),
    [(True, False), (False, True)],
)
def test_refit_or_policy_execution_cannot_coexist_with_complete_pass(
    calibration_refit_performed: bool,
    scheduler_or_policy_execution_performed: bool,
) -> None:
    with pytest.raises(ValidationError, match="status must match"):
        _result(
            calibration_refit_performed=calibration_refit_performed,
            scheduler_or_policy_execution_performed=scheduler_or_policy_execution_performed,
            status=(
                V4FinalHeldOutAssessmentStatus.PASSES_COMPLETE_HELD_OUT_CALIBRATION_GATE
            ),
        )


def test_runtime_control_eligibility_cannot_be_true() -> None:
    payload = _result().model_dump(mode="python")
    payload["runtime_control_eligible"] = True

    with pytest.raises(ValidationError):
        V4FinalHeldOutAssessmentResult.model_validate(payload)


def test_existing_destination_blocks_builder_before_any_assessment_work(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "result.json"
    destination.write_text("existing\n", encoding="utf-8")
    builder_called = False

    def _unexpected_builder() -> V4FinalHeldOutAssessmentResult:
        nonlocal builder_called
        builder_called = True
        return _result()

    with pytest.raises(V4FinalAssessmentError) as error:
        run_v4_final_assessment_once(destination, _unexpected_builder)

    assert error.value.code is V4FinalAssessmentErrorCode.DESTINATION_ALREADY_EXISTS
    assert builder_called is False


def test_canonical_json_is_byte_identical_for_equivalent_non_final_results() -> None:
    first = _result()
    second = _result()

    assert canonical_v4_final_assessment_json(
        first
    ) == canonical_v4_final_assessment_json(second)


def test_unsafe_retrospective_control_is_rejected_and_labelled_invalid() -> None:
    rejection = reject_unsafe_retrospective_control("unsafe_retrospective_oracle_v4")

    assert rejection.classification == "test_only_invalid_control"
    assert rejection.result_label == "INVALID_CAUSAL_COMPARISON"
    assert rejection.admitted_to_valid_baseline_comparison is False


def test_tie_aware_auroc_uses_average_ranks_deterministically() -> None:
    auroc = calculate_tie_aware_auroc(
        probabilities=(0.2, 0.2, 0.8, 0.8),
        labels=(False, True, False, True),
    )

    assert auroc == pytest.approx(0.5)
