from __future__ import annotations

from pathlib import Path

import pytest

from specsafe.contracts import (
    CausalSafetyStatus,
    TraceSplit,
    VerificationAction,
    VerificationDecision,
)
from specsafe.scheduling import (
    FixedLengthPolicyConfig,
    FixedLengthVerificationPolicy,
    StaticThresholdPolicyConfig,
    StaticThresholdVerificationPolicy,
    UnsafeRetrospectiveLookaheadPolicy,
)
from specsafe.trace_replay import (
    DeterministicReplayExecutionError,
    ReplayExecutionErrorCode,
    ReplayValidityStatus,
    run_unsafe_retrospective_replay,
    run_valid_policy_replay,
)
from specsafe.traces import load_synthetic_trace_fixture_set

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_trace_baselines"
)


class NonCausalDecisionPolicy:
    """Test double that proves invalid decisions cannot enter a valid replay result."""

    def decide(self, context: object) -> VerificationDecision:
        assert hasattr(context, "trace_id")
        return VerificationDecision(
            policy_id="non-causal-test-policy",
            trace_id=context.trace_id,
            decode_round=context.decode_round,
            block_position_index=context.block_position_index,
            action=VerificationAction.ADMIT,
            reason_code="test_only_non_causal_decision",
            causal_safety_status=CausalSafetyStatus.FAIL,
        )


class WrongPositionPolicy:
    """Test double that returns a decision for a different candidate position."""

    def decide(self, context: object) -> VerificationDecision:
        assert hasattr(context, "trace_id")
        return VerificationDecision(
            policy_id="wrong-position-test-policy",
            trace_id=context.trace_id,
            decode_round=context.decode_round,
            block_position_index=context.block_position_index + 1,
            action=VerificationAction.ADMIT,
            reason_code="test_only_wrong_position",
        )


def load_fixture_set():
    return load_synthetic_trace_fixture_set(FIXTURE_ROOT)


def test_fixed_length_replay_is_deterministic_and_scores_post_hoc_outcomes() -> None:
    fixture_set = load_fixture_set()
    policy = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(maximum_verification_length=3)
    )

    first_result = run_valid_policy_replay(
        fixture_set,
        case_id="STF-001",
        policy=policy,
        run_id="fixed-length-stf-001-v1",
    )
    second_result = run_valid_policy_replay(
        fixture_set,
        case_id="STF-001",
        policy=policy,
        run_id="fixed-length-stf-001-v1",
    )

    assert first_result == second_result
    assert first_result.validity_status is ReplayValidityStatus.VALID_COMPARISON
    assert first_result.causal_safety_status is CausalSafetyStatus.PASS
    assert first_result.split is TraceSplit.DEVELOPMENT
    assert tuple(result.decision.action for result in first_result.position_results) == (
        VerificationAction.ADMIT,
        VerificationAction.ADMIT,
        VerificationAction.ADMIT,
        VerificationAction.STOP,
    )
    assert first_result.admitted_position_count == 3
    assert first_result.accepted_admission_count == 3
    assert first_result.rejected_admission_count == 0
    assert first_result.terminal_decode_round == 0
    assert first_result.terminal_position_index == 4
    assert first_result.unprocessed_position_count == 0


def test_static_threshold_replay_stops_without_deciding_later_positions() -> None:
    fixture_set = load_fixture_set()
    policy = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(minimum_conditional_survival_confidence=0.4)
    )

    result = run_valid_policy_replay(
        fixture_set,
        case_id="STF-002",
        policy=policy,
        run_id="static-threshold-stf-002-v1",
    )

    assert tuple(result.decision.action for result in result.position_results) == (
        VerificationAction.ADMIT,
        VerificationAction.STOP,
    )
    assert result.admitted_position_count == 1
    assert result.accepted_admission_count == 1
    assert result.rejected_admission_count == 0
    assert result.terminal_decode_round == 0
    assert result.terminal_position_index == 2
    assert result.unprocessed_position_count == 1


def test_fixed_policy_replays_final_evaluation_with_predeclared_configuration() -> None:
    fixture_set = load_fixture_set()
    policy = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(maximum_verification_length=4)
    )

    result = run_valid_policy_replay(
        fixture_set,
        case_id="STF-004",
        policy=policy,
        run_id="fixed-length-stf-004-v1",
    )

    assert result.split is TraceSplit.FINAL_EVALUATION
    assert result.admitted_position_count == 4
    assert result.accepted_admission_count == 4
    assert result.terminal_position_index is None
    assert result.unprocessed_position_count == 0


def test_valid_replay_blocks_the_explicitly_evaluation_only_policy() -> None:
    fixture_set = load_fixture_set()

    with pytest.raises(DeterministicReplayExecutionError) as error:
        run_valid_policy_replay(
            fixture_set,
            case_id="STF-003",
            policy=UnsafeRetrospectiveLookaheadPolicy(),
            run_id="blocked-unsafe-replay-v1",
        )

    assert error.value.code is ReplayExecutionErrorCode.INVALID_REPLAY_INPUT


def test_valid_replay_rejects_a_policy_that_marks_its_decision_non_causal() -> None:
    fixture_set = load_fixture_set()

    with pytest.raises(DeterministicReplayExecutionError) as error:
        run_valid_policy_replay(
            fixture_set,
            case_id="STF-001",
            policy=NonCausalDecisionPolicy(),
            run_id="invalid-decision-replay-v1",
        )

    assert error.value.code is ReplayExecutionErrorCode.NON_CAUSAL_POLICY_DECISION


def test_valid_replay_rejects_a_cross_position_decision_before_scoring() -> None:
    fixture_set = load_fixture_set()

    with pytest.raises(DeterministicReplayExecutionError) as error:
        run_valid_policy_replay(
            fixture_set,
            case_id="STF-001",
            policy=WrongPositionPolicy(),
            run_id="wrong-position-replay-v1",
        )

    assert error.value.code is ReplayExecutionErrorCode.INVALID_POLICY_DECISION


def test_unsafe_retrospective_replay_is_explicitly_excluded_from_valid_comparisons() -> None:
    fixture_set = load_fixture_set()

    result = run_unsafe_retrospective_replay(
        fixture_set,
        case_id="STF-003",
        policy=UnsafeRetrospectiveLookaheadPolicy(),
        run_id="unsafe-retrospective-stf-003-v1",
    )

    assert result.validity_status is ReplayValidityStatus.INVALID_CAUSAL_COMPARISON
    assert result.causal_safety_status is CausalSafetyStatus.FAIL
    assert result.evaluation_only is True
    assert tuple(item.decision.action for item in result.position_results) == (
        VerificationAction.ADMIT,
        VerificationAction.STOP,
    )
    assert result.accepted_admission_count == 1
    assert result.unprocessed_position_count == 2
