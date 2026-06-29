from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.causal_safety import ForbiddenInformationAccessError
from specsafe.causal_safety.unsafe_controls import RetrospectiveEvaluationContext
from specsafe.contracts import (
    CapacityProfileSource,
    CapacitySnapshot,
    CausalSafetyStatus,
    CausalSchedulerContext,
    VerificationAction,
    WorkloadType,
)
from specsafe.scheduling import (
    FixedLengthPolicyConfig,
    FixedLengthVerificationPolicy,
    StaticThresholdPolicyConfig,
    StaticThresholdVerificationPolicy,
    UnsafeRetrospectiveLookaheadPolicy,
)
from specsafe.traces import load_synthetic_trace_fixture_set

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_trace_baselines"
)


def make_context(
    *,
    position: int = 1,
    confidence: float = 0.7,
) -> CausalSchedulerContext:
    return CausalSchedulerContext(
        trace_id="policy-test-trace",
        request_id="policy-test-request",
        workload_type=WorkloadType.CODE,
        decode_round=0,
        block_position_index=position,
        visible_prefix_token_ids=tuple(range(position - 1)),
        conditional_survival_confidence=confidence,
        capacity_snapshot=CapacitySnapshot(
            profile_id="synthetic-policy-test-v1",
            source=CapacityProfileSource.SYNTHETIC,
            active_request_count=3,
            verification_batch_tokens=position - 1,
        ),
    )


def test_fixed_length_policy_admits_only_positions_inside_its_budget() -> None:
    policy = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(maximum_verification_length=2)
    )

    first_decision = policy.decide(make_context(position=1))
    third_decision = policy.decide(make_context(position=3))

    assert first_decision.action is VerificationAction.ADMIT
    assert first_decision.reason_code == "fixed_length_within_budget"
    assert third_decision.action is VerificationAction.STOP
    assert third_decision.reason_code == "fixed_length_budget_exhausted"
    assert third_decision.causal_safety_status is CausalSafetyStatus.PASS


def test_threshold_policy_admits_at_the_configured_boundary() -> None:
    policy = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(minimum_conditional_survival_confidence=0.7)
    )

    boundary_decision = policy.decide(make_context(confidence=0.7))
    lower_decision = policy.decide(make_context(confidence=0.69))

    assert boundary_decision.action is VerificationAction.ADMIT
    assert boundary_decision.reason_code == "static_threshold_met"
    assert lower_decision.action is VerificationAction.STOP
    assert lower_decision.reason_code == "static_threshold_below_minimum"


def test_valid_baselines_reject_the_test_only_retrospective_context() -> None:
    unsafe_context = RetrospectiveEvaluationContext(
        runtime_context=make_context(),
        future_candidate_token_ids=(901,),
        future_acceptance_outcomes=(True,),
    )
    fixed_policy = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(maximum_verification_length=1)
    )
    threshold_policy = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(minimum_conditional_survival_confidence=0.5)
    )

    with pytest.raises(ForbiddenInformationAccessError):
        fixed_policy.decide(unsafe_context)
    with pytest.raises(ForbiddenInformationAccessError):
        threshold_policy.decide(unsafe_context)


def test_unsafe_retrospective_policy_uses_future_outcome_and_marks_failure() -> None:
    policy = UnsafeRetrospectiveLookaheadPolicy()
    admitted = policy.decide(
        RetrospectiveEvaluationContext(
            runtime_context=make_context(),
            future_candidate_token_ids=(901,),
            future_acceptance_outcomes=(True,),
        )
    )
    stopped = policy.decide(
        RetrospectiveEvaluationContext(
            runtime_context=make_context(),
            future_candidate_token_ids=(902,),
            future_acceptance_outcomes=(False,),
        )
    )

    assert admitted.action is VerificationAction.ADMIT
    assert admitted.reason_code == "unsafe_future_outcome_admit"
    assert admitted.causal_safety_status is CausalSafetyStatus.FAIL
    assert stopped.action is VerificationAction.STOP
    assert stopped.reason_code == "unsafe_future_outcome_stop"
    assert stopped.causal_safety_status is CausalSafetyStatus.FAIL
    assert policy.config.evaluation_only is True


def test_unsafe_policy_rejects_a_valid_runtime_context() -> None:
    policy = UnsafeRetrospectiveLookaheadPolicy()

    with pytest.raises(TypeError, match="RetrospectiveEvaluationContext"):
        policy.decide(make_context())


def test_policy_configurations_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        FixedLengthPolicyConfig(
            maximum_verification_length=2,
            observed_acceptance=True,
        )


def test_baselines_run_over_identical_development_fixture_contexts() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)
    development_case = next(
        case
        for case in fixture_set.cases
        if case.runtime_input.case_id == "STF-002"
    )
    fixed_policy = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(maximum_verification_length=3)
    )
    threshold_policy = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(minimum_conditional_survival_confidence=0.4)
    )

    fixed_actions = tuple(
        fixed_policy.decide(context).action
        for context in development_case.runtime_input.contexts
    )
    threshold_actions = tuple(
        threshold_policy.decide(context).action
        for context in development_case.runtime_input.contexts
    )

    assert fixed_actions == (
        VerificationAction.ADMIT,
        VerificationAction.ADMIT,
        VerificationAction.ADMIT,
    )
    assert threshold_actions == (
        VerificationAction.ADMIT,
        VerificationAction.STOP,
        VerificationAction.STOP,
    )
