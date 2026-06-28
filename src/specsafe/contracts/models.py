"""Typed contracts for SpecSafe causal scheduling experiments.

These models form the policy boundary between trace-derived confidence signals and
runtime scheduling decisions. They intentionally exclude future sampled tokens and
verification outcomes from valid runtime contexts.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictContract(BaseModel):
    """Immutable, schema-strict base model for core policy boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class WorkloadType(StrEnum):
    """High-level workload grouping used by later evaluation fixtures."""

    STRUCTURED_TEXT = "structured_text"
    CODE = "code"
    OPEN_ENDED_CHAT = "open_ended_chat"


class CapacityProfileSource(StrEnum):
    """Evidence source for a capacity profile."""

    SYNTHETIC = "synthetic"
    KAGGLE_MEASURED = "kaggle_measured"


class VerificationAction(StrEnum):
    """A bounded verification action available to a future policy."""

    ADMIT = "admit"
    STOP = "stop"
    CONSERVATIVE_FALLBACK = "conservative_fallback"


class CausalSafetyStatus(StrEnum):
    """Whether a decision context meets the causal runtime boundary."""

    PASS = "pass"
    FAIL = "fail"


class CausalViolationCode(StrEnum):
    """Machine-readable reasons a context may be rejected."""

    FORBIDDEN_FUTURE_INFORMATION_ACCESS = "forbidden_future_information_access"
    UNAPPROVED_RUNTIME_CONTEXT_TYPE = "unapproved_runtime_context_type"
    INVALID_VISIBLE_PREFIX = "invalid_visible_prefix"


class CapacitySnapshot(StrictContract):
    """The capacity state visible to a scheduler at a decision point."""

    profile_id: str = Field(min_length=1, max_length=128)
    source: CapacityProfileSource
    active_request_count: int = Field(ge=1)
    verification_batch_tokens: int = Field(ge=0)


class CausalSchedulerContext(StrictContract):
    """Information legally visible before admitting the next block position.

    ``block_position_index`` is one-based and local to the speculative block. The
    current candidate token value and every future token or verification outcome are
    intentionally absent. A valid scheduler must make its decision using this context
    only.
    """

    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    workload_type: WorkloadType
    decode_round: int = Field(ge=0)
    block_position_index: int = Field(ge=1)
    visible_prefix_token_ids: tuple[int, ...] = ()
    conditional_survival_confidence: float = Field(ge=0.0, le=1.0)
    capacity_snapshot: CapacitySnapshot

    @field_validator("visible_prefix_token_ids")
    @classmethod
    def validate_visible_token_ids(cls, token_ids: tuple[int, ...]) -> tuple[int, ...]:
        """Token IDs are non-negative implementation identifiers."""

        if any(token_id < 0 for token_id in token_ids):
            raise ValueError("visible_prefix_token_ids must contain only non-negative token IDs")
        return token_ids

    @model_validator(mode="after")
    def validate_prefix_matches_position(self) -> CausalSchedulerContext:
        """Ensure the visible prefix is exactly the history before this decision."""

        expected_position = len(self.visible_prefix_token_ids) + 1
        if self.block_position_index != expected_position:
            raise ValueError(
                "block_position_index must equal len(visible_prefix_token_ids) + 1 "
                f"(expected {expected_position}, got {self.block_position_index})"
            )
        return self


class VerificationDecision(StrictContract):
    """Typed output contract for a future scheduling policy."""

    policy_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    block_position_index: int = Field(ge=1)
    action: VerificationAction
    reason_code: str = Field(min_length=1, max_length=128)
    expected_marginal_utility: float | None = None
    causal_safety_status: CausalSafetyStatus = CausalSafetyStatus.PASS


class CausalSafetyViolation(StrictContract):
    """Machine-readable explanation of a rejected runtime context."""

    code: CausalViolationCode
    message: str = Field(min_length=1, max_length=500)
    offending_fields: tuple[str, ...] = ()


class CausalSafetyAssessment(StrictContract):
    """Assessment returned by the causal runtime gate."""

    status: CausalSafetyStatus
    violation: CausalSafetyViolation | None = None

    @model_validator(mode="after")
    def validate_status_and_violation(self) -> CausalSafetyAssessment:
        """A failing assessment must explain itself; a pass may not invent a violation."""

        if self.status is CausalSafetyStatus.FAIL and self.violation is None:
            raise ValueError("a failed causal-safety assessment requires a violation")
        if self.status is CausalSafetyStatus.PASS and self.violation is not None:
            raise ValueError("a passing causal-safety assessment cannot contain a violation")
        return self
