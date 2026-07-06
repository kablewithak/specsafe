"""Typed V4 calibration case contracts and loaders.

CRV4-101 through CRV4-148 are the only authorised calibration-only case pairs. A
calibration manifest and calibration-only fit diagnostics are retained, while quarantined
final-evaluation assets now exist in a separate tree. Runtime inputs and post-hoc outcomes
remain physically separate. This module does not fit calibration or execute a scheduler.
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

_V4_AUTHORISED_CALIBRATION_FAMILY_IDS = frozenset(
    {
        "CRV4-CAL-CURVE-COVERAGE",
        "CRV4-CAL-POSITION-SPREAD",
        "CRV4-CAL-WORKLOAD-MIX",
        "CRV4-CAL-CAPACITY-CONTRAST",
    }
)
_V4_EXPECTED_STATUS_BY_FAMILY = {
    "CRV4-CAL-CURVE-COVERAGE": "calibration_curve_coverage_authored",
    "CRV4-CAL-POSITION-SPREAD": "calibration_position_spread_authored",
    "CRV4-CAL-WORKLOAD-MIX": "calibration_workload_mix_authored",
    "CRV4-CAL-CAPACITY-CONTRAST": "calibration_capacity_contrast_authored",
}


class CalibrationRedesignV4CaseViolationCode(StrEnum):
    """Machine-readable reasons a V4 calibration case cannot cross this boundary."""

    RUNTIME_SCHEMA_ERROR = "calibration_redesign_v4_runtime_schema_error"
    OUTCOME_SCHEMA_ERROR = "calibration_redesign_v4_outcome_schema_error"
    CASE_ALIGNMENT_ERROR = "calibration_redesign_v4_case_alignment_error"
    REGISTRY_MEMBERSHIP_ERROR = "calibration_redesign_v4_registry_membership_error"
    UNTRUSTED_REGISTRY = "calibration_redesign_v4_untrusted_registry"
    CASE_ASSET_LAYOUT_ERROR = "calibration_redesign_v4_case_asset_layout_error"
    CASE_ASSET_PROVENANCE_MISMATCH = (
        "calibration_redesign_v4_case_asset_provenance_mismatch"
    )


class CalibrationRedesignV4CaseContractError(ValueError):
    """Raised when one V4 case pair is malformed or outside the active boundary."""

    def __init__(
        self,
        code: CalibrationRedesignV4CaseViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV4RuntimeInput(StrictContract):
    """Scheduler-visible inputs for one V4 calibration-only replay case."""

    schema_version: Literal["calibration-redesign-v4-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CRV4-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CRV4-CAL-CURVE-COVERAGE",
        "CRV4-CAL-POSITION-SPREAD",
        "CRV4-CAL-WORKLOAD-MIX",
        "CRV4-CAL-CAPACITY-CONTRAST",
    ]
    split: Literal[TraceSplit.CALIBRATION]
    data_role: Literal[TraceDataRole.CALIBRATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    generation_note: str = Field(min_length=1, max_length=500)
    contexts: tuple[CausalSchedulerContext, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_runtime_contexts(self) -> CalibrationRedesignV4RuntimeInput:
        """Require four decision-time positions in deterministic causal order."""

        expected_position = 1
        seen_keys: set[tuple[int, int]] = set()
        for context in self.contexts:
            if context.trace_id != self.trace_id:
                raise ValueError(
                    "all V4 runtime contexts must use the enclosing trace_id"
                )
            if context.request_id != self.request_id:
                raise ValueError(
                    "all V4 runtime contexts must use the enclosing request_id"
                )
            if context.decode_round != 0:
                raise ValueError("V4 calibration cases must use decode round zero")
            key = (context.decode_round, context.block_position_index)
            if key in seen_keys:
                raise ValueError("V4 runtime contexts must not repeat a position key")
            if context.block_position_index != expected_position:
                raise ValueError(
                    "V4 runtime contexts must have contiguous positions from one"
                )
            seen_keys.add(key)
            expected_position += 1
        return self


class CalibrationRedesignV4ExpectedOutcomes(StrictContract):
    """Evaluation-only V4 outcomes kept separate from the runtime-input asset."""

    schema_version: Literal["calibration-redesign-v4-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CRV4-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CRV4-CAL-CURVE-COVERAGE",
        "CRV4-CAL-POSITION-SPREAD",
        "CRV4-CAL-WORKLOAD-MIX",
        "CRV4-CAL-CAPACITY-CONTRAST",
    ]
    split: Literal[TraceSplit.CALIBRATION]
    data_role: Literal[TraceDataRole.CALIBRATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...] = Field(
        min_length=4,
        max_length=4,
    )

    @model_validator(mode="after")
    def validate_outcomes(self) -> CalibrationRedesignV4ExpectedOutcomes:
        """Require four ordered, cumulative-prefix outcome labels."""

        expected_position = 1
        prefix_survives = True
        for outcome in self.outcomes:
            if outcome.trace_id != self.trace_id:
                raise ValueError("all V4 outcomes must use the enclosing trace_id")
            if outcome.decode_round != 0:
                raise ValueError("V4 calibration outcomes must use decode round zero")
            if outcome.block_position_index != expected_position:
                raise ValueError("V4 outcomes must be contiguous from position one")
            prefix_survives = prefix_survives and outcome.observed_acceptance
            if outcome.prefix_survival_label is not prefix_survives:
                raise ValueError(
                    "V4 prefix_survival_label must equal cumulative acceptance"
                )
            expected_position += 1
        return self


class CalibrationRedesignV4ReplayCase(StrictContract):
    """A paired V4 replay case formed only after both evidence halves are loaded."""

    runtime_input: CalibrationRedesignV4RuntimeInput
    expected_outcomes: CalibrationRedesignV4ExpectedOutcomes

    @model_validator(mode="after")
    def validate_runtime_outcome_alignment(self) -> CalibrationRedesignV4ReplayCase:
        """Join matching assets without making outcomes part of runtime state."""

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
                raise ValueError(f"V4 runtime and outcomes disagree on {field_name}")

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
                "V4 runtime and outcomes must have identical position keys"
            )
        _validate_visible_prefixes(contexts_by_key, outcomes.outcomes)
        return self


def validate_calibration_redesign_v4_replay_case_membership(
    replay_case: CalibrationRedesignV4ReplayCase,
    registry: CalibrationRedesignV4ScenarioFamilyRegistry,
) -> None:
    """Verify the pair belongs to an authorised V4 calibration-only family."""

    if type(registry) is not CalibrationRedesignV4ScenarioFamilyRegistry:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.UNTRUSTED_REGISTRY,
            "V4 case membership requires the exact V4 scenario-family registry",
        )

    runtime = replay_case.runtime_input
    if runtime.scenario_family_id not in _V4_AUTHORISED_CALIBRATION_FAMILY_IDS:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V4 runtime case references a family outside the calibration-only boundary",
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
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V4 runtime case references a family not authorised for current case loading",
        )
    if runtime.case_id not in family.reserved_case_ids:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V4 runtime case ID is not reserved by its authorised scenario family",
        )


def load_calibration_redesign_v4_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationRedesignV4ReplayCase:
    """Load one final-authoring-stage calibration case pair without touching final outcomes."""

    if not _is_v4_case_id(case_id):
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            "V4 case asset loading requires a CRV4-### case identifier",
        )
    resolved_root = root.resolve()
    try:
        registry = load_calibration_redesign_v4_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_final_evaluation_fixture_assets=True,
        )
    except CalibrationRedesignV4RegistryLoadError as error:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V4 case asset root is not authorised for loading: {error}",
        ) from error

    runtime_payload = _read_json_asset(
        resolved_root / "inputs" / "cases" / f"{case_id}.json"
    )
    outcomes_payload = _read_json_asset(
        resolved_root / "expected_outcomes" / "cases" / f"{case_id}.json"
    )
    try:
        runtime_input = CalibrationRedesignV4RuntimeInput.model_validate(
            runtime_payload
        )
    except ValidationError as error:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.RUNTIME_SCHEMA_ERROR,
            f"V4 runtime case asset schema validation failed: {error}",
        ) from error
    try:
        expected_outcomes = CalibrationRedesignV4ExpectedOutcomes.model_validate(
            outcomes_payload
        )
    except ValidationError as error:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.OUTCOME_SCHEMA_ERROR,
            f"V4 expected-outcome case asset schema validation failed: {error}",
        ) from error
    try:
        replay_case = CalibrationRedesignV4ReplayCase(
            runtime_input=runtime_input,
            expected_outcomes=expected_outcomes,
        )
    except ValidationError as error:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.CASE_ALIGNMENT_ERROR,
            f"V4 runtime and expected-outcome case assets do not align: {error}",
        ) from error

    validate_calibration_redesign_v4_replay_case_membership(replay_case, registry)
    return replay_case


def _read_json_asset(path: Path) -> Mapping[str, Any]:
    """Read one V4 JSON object with typed boundary errors."""

    try:
        payload: Any = json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.CASE_ASSET_PROVENANCE_MISMATCH,
            f"unable to read V4 case asset: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"invalid JSON in V4 case asset {path.name}: {error.msg}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationRedesignV4CaseContractError(
            CalibrationRedesignV4CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V4 case asset must be a JSON object: {path.name}",
        )
    return payload


def _is_v4_case_id(case_id: str) -> bool:
    return (
        case_id.startswith("CRV4-")
        and len(case_id) == 8
        and case_id.removeprefix("CRV4-").isdigit()
    )


def _validate_visible_prefixes(
    contexts_by_key: dict[tuple[int, int], CausalSchedulerContext],
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...],
) -> None:
    expected_prefix: tuple[int, ...] = ()
    for outcome in outcomes:
        context = contexts_by_key[(outcome.decode_round, outcome.block_position_index)]
        if context.visible_prefix_token_ids != expected_prefix:
            raise ValueError(
                "V4 visible prefix must match prior evaluation-only candidate token IDs"
            )
        expected_prefix = (*expected_prefix, outcome.candidate_token_id)
