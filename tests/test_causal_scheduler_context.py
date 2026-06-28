from __future__ import annotations

import pytest
from pydantic import ValidationError

from specsafe.contracts import (
    CapacityProfileSource,
    CapacitySnapshot,
    CausalSchedulerContext,
    WorkloadType,
)


def make_capacity_snapshot() -> CapacitySnapshot:
    return CapacitySnapshot(
        profile_id="synthetic-moderate-v1",
        source=CapacityProfileSource.SYNTHETIC,
        active_request_count=8,
        verification_batch_tokens=32,
    )


def test_causal_context_accepts_only_visible_prefix_information() -> None:
    context = CausalSchedulerContext(
        trace_id="trace-001",
        request_id="request-001",
        workload_type=WorkloadType.CODE,
        decode_round=2,
        block_position_index=3,
        visible_prefix_token_ids=(101, 202),
        conditional_survival_confidence=0.73,
        capacity_snapshot=make_capacity_snapshot(),
    )

    assert context.block_position_index == 3
    assert context.visible_prefix_token_ids == (101, 202)


def test_causal_context_rejects_future_information_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CausalSchedulerContext(
            trace_id="trace-001",
            request_id="request-001",
            workload_type=WorkloadType.CODE,
            decode_round=0,
            block_position_index=1,
            conditional_survival_confidence=0.73,
            capacity_snapshot=make_capacity_snapshot(),
            future_candidate_token_ids=(999,),
        )


def test_causal_context_requires_prefix_length_to_match_position() -> None:
    with pytest.raises(ValidationError, match="block_position_index must equal"):
        CausalSchedulerContext(
            trace_id="trace-001",
            request_id="request-001",
            workload_type=WorkloadType.STRUCTURED_TEXT,
            decode_round=0,
            block_position_index=3,
            visible_prefix_token_ids=(101,),
            conditional_survival_confidence=0.61,
            capacity_snapshot=make_capacity_snapshot(),
        )
