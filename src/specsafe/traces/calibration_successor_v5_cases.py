"""Typed V5 calibration case contracts and staged loaders.

V5-3e authorises only CSV5-101 through CSV5-148. Runtime inputs and post-hoc
outcomes stay physically separate. This boundary does not fit calibration, freeze a
manifest, load final evidence, or execute a scheduler.
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
from specsafe.traces.calibration_successor_v5 import (
    CalibrationSuccessorV5RegistryLoadError,
    CalibrationSuccessorV5ScenarioFamilyRegistry,
    load_calibration_successor_v5_scenario_family_registry,
)

_V5_CURVE_COVERAGE_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(101, 113))
_V5_POSITION_SPREAD_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(113, 125))
_V5_WORKLOAD_VARIATION_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(125, 137))
_V5_MIXED_RELIABILITY_CONTRAST_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(137, 149))
_V5_CURVE_COVERAGE_FAMILY_ID = "CSV5-CAL-CURVE-COVERAGE"
_V5_POSITION_SPREAD_FAMILY_ID = "CSV5-CAL-POSITION-SPREAD"
_V5_WORKLOAD_VARIATION_FAMILY_ID = "CSV5-CAL-WORKLOAD-VARIATION"
_V5_MIXED_RELIABILITY_CONTRAST_FAMILY_ID = "CSV5-CAL-MIXED-RELIABILITY-CONTRAST"
_V5_CASE_IDS_BY_FAMILY = {
    _V5_CURVE_COVERAGE_FAMILY_ID: _V5_CURVE_COVERAGE_CASE_IDS,
    _V5_POSITION_SPREAD_FAMILY_ID: _V5_POSITION_SPREAD_CASE_IDS,
    _V5_WORKLOAD_VARIATION_FAMILY_ID: _V5_WORKLOAD_VARIATION_CASE_IDS,
    _V5_MIXED_RELIABILITY_CONTRAST_FAMILY_ID: _V5_MIXED_RELIABILITY_CONTRAST_CASE_IDS,
}
_V5_AUTHORED_STATUS_BY_FAMILY = {
    _V5_CURVE_COVERAGE_FAMILY_ID: "calibration_curve_coverage_authored",
    _V5_POSITION_SPREAD_FAMILY_ID: "calibration_position_spread_authored",
    _V5_WORKLOAD_VARIATION_FAMILY_ID: "calibration_workload_variation_authored",
    _V5_MIXED_RELIABILITY_CONTRAST_FAMILY_ID: ("calibration_mixed_reliability_contrast_authored"),
}


class CalibrationSuccessorV5CaseViolationCode(StrEnum):
    """Machine-readable reasons a V5-3c case cannot cross this boundary."""

    RUNTIME_SCHEMA_ERROR = "calibration_successor_v5_runtime_schema_error"
    OUTCOME_SCHEMA_ERROR = "calibration_successor_v5_outcome_schema_error"
    CASE_ALIGNMENT_ERROR = "calibration_successor_v5_case_alignment_error"
    REGISTRY_MEMBERSHIP_ERROR = "calibration_successor_v5_registry_membership_error"
    UNTRUSTED_REGISTRY = "calibration_successor_v5_untrusted_registry"
    CASE_ASSET_LAYOUT_ERROR = "calibration_successor_v5_case_asset_layout_error"
    CASE_ASSET_PROVENANCE_MISMATCH = "calibration_successor_v5_case_asset_provenance_mismatch"


class CalibrationSuccessorV5CaseContractError(ValueError):
    """Raised when one V5 calibration case pair is malformed or unauthorised."""

    def __init__(self, code: CalibrationSuccessorV5CaseViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CalibrationSuccessorV5RuntimeInput(StrictContract):
    """Scheduler-visible inputs for one V5 calibration-only case."""

    schema_version: Literal["calibration-successor-v5-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-successor-v5"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CSV5-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CSV5-CAL-CURVE-COVERAGE",
        "CSV5-CAL-POSITION-SPREAD",
        "CSV5-CAL-WORKLOAD-VARIATION",
        "CSV5-CAL-MIXED-RELIABILITY-CONTRAST",
    ]
    split: Literal[TraceSplit.CALIBRATION]
    data_role: Literal[TraceDataRole.CALIBRATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    generation_note: str = Field(min_length=1, max_length=500)
    contexts: tuple[CausalSchedulerContext, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_runtime_contexts(
        self,
    ) -> CalibrationSuccessorV5RuntimeInput:
        for expected_position, context in enumerate(self.contexts, start=1):
            if context.trace_id != self.trace_id:
                raise ValueError("all V5 runtime contexts must use the enclosing trace_id")
            if context.request_id != self.request_id:
                raise ValueError("all V5 runtime contexts must use the enclosing request_id")
            if context.decode_round != 0:
                raise ValueError("V5 calibration cases must use decode round zero")
            if context.block_position_index != expected_position:
                raise ValueError("V5 runtime contexts must be contiguous from position one")
        return self


class CalibrationSuccessorV5ExpectedOutcomes(StrictContract):
    """Evaluation-only V5 outcome labels, separated from runtime inputs."""

    schema_version: Literal["calibration-successor-v5-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-successor-v5"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CSV5-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CSV5-CAL-CURVE-COVERAGE",
        "CSV5-CAL-POSITION-SPREAD",
        "CSV5-CAL-WORKLOAD-VARIATION",
        "CSV5-CAL-MIXED-RELIABILITY-CONTRAST",
    ]
    split: Literal[TraceSplit.CALIBRATION]
    data_role: Literal[TraceDataRole.CALIBRATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_outcomes(
        self,
    ) -> CalibrationSuccessorV5ExpectedOutcomes:
        prefix_survives = True
        for expected_position, outcome in enumerate(self.outcomes, start=1):
            if outcome.trace_id != self.trace_id:
                raise ValueError("all V5 outcomes must use the enclosing trace_id")
            if outcome.decode_round != 0:
                raise ValueError("V5 calibration outcomes must use decode round zero")
            if outcome.block_position_index != expected_position:
                raise ValueError("V5 outcomes must be contiguous from position one")
            prefix_survives = prefix_survives and outcome.observed_acceptance
            if outcome.prefix_survival_label is not prefix_survives:
                raise ValueError("V5 prefix_survival_label must equal cumulative acceptance")
        return self


class CalibrationSuccessorV5ReplayCase(StrictContract):
    """One V5 replay case, composed only after separate evidence halves are loaded."""

    runtime_input: CalibrationSuccessorV5RuntimeInput
    expected_outcomes: CalibrationSuccessorV5ExpectedOutcomes

    @model_validator(mode="after")
    def validate_alignment(self) -> CalibrationSuccessorV5ReplayCase:
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
                raise ValueError(f"V5 runtime and outcomes disagree on {field_name}")
        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in runtime.contexts
        }
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in outcomes.outcomes
        }
        if set(contexts_by_key) != set(outcomes_by_key):
            raise ValueError("V5 runtime and outcomes must have identical position keys")
        expected_prefix: tuple[int, ...] = ()
        for outcome in outcomes.outcomes:
            context = contexts_by_key[(outcome.decode_round, outcome.block_position_index)]
            if context.visible_prefix_token_ids != expected_prefix:
                raise ValueError(
                    "V5 visible prefix must match prior evaluation-only candidate token IDs"
                )
            expected_prefix = (*expected_prefix, outcome.candidate_token_id)
        return self


def validate_calibration_successor_v5_replay_case_membership(
    replay_case: CalibrationSuccessorV5ReplayCase,
    registry: CalibrationSuccessorV5ScenarioFamilyRegistry,
) -> None:
    """Verify one case belongs to an authorised V5-3e calibration family."""

    if type(registry) is not CalibrationSuccessorV5ScenarioFamilyRegistry:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.UNTRUSTED_REGISTRY,
            "V5 case membership requires the exact V5 scenario-family registry",
        )
    runtime = replay_case.runtime_input
    allowed_case_ids = _V5_CASE_IDS_BY_FAMILY.get(runtime.scenario_family_id)
    expected_status = _V5_AUTHORED_STATUS_BY_FAMILY.get(runtime.scenario_family_id)
    if allowed_case_ids is None or expected_status is None:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V5-3e loads only authorised V5 calibration families",
        )
    family = next(
        item for item in registry.families if item.scenario_family_id == runtime.scenario_family_id
    )
    if family.authoring_status != expected_status:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V5 case family is not authorised for loading at the current stage",
        )
    if runtime.case_id not in allowed_case_ids:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V5 case ID is outside its active family reservation",
        )


def load_calibration_successor_v5_curve_coverage_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5ReplayCase:
    """Load one retained curve-coverage case through the V5-3c root."""

    if case_id not in _V5_CURVE_COVERAGE_CASE_IDS:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            "curve-coverage loading requires a CSV5-101 through CSV5-112 identifier",
        )
    return _load_calibration_successor_v5_replay_case(root, case_id)


def load_calibration_successor_v5_position_spread_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5ReplayCase:
    """Load one V5-3c position-spread calibration case pair."""

    if case_id not in _V5_POSITION_SPREAD_CASE_IDS:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            "position-spread loading requires a CSV5-113 through CSV5-124 identifier",
        )
    return _load_calibration_successor_v5_replay_case(root, case_id)


def load_calibration_successor_v5_workload_variation_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5ReplayCase:
    """Load one V5-3d workload-variation calibration case pair."""

    if case_id not in _V5_WORKLOAD_VARIATION_CASE_IDS:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            "workload-variation loading requires a CSV5-125 through CSV5-136 identifier",
        )
    return _load_calibration_successor_v5_replay_case(root, case_id)


def load_calibration_successor_v5_mixed_reliability_contrast_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5ReplayCase:
    """Load one V5-3e mixed-reliability contrast calibration case pair."""

    if case_id not in _V5_MIXED_RELIABILITY_CONTRAST_CASE_IDS:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            "mixed-reliability loading requires a CSV5-137 through CSV5-148 identifier",
        )
    return _load_calibration_successor_v5_replay_case(root, case_id)


def _load_calibration_successor_v5_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5ReplayCase:
    resolved_root = root.resolve()
    try:
        registry = load_calibration_successor_v5_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_calibration_mixed_reliability_contrast_assets=True,
        )
    except CalibrationSuccessorV5RegistryLoadError as error:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V5 case asset root is not authorised for loading: {error}",
        ) from error
    runtime_payload = _read_json_asset(resolved_root / "inputs" / "cases" / f"{case_id}.json")
    outcomes_payload = _read_json_asset(
        resolved_root / "expected_outcomes" / "cases" / f"{case_id}.json"
    )
    try:
        runtime_input = CalibrationSuccessorV5RuntimeInput.model_validate(runtime_payload)
    except ValidationError as error:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.RUNTIME_SCHEMA_ERROR,
            f"V5 runtime case asset schema validation failed: {error}",
        ) from error
    try:
        expected_outcomes = CalibrationSuccessorV5ExpectedOutcomes.model_validate(outcomes_payload)
    except ValidationError as error:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.OUTCOME_SCHEMA_ERROR,
            f"V5 expected-outcome case asset schema validation failed: {error}",
        ) from error
    try:
        replay_case = CalibrationSuccessorV5ReplayCase(
            runtime_input=runtime_input,
            expected_outcomes=expected_outcomes,
        )
    except ValidationError as error:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ALIGNMENT_ERROR,
            f"V5 runtime and expected-outcome case assets do not align: {error}",
        ) from error
    validate_calibration_successor_v5_replay_case_membership(replay_case, registry)
    return replay_case


def _read_json_asset(path: Path) -> Mapping[str, Any]:
    try:
        payload: Any = json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_PROVENANCE_MISMATCH,
            f"unable to read V5 case asset: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"invalid JSON in V5 case asset {path.name}: {error.msg}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationSuccessorV5CaseContractError(
            CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V5 case asset must be a JSON object: {path.name}",
        )
    return payload
