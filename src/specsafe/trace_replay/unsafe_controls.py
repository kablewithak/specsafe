"""Isolated retrospective replay path for the test-only causal negative control."""

from __future__ import annotations

from specsafe.causal_safety.unsafe_controls import RetrospectiveEvaluationContext
from specsafe.contracts import (
    SyntheticTraceFixtureSet,
    VerificationAction,
)
from specsafe.scheduling import UnsafeRetrospectiveLookaheadPolicy
from specsafe.trace_replay.models import (
    ReplayPositionResult,
    UnsafeRetrospectiveReplayResult,
)
from specsafe.trace_replay.replay import _select_case


def run_unsafe_retrospective_replay(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    case_id: str,
    policy: UnsafeRetrospectiveLookaheadPolicy,
    run_id: str,
) -> UnsafeRetrospectiveReplayResult:
    """Replay an intentionally invalid look-ahead policy outside valid comparison paths.

    Future candidate tokens and outcomes are exposed only here, to prove that a policy can
    appear favorable while being causally ineligible. The returned result is permanently
    marked as an invalid causal comparison.
    """

    replay_case = _select_case(fixture_set, case_id)
    outcomes_by_key = {
        (outcome.decode_round, outcome.block_position_index): outcome
        for outcome in replay_case.expected_outcomes.outcomes
    }
    contexts = replay_case.runtime_input.contexts
    ordered_outcomes = tuple(
        outcomes_by_key[(context.decode_round, context.block_position_index)]
        for context in contexts
    )

    position_results: list[ReplayPositionResult] = []
    terminal_decode_round: int | None = None
    terminal_position_index: int | None = None

    for context_index, context in enumerate(contexts):
        remaining_outcomes = ordered_outcomes[context_index:]
        retrospective_context = RetrospectiveEvaluationContext(
            runtime_context=context,
            future_candidate_token_ids=tuple(
                outcome.candidate_token_id for outcome in remaining_outcomes
            ),
            future_acceptance_outcomes=tuple(
                outcome.observed_acceptance for outcome in remaining_outcomes
            ),
        )
        decision = policy.decide(retrospective_context)
        outcome = outcomes_by_key[(context.decode_round, context.block_position_index)]
        position_results.append(
            ReplayPositionResult(decision=decision, expected_outcome=outcome)
        )
        if decision.action in {
            VerificationAction.STOP,
            VerificationAction.CONSERVATIVE_FALLBACK,
        }:
            terminal_decode_round = decision.decode_round
            terminal_position_index = decision.block_position_index
            break

    if not position_results:
        raise ValueError("unsafe retrospective replay requires at least one policy decision")

    admitted_position_count = sum(
        result.decision.action is VerificationAction.ADMIT for result in position_results
    )
    accepted_admission_count = sum(
        result.decision.action is VerificationAction.ADMIT
        and result.expected_outcome.observed_acceptance
        for result in position_results
    )
    runtime_input = replay_case.runtime_input
    return UnsafeRetrospectiveReplayResult(
        run_id=run_id,
        fixture_set_id=fixture_set.manifest.fixture_set_id,
        fixture_set_version=fixture_set.manifest.fixture_set_version,
        fixture_id=runtime_input.fixture_id,
        case_id=runtime_input.case_id,
        trace_id=runtime_input.trace_id,
        split=runtime_input.split,
        policy_id=policy.config.policy_id,
        total_runtime_position_count=len(contexts),
        position_results=tuple(position_results),
        admitted_position_count=admitted_position_count,
        accepted_admission_count=accepted_admission_count,
        rejected_admission_count=admitted_position_count - accepted_admission_count,
        terminal_decode_round=terminal_decode_round,
        terminal_position_index=terminal_position_index,
        unprocessed_position_count=len(contexts) - len(position_results),
    )
