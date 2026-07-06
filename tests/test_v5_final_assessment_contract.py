"""Non-final V5 complete-gate contract and regression harness.

These tests construct only synthetic contract objects. They do not load, author, fit, or assess
any V5 runtime input, label, manifest, calibration artifact, or final-evidence asset.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.contracts.models import WorkloadType
from specsafe.heldout_calibration.v5_final_assessment import (
    DEFAULT_V5_BOUNDED_MONOTONE_BETA_CALIBRATION_PROTOCOL,
    DEFAULT_V5_FINAL_ASSESSMENT_PROTOCOL,
    V5AdaptivePolicyResearchEligibility,
    V5BoundedMonotoneBetaCalibrationArtifact,
    V5BoundedMonotoneBetaParameters,
    V5ConservativeFallbackRecord,
    V5EvidenceRole,
    V5FinalAssessmentError,
    V5FinalAssessmentErrorCode,
    V5FinalAssessmentGateChecks,
    V5FinalHeldOutAssessmentResult,
    V5FinalHeldOutAssessmentStatus,
    V5FinalPositionMetrics,
    V5FinalProbabilityMetrics,
    V5FinalWorkloadCoverage,
    V5FrozenEvidenceManifestReference,
    calculate_tie_aware_auroc,
    calculate_v5_bounded_monotone_beta_probability,
    canonical_v5_final_assessment_json,
    run_v5_final_assessment_once,
    verify_v5_bounded_monotone_beta_monotonicity,
)


def _manifest(role: V5EvidenceRole) -> V5FrozenEvidenceManifestReference:
    if role is V5EvidenceRole.CALIBRATION:
        return V5FrozenEvidenceManifestReference(
            evidence_role=role,
            manifest_schema_version="v5-calibration-manifest-v1",
            manifest_relative_path="calibration_manifest.json",
            manifest_sha256="a" * 64,
            aggregate_sha256="b" * 64,
            case_id_start="CSV5-101",
            case_id_end="CSV5-148",
            case_count=48,
            observation_count=192,
        )
    return V5FrozenEvidenceManifestReference(
        evidence_role=role,
        manifest_schema_version="v5-final-evaluation-manifest-v1",
        manifest_relative_path="final_evaluation_manifest.json",
        manifest_sha256="c" * 64,
        aggregate_sha256="d" * 64,
        case_id_start="CSV5-201",
        case_id_end="CSV5-236",
        case_count=36,
        observation_count=144,
    )


def _artifact() -> V5BoundedMonotoneBetaCalibrationArtifact:
    parameters = V5BoundedMonotoneBetaParameters(a=1.0, b=1.0, c=0.0)
    monotonicity = verify_v5_bounded_monotone_beta_monotonicity(
        parameters,
        boundary_inputs=(0.0, 0.25, 0.5, 0.75, 1.0),
        observed_calibration_inputs=(0.12, 0.25, 0.25, 0.61, 0.88),
    )
    return V5BoundedMonotoneBetaCalibrationArtifact(
        protocol=DEFAULT_V5_BOUNDED_MONOTONE_BETA_CALIBRATION_PROTOCOL,
        calibration_manifest=_manifest(V5EvidenceRole.CALIBRATION),
        parameters=parameters,
        monotonicity_verification=monotonicity,
    )


def _metrics(*, brier: float, ece: float, auroc: float) -> V5FinalProbabilityMetrics:
    return V5FinalProbabilityMetrics(brier_score=brier, ece_10_bin=ece, auroc=auroc)


def _position_metrics(
    *,
    observation_counts: tuple[int, int, int, int],
    raw_metrics: V5FinalProbabilityMetrics,
    calibrated_metrics: V5FinalProbabilityMetrics,
) -> tuple[V5FinalPositionMetrics, ...]:
    return tuple(
        V5FinalPositionMetrics(
            block_position_index=index,
            observation_count=count,
            raw_metrics=raw_metrics,
            calibrated_metrics=calibrated_metrics,
            brier_score_improvement=(
                raw_metrics.brier_score - calibrated_metrics.brier_score
            ),
            ece_10_bin_improvement=(
                raw_metrics.ece_10_bin - calibrated_metrics.ece_10_bin
            ),
            auroc_delta=calibrated_metrics.auroc - raw_metrics.auroc,
        )
        for index, count in enumerate(observation_counts, start=1)
    )


def _workload_coverage(
    counts: tuple[int, int, int] = (48, 48, 48),
) -> tuple[V5FinalWorkloadCoverage, ...]:
    return tuple(
        V5FinalWorkloadCoverage(workload_type=workload, observation_count=count)
        for workload, count in zip(
            (
                WorkloadType.STRUCTURED_TEXT,
                WorkloadType.CODE,
                WorkloadType.OPEN_ENDED_CHAT,
            ),
            counts,
            strict=True,
        )
    )


def _result(
    *,
    case_count: int = 36,
    observation_counts: tuple[int, int, int, int] = (36, 36, 36, 36),
    workload_counts: tuple[int, int, int] = (48, 48, 48),
    raw_auroc: float = 0.800,
    calibrated_auroc: float = 0.800,
    manifest_integrity_passed: bool = True,
    provenance_alignment_passed: bool = True,
    write_once_precheck_passed: bool = True,
    canonical_serialization_passed: bool = True,
    calibration_refit_performed: bool = False,
    policy_or_replay_execution_performed: bool = False,
    status: V5FinalHeldOutAssessmentStatus | None = None,
) -> V5FinalHeldOutAssessmentResult:
    raw_metrics = _metrics(brier=0.200, ece=0.200, auroc=raw_auroc)
    calibrated_metrics = _metrics(brier=0.190, ece=0.185, auroc=calibrated_auroc)
    position_metrics = _position_metrics(
        observation_counts=observation_counts,
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
    )
    workloads = _workload_coverage(workload_counts)
    observation_count = sum(observation_counts)
    brier_improvement = raw_metrics.brier_score - calibrated_metrics.brier_score
    ece_improvement = raw_metrics.ece_10_bin - calibrated_metrics.ece_10_bin
    auroc_delta = calibrated_metrics.auroc - raw_metrics.auroc
    artifact = _artifact()
    checks = V5FinalAssessmentGateChecks(
        manifest_integrity_passed=manifest_integrity_passed,
        provenance_alignment_passed=provenance_alignment_passed,
        observation_coverage_passed=(case_count == 36 and observation_count == 144),
        per_position_coverage_passed=all(count == 36 for count in observation_counts),
        workload_coverage_passed=all(count == 48 for count in workload_counts),
        monotonicity_verification_passed=artifact.monotonicity_verification.verification_passed,
        brier_improvement_passed=brier_improvement >= 0.005,
        ece_improvement_passed=ece_improvement >= 0.010,
        ranking_safety_passed=calibrated_auroc >= raw_auroc - 0.001,
        no_refit_passed=not calibration_refit_performed,
        no_policy_execution_passed=not policy_or_replay_execution_performed,
        write_once_precheck_passed=write_once_precheck_passed,
        canonical_serialization_passed=canonical_serialization_passed,
    )
    expected_status = _status_from_checks(checks)
    resolved_status = status or expected_status
    is_pass = (
        resolved_status
        is V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
    )
    case_ids = tuple(f"CSV5-{200 + index:03d}" for index in range(1, case_count + 1))
    trace_ids = tuple(f"v5-nonfinal-trace-{index:03d}" for index in range(1, case_count + 1))
    return V5FinalHeldOutAssessmentResult(
        protocol=DEFAULT_V5_FINAL_ASSESSMENT_PROTOCOL,
        final_manifest=_manifest(V5EvidenceRole.FINAL_EVALUATION),
        calibration_manifest=_manifest(V5EvidenceRole.CALIBRATION),
        final_evidence_index_sha256="e" * 64,
        calibration_artifact_sha256="f" * 64,
        calibration_fit_report_sha256="0" * 64,
        calibration_artifact=artifact,
        assessment_case_ids=case_ids,
        assessment_trace_ids=trace_ids,
        case_count=case_count,
        observation_count=observation_count,
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        position_metrics=position_metrics,
        workload_coverage=workloads,
        brier_score_improvement=brier_improvement,
        ece_10_bin_improvement=ece_improvement,
        auroc_delta=auroc_delta,
        gate_checks=checks,
        status=resolved_status,
        adaptive_policy_research_eligibility=(
            V5AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
            if is_pass
            else V5AdaptivePolicyResearchEligibility.BLOCKED
        ),
        fallback=None if is_pass else V5ConservativeFallbackRecord(),
        calibration_refit_performed=calibration_refit_performed,
        policy_or_replay_execution_performed=policy_or_replay_execution_performed,
    )


def _status_from_checks(
    checks: V5FinalAssessmentGateChecks,
) -> V5FinalHeldOutAssessmentStatus:
    if not (checks.manifest_integrity_passed and checks.provenance_alignment_passed):
        return V5FinalHeldOutAssessmentStatus.INVALID_PROVENANCE
    if not checks.write_once_precheck_passed:
        return V5FinalHeldOutAssessmentStatus.WRITE_ONCE_DESTINATION_EXISTS
    if not (
        checks.no_refit_passed
        and checks.no_policy_execution_passed
        and checks.canonical_serialization_passed
    ):
        return V5FinalHeldOutAssessmentStatus.INCOMPLETE_GATE_EVIDENCE
    if not (
        checks.observation_coverage_passed
        and checks.per_position_coverage_passed
        and checks.workload_coverage_passed
    ):
        return V5FinalHeldOutAssessmentStatus.INSUFFICIENT_HELD_OUT_COVERAGE
    if not checks.ranking_safety_passed:
        return V5FinalHeldOutAssessmentStatus.RANKING_SAFETY_REGRESSION
    if not (
        checks.monotonicity_verification_passed
        and checks.brier_improvement_passed
        and checks.ece_improvement_passed
    ):
        return V5FinalHeldOutAssessmentStatus.CALIBRATOR_REGRESSION
    return V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE


def test_predeclared_v5_transform_is_bounded_and_order_preserving() -> None:
    parameters = V5BoundedMonotoneBetaParameters(a=1.0, b=1.0, c=0.0)

    calibrated = tuple(
        calculate_v5_bounded_monotone_beta_probability(value, parameters)
        for value in (0.0, 0.2, 0.5, 0.8, 1.0)
    )
    monotonicity = verify_v5_bounded_monotone_beta_monotonicity(
        parameters,
        boundary_inputs=(0.0, 0.2, 0.5, 0.8, 1.0),
        observed_calibration_inputs=(0.8, 0.2, 0.2, 0.5),
    )

    assert all(0.0 < value < 1.0 for value in calibrated)
    assert calibrated == tuple(sorted(calibrated))
    assert monotonicity.verification_passed is True
    assert monotonicity.boundary_strictly_increasing is True


def test_complete_gate_pass_permits_research_only() -> None:
    result = _result()

    assert (
        result.status
        is V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
    )
    assert (
        result.adaptive_policy_research_eligibility
        is V5AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
    )
    assert result.fallback is None
    assert result.runtime_control_eligible is False


def test_ranking_safety_failure_wins_after_brier_and_ece_pass() -> None:
    result = _result(raw_auroc=0.800, calibrated_auroc=0.798)

    assert result.gate_checks.brier_improvement_passed is True
    assert result.gate_checks.ece_improvement_passed is True
    assert result.gate_checks.ranking_safety_passed is False
    assert result.status is V5FinalHeldOutAssessmentStatus.RANKING_SAFETY_REGRESSION
    assert result.fallback == V5ConservativeFallbackRecord()


@pytest.mark.parametrize(
    ("case_count", "observation_counts", "workload_counts"),
    [
        (35, (35, 35, 35, 35), (47, 47, 46)),
        (36, (36, 36, 36, 35), (48, 48, 47)),
        (36, (36, 36, 36, 36), (48, 47, 49)),
    ],
)
def test_missing_case_position_or_workload_coverage_blocks_pass(
    case_count: int,
    observation_counts: tuple[int, int, int, int],
    workload_counts: tuple[int, int, int],
) -> None:
    result = _result(
        case_count=case_count,
        observation_counts=observation_counts,
        workload_counts=workload_counts,
    )

    assert result.status is V5FinalHeldOutAssessmentStatus.INSUFFICIENT_HELD_OUT_COVERAGE
    assert (
        result.adaptive_policy_research_eligibility
        is V5AdaptivePolicyResearchEligibility.BLOCKED
    )


def test_incomplete_gate_evidence_cannot_be_declared_a_pass() -> None:
    with pytest.raises(ValidationError, match="status must match"):
        _result(
            canonical_serialization_passed=False,
            status=(
                V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
            ),
        )


def test_write_once_status_is_retained_by_contract_but_builder_is_never_called() -> None:
    result = _result(write_once_precheck_passed=False)

    assert result.status is V5FinalHeldOutAssessmentStatus.WRITE_ONCE_DESTINATION_EXISTS
    assert result.fallback == V5ConservativeFallbackRecord()


def test_existing_destination_blocks_builder_before_any_assessment_work(tmp_path: Path) -> None:
    destination = tmp_path / "result.json"
    destination.write_text("existing\n", encoding="utf-8")
    builder_called = False

    def _unexpected_builder() -> V5FinalHeldOutAssessmentResult:
        nonlocal builder_called
        builder_called = True
        return _result()

    with pytest.raises(V5FinalAssessmentError) as error:
        run_v5_final_assessment_once(destination, _unexpected_builder)

    assert error.value.code is V5FinalAssessmentErrorCode.DESTINATION_ALREADY_EXISTS
    assert builder_called is False


def test_canonical_json_is_byte_identical_for_equivalent_non_final_results() -> None:
    assert canonical_v5_final_assessment_json(_result()) == canonical_v5_final_assessment_json(
        _result()
    )


def test_artifact_rejects_final_manifest_reference() -> None:
    parameters = V5BoundedMonotoneBetaParameters(a=1.0, b=1.0, c=0.0)
    monotonicity = verify_v5_bounded_monotone_beta_monotonicity(
        parameters,
        boundary_inputs=(0.0, 0.5, 1.0),
        observed_calibration_inputs=(0.2, 0.7),
    )

    with pytest.raises(ValidationError, match="calibration evidence only"):
        V5BoundedMonotoneBetaCalibrationArtifact(
            protocol=DEFAULT_V5_BOUNDED_MONOTONE_BETA_CALIBRATION_PROTOCOL,
            calibration_manifest=_manifest(V5EvidenceRole.FINAL_EVALUATION),
            parameters=parameters,
            monotonicity_verification=monotonicity,
        )


def test_tie_aware_auroc_uses_average_ranks_deterministically() -> None:
    auroc = calculate_tie_aware_auroc(
        probabilities=(0.2, 0.2, 0.8, 0.8),
        labels=(False, True, False, True),
    )

    assert auroc == pytest.approx(0.5)
