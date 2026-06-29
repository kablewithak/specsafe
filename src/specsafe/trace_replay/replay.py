"""Deterministic, causal replay of one policy against immutable synthetic traces."""

from __future__ import annotations

from typing import Protocol

from specsafe.causal_safety import require_causal_runtime_context
from specsafe.contracts import (
    CausalSafetyStatus,
    CausalSchedulerContext,
    SyntheticTraceFixtureSet,
    SyntheticTraceReplayCase,
    VerificationAction,
    VerificationDecision,
)
from specsafe.trace_replay.models import (
    ReplayExecutionErrorCode,
    ReplayPositionResult,
    ValidPolicyReplayResult,
)


class CausalReplayPolicy(Protocol):
    """Minimal interface for a valid policy that decides from causal context only."""

    def decide(self, context: CausalSchedulerContext) -> VerificationDecision:
        """Return a typed decision for one causal runtime context."""


class DeterministicReplayExecutionError(ValueError):
    """Raised when replay evidence cannot be retained as a valid causal comparison."""

    def __init__(self, code: ReplayExecutionErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def run_valid_policy_replay(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    case_id: str,
    policy: CausalReplayPolicy,
    run_id: str,
) -> ValidPolicyReplayResult:
    """Replay one valid policy sequentially against exactly one immutable fixture case.

    The policy receives only each existing ``CausalSchedulerContext``. Expected outcomes are
    attached to retained output records only after the corresponding policy decision exists.
    A decision marked causally invalid rejects the entire valid replay path.
    """

    if _policy_is_evaluation_only(policy):
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.INVALID_REPLAY_INPUT,
            "an evaluation-only policy cannot enter the valid replay path",
        )

    replay_case = _select_case(fixture_set, case_id)
    outcomes_by_key = {
        (outcome.decode_round, outcome.block_position_index): outcome
        for outcome in replay_case.expected_outcomes.outcomes
    }

    position_results: list[ReplayPositionResult] = []
    policy_id: str | None = None
    terminal_decode_round: int | None = None
    terminal_position_index: int | None = None

    for context in replay_case.runtime_input.contexts:
        approved_context = require_causal_runtime_context(context)
        decision = policy.decide(approved_context)
        _validate_valid_policy_decision(approved_context, decision, policy_id)

        outcome = outcomes_by_key[(context.decode_round, context.block_position_index)]
        position_results.append(
            ReplayPositionResult(decision=decision, expected_outcome=outcome)
        )
        policy_id = decision.policy_id

        if decision.action in {
            VerificationAction.STOP,
            VerificationAction.CONSERVATIVE_FALLBACK,
        }:
            terminal_decode_round = decision.decode_round
            terminal_position_index = decision.block_position_index
            break

    if not position_results or policy_id is None:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.INVALID_REPLAY_INPUT,
            "replay requires at least one runtime context and one policy decision",
        )

    return _build_valid_result(
        fixture_set=fixture_set,
        replay_case=replay_case,
        run_id=run_id,
        policy_id=policy_id,
        position_results=tuple(position_results),
        terminal_decode_round=terminal_decode_round,
        terminal_position_index=terminal_position_index,
    )


def _policy_is_evaluation_only(policy: object) -> bool:
    """Block controls whose immutable configuration explicitly marks them test-only."""

    config = getattr(policy, "config", None)
    return getattr(config, "evaluation_only", False) is True


def _select_case(
    fixture_set: SyntheticTraceFixtureSet,
    case_id: str,
) -> SyntheticTraceReplayCase:
    """Select one case by identity without changing fixture ordering or contents."""

    if type(fixture_set) is not SyntheticTraceFixtureSet:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.INVALID_REPLAY_INPUT,
            "replay requires the exact SyntheticTraceFixtureSet contract",
        )

    matching_cases = tuple(
        case for case in fixture_set.cases if case.runtime_input.case_id == case_id
    )
    if len(matching_cases) != 1:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.CASE_NOT_FOUND,
            f"fixture set does not contain exactly one case with case_id={case_id!r}",
        )
    return matching_cases[0]


def _validate_valid_policy_decision(
    context: CausalSchedulerContext,
    decision: object,
    policy_id: str | None,
) -> None:
    """Reject malformed, non-causal, or cross-position decisions before scoring labels."""

    if type(decision) is not VerificationDecision:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.INVALID_POLICY_DECISION,
            "valid policy replay requires the exact VerificationDecision contract",
        )
    if decision.causal_safety_status is not CausalSafetyStatus.PASS:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.NON_CAUSAL_POLICY_DECISION,
            "a causally invalid decision cannot enter the valid replay path",
        )
    if decision.trace_id != context.trace_id:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.INVALID_POLICY_DECISION,
            "policy decision trace_id must match the runtime context",
        )
    if decision.decode_round != context.decode_round:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.INVALID_POLICY_DECISION,
            "policy decision decode_round must match the runtime context",
        )
    if decision.block_position_index != context.block_position_index:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.INVALID_POLICY_DECISION,
            "policy decision block_position_index must match the runtime context",
        )
    if policy_id is not None and decision.policy_id != policy_id:
        raise DeterministicReplayExecutionError(
            ReplayExecutionErrorCode.INVALID_POLICY_DECISION,
            "all decisions in one replay must share a policy_id",
        )


def _build_valid_result(
    *,
    fixture_set: SyntheticTraceFixtureSet,
    replay_case: SyntheticTraceReplayCase,
    run_id: str,
    policy_id: str,
    position_results: tuple[ReplayPositionResult, ...],
    terminal_decode_round: int | None,
    terminal_position_index: int | None,
) -> ValidPolicyReplayResult:
    """Compute label-derived replay summaries only after decision records are retained."""

    admitted_position_count = sum(
        result.decision.action is VerificationAction.ADMIT for result in position_results
    )
    accepted_admission_count = sum(
        result.decision.action is VerificationAction.ADMIT
        and result.expected_outcome.observed_acceptance
        for result in position_results
    )
    runtime_input = replay_case.runtime_input
    return ValidPolicyReplayResult(
        run_id=run_id,
        fixture_set_id=fixture_set.manifest.fixture_set_id,
        fixture_set_version=fixture_set.manifest.fixture_set_version,
        fixture_id=runtime_input.fixture_id,
        case_id=runtime_input.case_id,
        trace_id=runtime_input.trace_id,
        split=runtime_input.split,
        policy_id=policy_id,
        total_runtime_position_count=len(runtime_input.contexts),
        position_results=position_results,
        admitted_position_count=admitted_position_count,
        accepted_admission_count=accepted_admission_count,
        rejected_admission_count=admitted_position_count - accepted_admission_count,
        terminal_decode_round=terminal_decode_round,
        terminal_position_index=terminal_position_index,
        unprocessed_position_count=len(runtime_input.contexts) - len(position_results),
    )
