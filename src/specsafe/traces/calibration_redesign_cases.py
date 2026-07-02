"""Strict case contracts for fresh calibration-redesign fixture assets.

These contracts keep scenario-family provenance attached to a fresh fixture case without
weakening the older synthetic trace fixture contract. Runtime inputs remain structurally
separate from post-hoc expected outcomes.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts import (
    CausalSchedulerContext,
    SyntheticTraceExpectedOutcome,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
)
from specsafe.contracts.models import StrictContract
from specsafe.traces.calibration_redesign import ScenarioFamilyRegistry


class CalibrationRedesignCaseViolationCode(StrEnum):
    """Machine-readable reasons fresh calibration case assets cannot be trusted."""

    CASE_SCHEMA_ERROR = "calibration_redesign_case_schema_error"
    CASE_PROVENANCE_MISMATCH = "calibration_redesign_case_provenance_mismatch"
    REGISTRY_CASE_MISMATCH = "calibration_redesign_registry_case_mismatch"


class CalibrationRedesignCaseLoadError(ValueError):
    """Typed error raised when a fresh runtime/outcome pair violates its boundary."""

    def __init__(self, code: CalibrationRedesignCaseViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.DEVELOPMENT: TraceDataRole.SYNTHETIC_FIXTURE,
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}


class CalibrationRedesignRuntimeInput(StrictContract):
    """Scheduler-visible input for one governed calibration-redesign case."""

    schema_version: str = Field(min_length=1, max_length=64)
    fixture_set_id: Literal["synthetic-calibration-redesign-v1"]
    fixture_set_version: str = Field(min_length=1, max_length=64)
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    data_role: TraceDataRole
    source_type: TraceSourceType
    generation_note: str = Field(min_length=1, max_length=500)
    contexts: tuple[CausalSchedulerContext, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_runtime_provenance_and_contexts(self) -> CalibrationRedesignRuntimeInput:
        """Bind fresh runtime assets to lawful context and governed split metadata."""

        if self.source_type is not TraceSourceType.SYNTHETIC:
            raise ValueError("calibration-redesign runtime input source_type must be synthetic")
        if self.data_role is not _EXPECTED_DATA_ROLE_BY_SPLIT[self.split]:
            raise ValueError("runtime data_role must match the governed data role for its split")

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
                    "runtime contexts must be ordered by decode_round and block_position_index"
                )
            seen_keys.add(key)
            prior_key = key
        return self


class CalibrationRedesignExpectedOutcomes(StrictContract):
    """Evaluation-only outcome labels for one governed calibration-redesign case."""

    schema_version: str = Field(min_length=1, max_length=64)
    fixture_set_id: Literal["synthetic-calibration-redesign-v1"]
    fixture_set_version: str = Field(min_length=1, max_length=64)
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    data_role: TraceDataRole
    source_type: TraceSourceType
    provenance_note: str = Field(min_length=1, max_length=500)
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_outcome_provenance_and_labels(self) -> CalibrationRedesignExpectedOutcomes:
        """Keep outcome assets post-hoc, complete, ordered, and split-governed."""

        if self.source_type is not TraceSourceType.SYNTHETIC:
            raise ValueError("calibration-redesign expected outcomes source_type must be synthetic")
        if self.data_role is not _EXPECTED_DATA_ROLE_BY_SPLIT[self.split]:
            raise ValueError("outcome data_role must match the governed data role for its split")

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
                        "expected outcomes must have contiguous positions beginning at one per "
                        "decode round"
                    )
                prefix_survives = prefix_survives and outcome.observed_acceptance
                if outcome.prefix_survival_label is not prefix_survives:
                    raise ValueError(
                        "prefix_survival_label must equal cumulative observed acceptance within "
                        "its round"
                    )
                expected_position += 1
        return self


class CalibrationRedesignReplayCase(StrictContract):
    """Validated fresh case composed only after runtime and outcome assets are parsed."""

    runtime_input: CalibrationRedesignRuntimeInput
    expected_outcomes: CalibrationRedesignExpectedOutcomes

    @model_validator(mode="after")
    def validate_runtime_outcome_alignment(self) -> CalibrationRedesignReplayCase:
        """Prove post-hoc labels line up without entering runtime policy input."""

        runtime = self.runtime_input
        outcomes = self.expected_outcomes
        aligned_fields = (
            "schema_version",
            "fixture_set_id",
            "fixture_set_version",
            "fixture_id",
            "case_id",
            "trace_id",
            "scenario_family_id",
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
                "runtime contexts and expected outcomes must have identical position keys"
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


def load_calibration_redesign_replay_case(
    runtime_input_path: Path,
    expected_outcomes_path: Path,
    registry: ScenarioFamilyRegistry,
) -> CalibrationRedesignReplayCase:
    """Load one fresh case and verify its registry assignment before later manifest use."""

    runtime_payload = _read_json_asset(runtime_input_path)
    outcomes_payload = _read_json_asset(expected_outcomes_path)
    try:
        runtime_input = CalibrationRedesignRuntimeInput.model_validate(runtime_payload)
        expected_outcomes = CalibrationRedesignExpectedOutcomes.model_validate(outcomes_payload)
    except ValidationError as error:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.CASE_SCHEMA_ERROR,
            f"calibration-redesign case schema validation failed: {error}",
        ) from error

    try:
        replay_case = CalibrationRedesignReplayCase(
            runtime_input=runtime_input,
            expected_outcomes=expected_outcomes,
        )
    except ValidationError as error:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.CASE_PROVENANCE_MISMATCH,
            f"calibration-redesign runtime/outcome alignment failed: {error}",
        ) from error

    _validate_case_against_registry(replay_case, registry)
    return replay_case


def _read_json_asset(path: Path) -> Mapping[str, Any]:
    """Read one local JSON case asset without an unsafe fallback path."""

    try:
        payload: Any = json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.CASE_PROVENANCE_MISMATCH,
            f"unable to read calibration-redesign case asset: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.CASE_SCHEMA_ERROR,
            f"invalid JSON in calibration-redesign case asset: {path.name}: {error.msg}",
        ) from error

    if not isinstance(payload, dict):
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.CASE_SCHEMA_ERROR,
            f"calibration-redesign case asset must be a JSON object: {path.name}",
        )
    return payload


def _validate_case_against_registry(
    replay_case: CalibrationRedesignReplayCase,
    registry: ScenarioFamilyRegistry,
) -> None:
    """Ensure an authored case belongs to exactly one predeclared fresh family."""

    runtime = replay_case.runtime_input
    family_by_id = {
        family.scenario_family_id: family
        for family in registry.families
    }
    family = family_by_id.get(runtime.scenario_family_id)
    if family is None:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.REGISTRY_CASE_MISMATCH,
            f"scenario family is not declared in the registry: {runtime.scenario_family_id}",
        )
    if runtime.case_id not in family.case_ids:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.REGISTRY_CASE_MISMATCH,
            f"case ID is not declared by its scenario family: {runtime.case_id}",
        )
    if runtime.split is not family.split or runtime.data_role is not family.primary_data_role:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.REGISTRY_CASE_MISMATCH,
            "case split or data role does not match its scenario-family registry record",
        )
    if runtime.fixture_set_id != registry.fixture_set_id:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.REGISTRY_CASE_MISMATCH,
            "case fixture_set_id does not match its scenario-family registry",
        )
    if runtime.fixture_set_version != registry.fixture_set_version:
        raise CalibrationRedesignCaseLoadError(
            CalibrationRedesignCaseViolationCode.REGISTRY_CASE_MISMATCH,
            "case fixture_set_version does not match its scenario-family registry",
        )
