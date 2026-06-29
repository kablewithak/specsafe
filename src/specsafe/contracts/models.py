"""Typed contracts for SpecSafe causal scheduling and trace-replay experiments.

These models separate scheduler-visible inputs from evaluation-only outcomes. Runtime
policies receive only :class:`CausalSchedulerContext`; replay loaders may compose that
context with outcomes after a decision has been recorded.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictContract(BaseModel):
    """Immutable, schema-strict base model for core policy boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class WorkloadType(StrEnum):
    """High-level workload grouping used by evaluation fixtures."""

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


class TraceSplit(StrEnum):
    """Governed trace split roles for local replay evidence."""

    DEVELOPMENT = "development"
    CALIBRATION = "calibration"
    FINAL_EVALUATION = "final_evaluation"
    ADVERSARIAL_REGRESSION = "adversarial_regression"


class TraceDataRole(StrEnum):
    """Primary role assigned to a trace artifact in the data-role ledger."""

    SYNTHETIC_FIXTURE = "synthetic_fixture"
    TRACE_COLLECTION = "trace_collection"
    CALIBRATION = "calibration"
    POLICY_TUNING = "policy_tuning"
    HELD_OUT_EVALUATION = "held_out_evaluation"
    PUBLIC_DEMONSTRATION = "public_demonstration"


class TraceSourceType(StrEnum):
    """Provenance category for trace fixtures and exports."""

    SYNTHETIC = "synthetic"
    KAGGLE_EXPORT = "kaggle_export"


class TraceArtifactKind(StrEnum):
    """Structural separation between policy inputs and post-hoc evidence."""

    RUNTIME_INPUT = "runtime_input"
    EXPECTED_OUTCOMES = "expected_outcomes"


class TraceFixtureViolationCode(StrEnum):
    """Machine-readable loader and fixture-validation failure labels."""

    TRACE_SCHEMA_ERROR = "trace_schema_error"
    TRACE_MANIFEST_MISMATCH = "trace_manifest_mismatch"
    TRACE_PROVENANCE_MISMATCH = "trace_provenance_mismatch"


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


class SyntheticTraceRuntimeInput(StrictContract):
    """Scheduler-visible positions for one synthetic trace case.

    This object intentionally contains no sampled candidate token IDs, acceptance labels,
    prefix-survival labels, or retrospective outcomes. Policies must consume individual
    ``CausalSchedulerContext`` values from ``contexts`` rather than this fixture wrapper.
    """

    schema_version: str = Field(min_length=1, max_length=64)
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    data_role: TraceDataRole
    source_type: TraceSourceType
    generation_note: str = Field(min_length=1, max_length=500)
    contexts: tuple[CausalSchedulerContext, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_context_provenance_and_order(self) -> SyntheticTraceRuntimeInput:
        """Make each fixture deterministic and internally consistent before replay."""

        seen_keys: set[tuple[int, int]] = set()
        prior_key: tuple[int, int] | None = None

        for context in self.contexts:
            if context.trace_id != self.trace_id:
                raise ValueError("all runtime contexts must use the enclosing trace_id")
            if context.request_id != self.request_id:
                raise ValueError("all runtime contexts must use the enclosing request_id")

            key = (context.decode_round, context.block_position_index)
            if key in seen_keys:
                raise ValueError("runtime contexts must not repeat a decode-round/position key")
            if prior_key is not None and key < prior_key:
                raise ValueError(
                    "runtime contexts must be ordered by decode_round and "
                    "block_position_index"
                )
            seen_keys.add(key)
            prior_key = key

        return self


class SyntheticTraceExpectedOutcome(StrictContract):
    """Evaluation-only result for a candidate position after a runtime decision exists."""

    trace_id: str = Field(min_length=1, max_length=128)
    decode_round: int = Field(ge=0)
    block_position_index: int = Field(ge=1)
    candidate_token_id: int = Field(ge=0)
    observed_acceptance: bool
    prefix_survival_label: bool


class SyntheticTraceExpectedOutcomes(StrictContract):
    """Post-hoc outcome labels structurally separate from runtime fixture inputs."""

    schema_version: str = Field(min_length=1, max_length=64)
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    data_role: TraceDataRole
    source_type: TraceSourceType
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_outcome_order_and_prefix_labels(self) -> SyntheticTraceExpectedOutcomes:
        """Ensure labels are complete, ordered, and coherent for replay scoring."""

        outcomes_by_round: dict[int, list[SyntheticTraceExpectedOutcome]] = {}
        for outcome in self.outcomes:
            if outcome.trace_id != self.trace_id:
                raise ValueError("all expected outcomes must use the enclosing trace_id")
            outcomes_by_round.setdefault(outcome.decode_round, []).append(outcome)

        for round_outcomes in outcomes_by_round.values():
            expected_position = 1
            prefix_survives = True
            for outcome in round_outcomes:
                if outcome.block_position_index != expected_position:
                    raise ValueError(
                        "expected outcomes must have contiguous positions "
                        "beginning at one per decode round"
                    )
                prefix_survives = prefix_survives and outcome.observed_acceptance
                if outcome.prefix_survival_label is not prefix_survives:
                    raise ValueError(
                        "prefix_survival_label must equal cumulative observed "
                        "acceptance within its round"
                    )
                expected_position += 1

        return self


class SyntheticTraceReplayCase(StrictContract):
    """A validated replay case composed only after inputs and labels are loaded separately."""

    runtime_input: SyntheticTraceRuntimeInput
    expected_outcomes: SyntheticTraceExpectedOutcomes

    @model_validator(mode="after")
    def validate_runtime_and_outcome_alignment(self) -> SyntheticTraceReplayCase:
        """Verify post-hoc labels line up without exposing them to runtime policy calls."""

        runtime = self.runtime_input
        outcomes = self.expected_outcomes
        aligned_fields = (
            "schema_version",
            "fixture_id",
            "case_id",
            "trace_id",
            "split",
            "data_role",
            "source_type",
        )
        for field_name in aligned_fields:
            if getattr(runtime, field_name) != getattr(outcomes, field_name):
                raise ValueError(f"runtime input and expected outcomes disagree on {field_name}")

        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in runtime.contexts
        }
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in outcomes.outcomes
        }
        if set(contexts_by_key) != set(outcomes_by_key):
            raise ValueError(
                "runtime contexts and expected outcomes must have identical "
                "position keys"
            )

        outcomes_by_round: dict[int, list[SyntheticTraceExpectedOutcome]] = {}
        for outcome in outcomes.outcomes:
            outcomes_by_round.setdefault(outcome.decode_round, []).append(outcome)

        for decode_round, round_outcomes in outcomes_by_round.items():
            expected_prefix: tuple[int, ...] = ()
            for outcome in round_outcomes:
                context = contexts_by_key[(decode_round, outcome.block_position_index)]
                if context.visible_prefix_token_ids != expected_prefix:
                    raise ValueError(
                        "runtime visible_prefix_token_ids must match prior candidate tokens from "
                        "evaluation-only outcomes"
                    )
                expected_prefix = (*expected_prefix, outcome.candidate_token_id)

        return self


