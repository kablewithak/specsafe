"""Typed V4 final-evaluation fixture contracts and quarantined case loaders.

CRV4-201 through CRV4-236 are held-out final-evaluation assets. They remain physically
separate from calibration assets and must not be used by calibration fitting, policy tuning,
or runtime control. This module does not create a final manifest or run a held-out assessment.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import (
    CausalSchedulerContext,
    StrictContract,
    SyntheticTraceExpectedOutcome,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
)
from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4RegistryLoadError,
    CalibrationRedesignV4ScenarioFamilyRegistry,
    load_calibration_redesign_v4_scenario_family_registry,
)

_V4_FINAL_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(201, 237))
_V4_FINAL_FAMILY_IDS = frozenset(
    {
        "CRV4-FINAL-LIGHT-CAPACITY",
        "CRV4-FINAL-MODERATE-CAPACITY",
        "CRV4-FINAL-SATURATED-CAPACITY",
        "CRV4-FINAL-JAGGED-CAPACITY",
    }
)
_V4_EXPECTED_STATUS_BY_FAMILY = {
    "CRV4-FINAL-LIGHT-CAPACITY": "final_evaluation_fixtures_authored",
    "CRV4-FINAL-MODERATE-CAPACITY": "final_evaluation_fixtures_authored",
    "CRV4-FINAL-SATURATED-CAPACITY": "final_evaluation_fixtures_authored",
    "CRV4-FINAL-JAGGED-CAPACITY": "final_evaluation_fixtures_authored",
}


class CalibrationRedesignV4FinalCaseViolationCode(StrEnum):
    """Machine-readable reasons held-out V4 final fixtures cannot cross this boundary."""

    RUNTIME_SCHEMA_ERROR = "calibration_redesign_v4_final_runtime_schema_error"
    OUTCOME_SCHEMA_ERROR = "calibration_redesign_v4_final_outcome_schema_error"
    CASE_ALIGNMENT_ERROR = "calibration_redesign_v4_final_case_alignment_error"
    REGISTRY_MEMBERSHIP_ERROR = (
        "calibration_redesign_v4_final_registry_membership_error"
    )
    UNTRUSTED_REGISTRY = "calibration_redesign_v4_final_untrusted_registry"
    CASE_ASSET_LAYOUT_ERROR = "calibration_redesign_v4_final_case_asset_layout_error"
    CASE_ASSET_PROVENANCE_MISMATCH = (
        "calibration_redesign_v4_final_case_asset_provenance_mismatch"
    )


class CalibrationRedesignV4FinalCaseContractError(ValueError):
    """Raised when a held-out V4 final case is malformed or not quarantined correctly."""

    def __init__(
        self,
        code: CalibrationRedesignV4FinalCaseViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV4FinalRuntimeInput(StrictContract):
    """Scheduler-visible inputs for one quarantined V4 held-out replay case."""

    schema_version: Literal["calibration-redesign-v4-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CRV4-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CRV4-FINAL-LIGHT-CAPACITY",
        "CRV4-FINAL-MODERATE-CAPACITY",
        "CRV4-FINAL-SATURATED-CAPACITY",
        "CRV4-FINAL-JAGGED-CAPACITY",
    ]
    split: Literal[TraceSplit.FINAL_EVALUATION]
    data_role: Literal[TraceDataRole.HELD_OUT_EVALUATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    generation_note: str = Field(min_length=1, max_length=500)
    contexts: tuple[CausalSchedulerContext, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_runtime_contexts(self) -> CalibrationRedesignV4FinalRuntimeInput:
        """Require four decision-time positions in deterministic causal order."""

        expected_position = 1
        seen_keys: set[tuple[int, int]] = set()
        for context in self.contexts:
            if context.trace_id != self.trace_id:
                raise ValueError(
                    "all V4 final runtime contexts must use the enclosing trace_id"
                )
            if context.request_id != self.request_id:
                raise ValueError(
                    "all V4 final runtime contexts must use the enclosing request_id"
                )
            if context.decode_round != 0:
                raise ValueError("V4 final-evaluation cases must use decode round zero")
            key = (context.decode_round, context.block_position_index)
            if key in seen_keys:
                raise ValueError(
                    "V4 final runtime contexts must not repeat a position key"
                )
            if context.block_position_index != expected_position:
                raise ValueError(
                    "V4 final runtime contexts must have contiguous positions from one"
                )
            seen_keys.add(key)
            expected_position += 1
        return self


class CalibrationRedesignV4FinalExpectedOutcomes(StrictContract):
    """Evaluation-only V4 held-out outcomes kept separate from runtime inputs."""

    schema_version: Literal["calibration-redesign-v4-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CRV4-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CRV4-FINAL-LIGHT-CAPACITY",
        "CRV4-FINAL-MODERATE-CAPACITY",
        "CRV4-FINAL-SATURATED-CAPACITY",
        "CRV4-FINAL-JAGGED-CAPACITY",
    ]
    split: Literal[TraceSplit.FINAL_EVALUATION]
    data_role: Literal[TraceDataRole.HELD_OUT_EVALUATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...] = Field(
        min_length=4,
        max_length=4,
    )

    @model_validator(mode="after")
    def validate_outcomes(self) -> CalibrationRedesignV4FinalExpectedOutcomes:
        """Require four ordered, cumulative-prefix outcomes without exposing them at runtime."""

        expected_position = 1
        prefix_survives = True
        for outcome in self.outcomes:
            if outcome.trace_id != self.trace_id:
                raise ValueError(
                    "all V4 final outcomes must use the enclosing trace_id"
                )
            if outcome.decode_round != 0:
                raise ValueError(
                    "V4 final-evaluation outcomes must use decode round zero"
                )
            if outcome.block_position_index != expected_position:
                raise ValueError(
                    "V4 final outcomes must be contiguous from position one"
                )
            prefix_survives = prefix_survives and outcome.observed_acceptance
            if outcome.prefix_survival_label is not prefix_survives:
                raise ValueError(
                    "V4 final prefix_survival_label must equal cumulative acceptance"
                )
            expected_position += 1
        return self


class CalibrationRedesignV4FinalReplayCase(StrictContract):
    """A held-out replay case joined only after separate runtime and outcome assets load."""

    runtime_input: CalibrationRedesignV4FinalRuntimeInput
    expected_outcomes: CalibrationRedesignV4FinalExpectedOutcomes

    @model_validator(mode="after")
    def validate_runtime_outcome_alignment(
        self,
    ) -> CalibrationRedesignV4FinalReplayCase:
        """Join final evidence halves without treating outcomes as runtime state."""

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
                raise ValueError(
                    f"V4 final runtime and outcomes disagree on {field_name}"
                )

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
                "V4 final runtime and outcomes must have identical position keys"
            )
        _validate_visible_prefixes(contexts_by_key, outcomes.outcomes)
        return self


def validate_calibration_redesign_v4_final_replay_case_membership(
    replay_case: CalibrationRedesignV4FinalReplayCase,
    registry: CalibrationRedesignV4ScenarioFamilyRegistry,
) -> None:
    """Verify that a held-out case belongs to one authorised final-evaluation family."""

    if type(registry) is not CalibrationRedesignV4ScenarioFamilyRegistry:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.UNTRUSTED_REGISTRY,
            "V4 final case membership requires the exact V4 scenario-family registry",
        )

    runtime = replay_case.runtime_input
    if runtime.scenario_family_id not in _V4_FINAL_FAMILY_IDS:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V4 final runtime case references a family outside the held-out boundary",
        )
    family = next(
        (
            candidate
            for candidate in registry.families
            if candidate.scenario_family_id == runtime.scenario_family_id
        ),
        None,
    )
    expected_status = _V4_EXPECTED_STATUS_BY_FAMILY[runtime.scenario_family_id]
    if family is None or family.authoring_status != expected_status:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V4 final runtime case references a family outside current final authoring",
        )
    if runtime.case_id not in family.reserved_case_ids:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V4 final runtime case ID is not reserved by its scenario family",
        )


def load_calibration_redesign_v4_final_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationRedesignV4FinalReplayCase:
    """Load one quarantined CRV4-201 through CRV4-236 held-out case pair."""

    if case_id not in _V4_FINAL_CASE_IDS:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            "V4 final case loading requires a reserved CRV4-201 through CRV4-236 identifier",
        )
    resolved_root = root.resolve()
    try:
        registry = load_calibration_redesign_v4_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_final_evaluation_manifest_assets=True,
        )
    except CalibrationRedesignV4RegistryLoadError as error:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V4 final case asset root is not authorised for loading: {error}",
        ) from error

    final_root = resolved_root / "final_evaluation"
    runtime_payload = _read_json_asset(
        final_root / "inputs" / "cases" / f"{case_id}.json"
    )
    outcomes_payload = _read_json_asset(
        final_root / "expected_outcomes" / "cases" / f"{case_id}.json"
    )
    try:
        runtime_input = CalibrationRedesignV4FinalRuntimeInput.model_validate(
            runtime_payload
        )
    except ValidationError as error:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.RUNTIME_SCHEMA_ERROR,
            f"V4 final runtime case asset schema validation failed: {error}",
        ) from error
    try:
        expected_outcomes = CalibrationRedesignV4FinalExpectedOutcomes.model_validate(
            outcomes_payload
        )
    except ValidationError as error:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.OUTCOME_SCHEMA_ERROR,
            f"V4 final expected-outcome case asset schema validation failed: {error}",
        ) from error
    try:
        replay_case = CalibrationRedesignV4FinalReplayCase(
            runtime_input=runtime_input,
            expected_outcomes=expected_outcomes,
        )
    except ValidationError as error:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.CASE_ALIGNMENT_ERROR,
            f"V4 final runtime and expected-outcome assets do not align: {error}",
        ) from error

    validate_calibration_redesign_v4_final_replay_case_membership(replay_case, registry)
    return replay_case


def _read_json_asset(path: Path) -> Mapping[str, Any]:
    try:
        payload: Any = json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.CASE_ASSET_PROVENANCE_MISMATCH,
            f"unable to read V4 final case asset: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"invalid JSON in V4 final case asset {path.name}: {error.msg}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationRedesignV4FinalCaseContractError(
            CalibrationRedesignV4FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V4 final case asset must be a JSON object: {path.name}",
        )
    return payload


def _validate_visible_prefixes(
    contexts_by_key: dict[tuple[int, int], CausalSchedulerContext],
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...],
) -> None:
    expected_prefix: tuple[int, ...] = ()
    for outcome in outcomes:
        context = contexts_by_key[(outcome.decode_round, outcome.block_position_index)]
        if context.visible_prefix_token_ids != expected_prefix:
            raise ValueError(
                "V4 final visible prefix must match prior evaluation-only candidate token IDs"
            )
        expected_prefix = (*expected_prefix, outcome.candidate_token_id)
