from __future__ import annotations

import pytest
from pydantic import ValidationError

from specsafe.contracts import (
    CapacityProfileSource,
    CapacitySnapshot,
    CausalSchedulerContext,
    SyntheticTraceExpectedOutcome,
    SyntheticTraceExpectedOutcomes,
    SyntheticTraceReplayCase,
    SyntheticTraceRuntimeInput,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
    WorkloadType,
)


def make_runtime_input() -> SyntheticTraceRuntimeInput:
    return SyntheticTraceRuntimeInput(
        schema_version="synthetic-trace-runtime-input/v1",
        fixture_id="fixture-001",
        case_id="STF-001",
        trace_id="trace-001",
        request_id="request-001",
        split=TraceSplit.DEVELOPMENT,
        data_role=TraceDataRole.SYNTHETIC_FIXTURE,
        source_type=TraceSourceType.SYNTHETIC,
        generation_note="Self-authored synthetic contract test fixture.",
        contexts=(
            CausalSchedulerContext(
                trace_id="trace-001",
                request_id="request-001",
                workload_type=WorkloadType.CODE,
                decode_round=0,
                block_position_index=1,
                conditional_survival_confidence=0.9,
                capacity_snapshot=CapacitySnapshot(
                    profile_id="synthetic-light-v1",
                    source=CapacityProfileSource.SYNTHETIC,
                    active_request_count=1,
                    verification_batch_tokens=0,
                ),
            ),
            CausalSchedulerContext(
                trace_id="trace-001",
                request_id="request-001",
                workload_type=WorkloadType.CODE,
                decode_round=0,
                block_position_index=2,
                visible_prefix_token_ids=(101,),
                conditional_survival_confidence=0.8,
                capacity_snapshot=CapacitySnapshot(
                    profile_id="synthetic-light-v1",
                    source=CapacityProfileSource.SYNTHETIC,
                    active_request_count=1,
                    verification_batch_tokens=1,
                ),
            ),
        ),
    )


def make_expected_outcomes() -> SyntheticTraceExpectedOutcomes:
    return SyntheticTraceExpectedOutcomes(
        schema_version="synthetic-trace-runtime-input/v1",
        fixture_id="fixture-001",
        case_id="STF-001",
        trace_id="trace-001",
        split=TraceSplit.DEVELOPMENT,
        data_role=TraceDataRole.SYNTHETIC_FIXTURE,
        source_type=TraceSourceType.SYNTHETIC,
        outcomes=(
            SyntheticTraceExpectedOutcome(
                trace_id="trace-001",
                decode_round=0,
                block_position_index=1,
                candidate_token_id=101,
                observed_acceptance=True,
                prefix_survival_label=True,
            ),
            SyntheticTraceExpectedOutcome(
                trace_id="trace-001",
                decode_round=0,
                block_position_index=2,
                candidate_token_id=102,
                observed_acceptance=False,
                prefix_survival_label=False,
            ),
        ),
    )


def test_runtime_input_rejects_evaluation_only_outcomes() -> None:
    payload = make_runtime_input().model_dump()
    payload["observed_acceptance"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SyntheticTraceRuntimeInput.model_validate(payload)


def test_replay_case_requires_runtime_prefix_to_match_prior_outcome_token() -> None:
    runtime_input = make_runtime_input()
    outcomes = make_expected_outcomes()

    replay_case = SyntheticTraceReplayCase(
        runtime_input=runtime_input,
        expected_outcomes=outcomes,
    )

    assert replay_case.runtime_input.contexts[1].visible_prefix_token_ids == (101,)
    assert replay_case.expected_outcomes.outcomes[1].candidate_token_id == 102


def test_replay_case_rejects_misaligned_runtime_prefix() -> None:
    runtime_payload = make_runtime_input().model_dump()
    runtime_payload["contexts"][1]["visible_prefix_token_ids"] = (999,)
    runtime_input = SyntheticTraceRuntimeInput.model_validate(runtime_payload)

    with pytest.raises(ValidationError, match="runtime visible_prefix_token_ids"):
        SyntheticTraceReplayCase(
            runtime_input=runtime_input,
            expected_outcomes=make_expected_outcomes(),
        )


def test_expected_outcomes_require_cumulative_prefix_survival_labels() -> None:
    payload = make_expected_outcomes().model_dump()
    payload["outcomes"][1]["prefix_survival_label"] = True

    with pytest.raises(ValidationError, match="prefix_survival_label"):
        SyntheticTraceExpectedOutcomes.model_validate(payload)