class FixtureSplitCount(StrictContract):
    """Count of logical cases assigned to one governed split."""

    split: TraceSplit
    case_count: int = Field(ge=0)


class SyntheticTraceFixtureManifestEntry(StrictContract):
    """Hash-addressed manifest record for one runtime-input or outcome artifact."""

    artifact_kind: TraceArtifactKind
    relative_path: str = Field(min_length=1, max_length=300)
    case_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    data_role: TraceDataRole
    source_type: TraceSourceType
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        """Reject absolute and parent-traversal paths from repository manifests."""

        normalized = value.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
            raise ValueError("relative_path must remain inside the fixture root")
        return normalized


class SyntheticTraceFixtureManifest(StrictContract):
    """Versioned, hash-verified inventory for one synthetic trace fixture set."""

    schema_version: str = Field(min_length=1, max_length=64)
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    source_type: TraceSourceType
    generation_note: str = Field(min_length=1, max_length=500)
    case_count: int = Field(gt=0)
    split_counts: tuple[FixtureSplitCount, ...] = Field(min_length=1)
    entries: tuple[SyntheticTraceFixtureManifestEntry, ...] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_manifest_shape(self) -> SyntheticTraceFixtureManifest:
        """Require one runtime input and one outcome artifact for every logical case."""

        entry_keys = {(entry.case_id, entry.artifact_kind) for entry in self.entries}
        if len(entry_keys) != len(self.entries):
            raise ValueError("manifest entries must not repeat a case_id/artifact_kind pair")

        case_ids = {entry.case_id for entry in self.entries}
        if len(case_ids) != self.case_count:
            raise ValueError("case_count must equal the number of unique manifest case IDs")

        for case_id in case_ids:
            kinds = {entry.artifact_kind for entry in self.entries if entry.case_id == case_id}
            if kinds != {TraceArtifactKind.RUNTIME_INPUT, TraceArtifactKind.EXPECTED_OUTCOMES}:
                raise ValueError(
                    "each case must include exactly one runtime input and "
                    "expected outcomes"
                )

        split_count_map = {count.split: count.case_count for count in self.split_counts}
        if len(split_count_map) != len(self.split_counts):
            raise ValueError("split_counts must not repeat a split")

        manifest_case_splits = {
            entry.case_id: entry.split
            for entry in self.entries
            if entry.artifact_kind is TraceArtifactKind.RUNTIME_INPUT
        }
        actual_counts = {
            split: sum(
                1
                for manifest_split in manifest_case_splits.values()
                if manifest_split is split
            )
            for split in TraceSplit
        }
        declared_counts = {split: split_count_map.get(split, 0) for split in TraceSplit}
        if actual_counts != declared_counts:
            raise ValueError("split_counts must match logical case splits in manifest entries")

        return self


class SyntheticTraceFixtureSet(StrictContract):
    """Loaded immutable fixture set for later deterministic trace replay."""

    manifest: SyntheticTraceFixtureManifest
    cases: tuple[SyntheticTraceReplayCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case_count_and_identity(self) -> SyntheticTraceFixtureSet:
        """Ensure all manifest cases were loaded exactly once."""

        case_ids = {case.runtime_input.case_id for case in self.cases}
        if len(case_ids) != len(self.cases):
            raise ValueError("loaded fixture cases must have unique case IDs")
        if len(case_ids) != self.manifest.case_count:
            raise ValueError("loaded fixture case count must match manifest case_count")
        return self
