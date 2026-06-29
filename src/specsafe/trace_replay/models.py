"""Typed result contracts for deterministic synthetic policy replay.

The contracts in this module are evaluation outputs. They are composed only after a
policy has decided from one approved :class:`CausalSchedulerContext`. They must never
be supplied to a valid runtime policy.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts import (
    CausalSafetyStatus,
    SyntheticTraceExpectedOutcome,
    TraceSplit,
    VerificationAction,
    VerificationDecision,
)
from specsafe.contracts.models import StrictContract


class ReplayValidityStatus(StrEnum):
    """Whether a replay result may support a valid policy comparison."""

    VALID_COMPARISON = "valid_comparison"
    INVALID_CAUSAL_COMPARISON = "invalid_causal_comparison"


class ReplayExecutionErrorCode(StrEnum):
    """Machine-readable failures for deterministic policy replay."""

    CASE_NOT_FOUND = "case_not_found"
    INVALID_REPLAY_INPUT = "invalid_replay_input"
    INVALID_POLICY_DECISION = "invalid_policy_decision"
    NON_CAUSAL_POLICY_DECISION = "non_causal_policy_decision"


class ReplayPositionResult(StrictContract):
    """One recorded policy decision plus labels consulted only after that decision."""

    decision: VerificationDecision
    expected_outcome: SyntheticTraceExpectedOutcome

    @model_validator(mode="after")
    def validate_decision_and_outcome_identity(self) -> ReplayPositionResult:
        """Require the post-hoc outcome to describe the exact decided position."""

        if self.decision.trace_id != self.expected_outcome.trace_id:
            raise ValueError("replay decision and expected outcome must share trace_id")
        if self.decision.decode_round != self.expected_outcome.decode_round:
            raise ValueError("replay decision and expected outcome must share decode_round")
        if self.decision.block_position_index != self.expected_outcome.block_position_index:
            raise ValueError(
                "replay decision and expected outcome must share block_position_index"
            )
        return self


class _ReplayResultBase(StrictContract):
    """Shared immutable summary fields for valid and invalid replay outputs."""

    run_id: str = Field(min_length=1, max_length=128)
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    policy_id: str = Field(min_length=1, max_length=128)
    total_runtime_position_count: int = Field(ge=1)
    position_results: tuple[ReplayPositionResult, ...] = Field(min_length=1)
    admitted_position_count: int = Field(ge=0)
    accepted_admission_count: int = Field(ge=0)
    rejected_admission_count: int = Field(ge=0)
    terminal_decode_round: int | None = Field(default=None, ge=0)
    terminal_position_index: int | None = Field(default=None, ge=1)
    unprocessed_position_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_replay_summary(self) -> _ReplayResultBase:
        """Prevent summary metrics from drifting away from retained decision evidence."""

        position_results = self.position_results
        if any(result.decision.trace_id != self.trace_id for result in position_results):
            raise ValueError("all replay decisions must use the enclosing trace_id")
        if any(result.decision.policy_id != self.policy_id for result in position_results):
            raise ValueError("all replay decisions must use the enclosing policy_id")

        actions = tuple(result.decision.action for result in position_results)
        terminal_keys = tuple(
            (result.decision.decode_round, result.decision.block_position_index)
            for result in position_results
            if result.decision.action
            in {VerificationAction.STOP, VerificationAction.CONSERVATIVE_FALLBACK}
        )
        if len(terminal_keys) > 1:
            raise ValueError("a sequential replay may contain at most one terminal decision")
        if terminal_keys and terminal_keys[0] != (
            position_results[-1].decision.decode_round,
            position_results[-1].decision.block_position_index,
        ):
            raise ValueError("a terminal decision must be the final processed replay position")
        expected_terminal_key = terminal_keys[0] if terminal_keys else None
        if self.terminal_decode_round is None and self.terminal_position_index is None:
            actual_terminal_key: tuple[int, int] | None = None
        elif self.terminal_decode_round is None or self.terminal_position_index is None:
            raise ValueError("terminal replay key must include both round and position")
        else:
            actual_terminal_key = (
                self.terminal_decode_round,
                self.terminal_position_index,
            )
        if actual_terminal_key != expected_terminal_key:
            raise ValueError("terminal replay key must match the retained terminal decision")

        admitted_count = sum(action is VerificationAction.ADMIT for action in actions)
        accepted_count = sum(
            result.decision.action is VerificationAction.ADMIT
            and result.expected_outcome.observed_acceptance
            for result in position_results
        )
        rejected_count = admitted_count - accepted_count
        if self.admitted_position_count != admitted_count:
            raise ValueError("admitted_position_count must match retained replay decisions")
        if self.accepted_admission_count != accepted_count:
            raise ValueError("accepted_admission_count must match post-hoc outcome labels")
        if self.rejected_admission_count != rejected_count:
            raise ValueError("rejected_admission_count must match post-hoc outcome labels")
        if self.total_runtime_position_count != (
            len(position_results) + self.unprocessed_position_count
        ):
            raise ValueError(
                "processed and unprocessed replay positions must equal total positions"
            )

        return self


class ValidPolicyReplayResult(_ReplayResultBase):
    """A causal replay result eligible for later comparison under shared inputs."""

    validity_status: Literal[ReplayValidityStatus.VALID_COMPARISON] = (
        ReplayValidityStatus.VALID_COMPARISON
    )
    causal_safety_status: Literal[CausalSafetyStatus.PASS] = CausalSafetyStatus.PASS

    @model_validator(mode="after")
    def validate_valid_policy_decisions(self) -> ValidPolicyReplayResult:
        """Ensure every retained decision remains causally valid."""

        if any(
            result.decision.causal_safety_status is not CausalSafetyStatus.PASS
            for result in self.position_results
        ):
            raise ValueError("valid replay results may contain only causal-pass decisions")
        return self


class UnsafeRetrospectiveReplayResult(_ReplayResultBase):
    """A test-only retrospective result that is excluded from valid comparisons."""

    validity_status: Literal[ReplayValidityStatus.INVALID_CAUSAL_COMPARISON] = (
        ReplayValidityStatus.INVALID_CAUSAL_COMPARISON
    )
    causal_safety_status: Literal[CausalSafetyStatus.FAIL] = CausalSafetyStatus.FAIL
    evaluation_only: Literal[True] = True

    @model_validator(mode="after")
    def validate_unsafe_policy_decisions(self) -> UnsafeRetrospectiveReplayResult:
        """Ensure an unsafe control cannot be relabeled as a valid replay result."""

        if any(
            result.decision.causal_safety_status is not CausalSafetyStatus.FAIL
            for result in self.position_results
        ):
            raise ValueError("unsafe replay results may contain only causal-fail decisions")
        return self
