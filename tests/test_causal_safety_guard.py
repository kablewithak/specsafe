from __future__ import annotations

import pytest

from specsafe.causal_safety import (
    ForbiddenInformationAccessError,
    assess_runtime_context,
    require_causal_runtime_context,
)
from specsafe.causal_safety.unsafe_controls import RetrospectiveEvaluationContext
from specsafe.contracts import (
    CapacityProfileSource,
    CapacitySnapshot,
    CausalSafetyStatus,
    CausalSchedulerContext,
    CausalViolationCode,
    WorkloadType,
)


def make_runtime_context() -> CausalSchedulerContext:
    return CausalSchedulerContext(
        trace_id="trace-002",
        request_id="request-002",
        workload_type=WorkloadType.OPEN_ENDED_CHAT,
        decode_round=1,
        block_position_index=2,
        visible_prefix_token_ids=(17,),
        conditional_survival_confidence=0.42,
        capacity_snapshot=CapacitySnapshot(
            profile_id="synthetic-saturated-v1",
            source=CapacityProfileSource.SYNTHETIC,
            active_request_count=64,
            verification_batch_tokens=128,
        ),
    )


def test_guard_accepts_exact_runtime_contract() -> None:
    context = make_runtime_context()

    assessment = assess_runtime_context(context)

    assert assessment.status is CausalSafetyStatus.PASS
    assert assessment.violation is None
    assert require_causal_runtime_context(context) is context


def test_guard_rejects_retrospective_context_with_future_information() -> None:
    unsafe_context = RetrospectiveEvaluationContext(
        runtime_context=make_runtime_context(),
        future_candidate_token_ids=(31, 41),
        future_acceptance_outcomes=(True, False),
    )

    assessment = assess_runtime_context(unsafe_context)

    assert assessment.status is CausalSafetyStatus.FAIL
    assert assessment.violation is not None
    assert assessment.violation.code is CausalViolationCode.FORBIDDEN_FUTURE_INFORMATION_ACCESS
    assert assessment.violation.offending_fields == (
        "future_candidate_token_ids",
        "future_acceptance_outcomes",
    )

    with pytest.raises(ForbiddenInformationAccessError) as error:
        require_causal_runtime_context(unsafe_context)

    assert error.value.violation.code is CausalViolationCode.FORBIDDEN_FUTURE_INFORMATION_ACCESS
