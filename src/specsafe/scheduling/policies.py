"""Blunt valid baselines and an explicitly invalid retrospective control.

Valid policies accept an object only so the existing causal gate can reject accidental
non-causal inputs. After the gate passes, they use the exact CausalSchedulerContext and
never consume replay outcomes, sampled candidate tokens, or later decision state.

The unsafe policy is intentionally isolated: it accepts only the test-only
RetrospectiveEvaluationContext, marks every decision as causally invalid, and must never
be used by a valid replay or promotion path.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from specsafe.causal_safety import require_causal_runtime_context
from specsafe.causal_safety.unsafe_controls import RetrospectiveEvaluationContext
from specsafe.contracts import (
    CausalSafetyStatus,
    CausalSchedulerContext,
    VerificationAction,
    VerificationDecision,
)
from specsafe.contracts.models import StrictContract


class FixedLengthPolicyConfig(StrictContract):
    """Configuration for the capacity-blind fixed verification-length baseline."""

    policy_id: str = Field(default="fixed-length-v1", min_length=1, max_length=128)
    maximum_verification_length: int = Field(ge=1)


class StaticThresholdPolicyConfig(StrictContract):
    """Configuration for the causal but capacity-blind threshold baseline."""

    policy_id: str = Field(default="static-threshold-v1", min_length=1, max_length=128)
    minimum_conditional_survival_confidence: float = Field(ge=0.0, le=1.0)


class UnsafeRetrospectivePolicyConfig(StrictContract):
    """Configuration that permanently labels a look-ahead control as test-only."""

    policy_id: str = Field(
        default="unsafe-retrospective-lookahead-v1",
        min_length=1,
        max_length=128,
    )
    evaluation_only: Literal[True] = True


class FixedLengthVerificationPolicy:
    """Admit positions at or below a configured fixed verification budget."""

    def __init__(self, config: FixedLengthPolicyConfig) -> None:
        self._config = config

    @property
    def config(self) -> FixedLengthPolicyConfig:
        """Return the immutable policy configuration for evidence retention."""

        return self._config

    def decide(self, context: object) -> VerificationDecision:
        """Make a causal fixed-budget decision from the exact runtime contract."""

        approved_context = require_causal_runtime_context(context)
        if approved_context.block_position_index <= self._config.maximum_verification_length:
            return _valid_decision(
                policy_id=self._config.policy_id,
                context=approved_context,
                action=VerificationAction.ADMIT,
                reason_code="fixed_length_within_budget",
            )
        return _valid_decision(
            policy_id=self._config.policy_id,
            context=approved_context,
            action=VerificationAction.STOP,
            reason_code="fixed_length_budget_exhausted",
        )


class StaticThresholdVerificationPolicy:
    """Admit positions only when their lawful confidence meets a static threshold."""

    def __init__(self, config: StaticThresholdPolicyConfig) -> None:
        self._config = config

    @property
    def config(self) -> StaticThresholdPolicyConfig:
        """Return the immutable policy configuration for evidence retention."""

        return self._config

    def decide(self, context: object) -> VerificationDecision:
        """Make a causal threshold decision without looking at capacity or outcomes."""

        approved_context = require_causal_runtime_context(context)
        if (
            approved_context.conditional_survival_confidence
            >= self._config.minimum_conditional_survival_confidence
        ):
            return _valid_decision(
                policy_id=self._config.policy_id,
                context=approved_context,
                action=VerificationAction.ADMIT,
                reason_code="static_threshold_met",
            )
        return _valid_decision(
            policy_id=self._config.policy_id,
            context=approved_context,
            action=VerificationAction.STOP,
            reason_code="static_threshold_below_minimum",
        )


class UnsafeRetrospectiveLookaheadPolicy:
    """Evaluation-only negative control that deliberately reads future outcomes.

    This class does not satisfy the valid-policy boundary. Its decisions are marked FAIL
    even where it appears to make a favorable choice from unavailable future evidence.
    """

    def __init__(self, config: UnsafeRetrospectivePolicyConfig | None = None) -> None:
        self._config = config or UnsafeRetrospectivePolicyConfig()

    @property
    def config(self) -> UnsafeRetrospectivePolicyConfig:
        """Return the immutable configuration proving this control is test-only."""

        return self._config

    def decide(self, context: object) -> VerificationDecision:
        """Use forbidden future outcomes only to demonstrate an invalid control path."""

        if type(context) is not RetrospectiveEvaluationContext:
            raise TypeError(
                "unsafe retrospective policy requires the exact "
                "RetrospectiveEvaluationContext test-only contract"
            )

        runtime_context = context.runtime_context
        if not context.future_acceptance_outcomes:
            return _unsafe_decision(
                policy_id=self._config.policy_id,
                context=runtime_context,
                action=VerificationAction.STOP,
                reason_code="unsafe_no_future_outcome",
            )

        next_outcome = context.future_acceptance_outcomes[0]
        action = VerificationAction.ADMIT if next_outcome else VerificationAction.STOP
        reason_code = (
            "unsafe_future_outcome_admit"
            if next_outcome
            else "unsafe_future_outcome_stop"
        )
        return _unsafe_decision(
            policy_id=self._config.policy_id,
            context=runtime_context,
            action=action,
            reason_code=reason_code,
        )


def _valid_decision(
    *,
    policy_id: str,
    context: CausalSchedulerContext,
    action: VerificationAction,
    reason_code: str,
) -> VerificationDecision:
    """Build a decision whose causal status is valid by construction."""

    return VerificationDecision(
        policy_id=policy_id,
        trace_id=context.trace_id,
        decode_round=context.decode_round,
        block_position_index=context.block_position_index,
        action=action,
        reason_code=reason_code,
        causal_safety_status=CausalSafetyStatus.PASS,
    )


def _unsafe_decision(
    *,
    policy_id: str,
    context: CausalSchedulerContext,
    action: VerificationAction,
    reason_code: str,
) -> VerificationDecision:
    """Build a decision that cannot be mistaken for a valid policy result."""

    return VerificationDecision(
        policy_id=policy_id,
        trace_id=context.trace_id,
        decode_round=context.decode_round,
        block_position_index=context.block_position_index,
        action=action,
        reason_code=reason_code,
        causal_safety_status=CausalSafetyStatus.FAIL,
    )
