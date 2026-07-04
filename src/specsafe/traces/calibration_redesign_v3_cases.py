"""Typed V3 calibration case contracts and loaders.

Only CRV3-101 through CRV3-136 may be loaded at this stage. Runtime inputs and
post-hoc outcomes remain separate, final-evaluation and adversarial data remain absent,
and no calibration fitting or scheduler behaviour is introduced here.
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
from specsafe.traces.calibration_redesign_v3 import (
    CalibrationRedesignV3RegistryLoadError,
    CalibrationRedesignV3ScenarioFamilyRegistry,
    load_calibration_redesign_v3_scenario_family_registry,
)


class CalibrationRedesignV3CaseViolationCode(StrEnum):
    """Machine-readable reasons a V3 curve-coverage case contract is invalid."""

    RUNTIME_SCHEMA_ERROR = "calibration_redesign_v3_runtime_schema_error"
    OUTCOME_SCHEMA_ERROR = "calibration_redesign_v3_outcome_schema_error"
    CASE_ALIGNMENT_ERROR = "calibration_redesign_v3_case_alignment_error"
    REGISTRY_MEMBERSHIP_ERROR = "calibration_redesign_v3_registry_membership_error"
    UNTRUSTED_REGISTRY = "calibration_redesign_v3_untrusted_registry"
    CASE_ASSET_LAYOUT_ERROR = "calibration_redesign_v3_case_asset_layout_error"
    CASE_ASSET_PROVENANCE_MISMATCH = "calibration_redesign_v3_case_asset_provenance_mismatch"


class CalibrationRedesignV3CaseContractError(ValueError):
    """Typed error raised when a V3 case cannot cross its current boundary."""

    def __init__(self, code: CalibrationRedesignV3CaseViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV3RuntimeInput(StrictContract):
    """Scheduler-visible V3 raw-confidence inputs for one calibration replay case."""

    schema_version: Literal["calibration-redesign-v3-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CRV3-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CRV3-CAL-CURVE-COVERAGE",
        "CRV3-CAL-POSITION-SPREAD",
        "CRV3-CAL-WORKLOAD-MIX",
    ]
    split: Literal[TraceSplit.CALIBRATION]
    data_role: Literal[TraceDataRole.CALIBRATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    generation_note: str = Field(min_length=1, max_length=500)
    contexts: tuple[CausalSchedulerContext, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_runtime_contexts(self) -> CalibrationRedesignV3RuntimeInput:
        """Preserve deterministic order while keeping labels absent from runtime inputs."""

        prior_key: tuple[int, int] | None = None
        seen_keys: set[tuple[int, int]] = set()
        for context in self.contexts:
            if context.trace_id != self.trace_id:
                raise ValueError("all V3 runtime contexts must use the enclosing trace_id")
            if context.request_id != self.request_id:
                raise ValueError("all V3 runtime contexts must use the enclosing request_id")
            key = (context.decode_round, context.block_position_index)
            if key in seen_keys:
                raise ValueError("V3 runtime contexts must not repeat a position key")
            if prior_key is not None and key < prior_key:
                raise ValueError("V3 runtime contexts must be ordered by round and position")
            seen_keys.add(key)
            prior_key = key
        return self


class CalibrationRedesignV3ExpectedOutcomes(StrictContract):
    """Post-hoc V3 labels structurally separated from runtime inputs."""

    schema_version: Literal["calibration-redesign-v3-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CRV3-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CRV3-CAL-CURVE-COVERAGE",
        "CRV3-CAL-POSITION-SPREAD",
        "CRV3-CAL-WORKLOAD-MIX",
    ]
    split: Literal[TraceSplit.CALIBRATION]
    data_role: Literal[TraceDataRole.CALIBRATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_outcomes(self) -> CalibrationRedesignV3ExpectedOutcomes:
        """Require ordered outcomes and cumulative prefix-survival labels."""

        expected_position = 1
        prefix_survives = True
        for outcome in self.outcomes:
            if outcome.trace_id != self.trace_id:
                raise ValueError("all V3 outcomes must use the enclosing trace_id")
            if outcome.decode_round != 0:
                raise ValueError("V3 calibration cases must use decode round zero")
            if outcome.block_position_index != expected_position:
                raise ValueError("V3 outcomes must be contiguous from position one")
            prefix_survives = prefix_survives and outcome.observed_acceptance
            if outcome.prefix_survival_label is not prefix_survives:
                raise ValueError("V3 prefix_survival_label must equal cumulative acceptance")
            expected_position += 1
        return self


class CalibrationRedesignV3ReplayCase(StrictContract):
    """Typed V3 pairing after separate runtime and outcome assets are loaded."""

    runtime_input: CalibrationRedesignV3RuntimeInput
    expected_outcomes: CalibrationRedesignV3ExpectedOutcomes

    @model_validator(mode="after")
    def validate_runtime_outcome_alignment(self) -> CalibrationRedesignV3ReplayCase:
        """Align both evidence halves without exposing outcomes to runtime policy code."""

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
                raise ValueError(f"V3 runtime and outcomes disagree on {field_name}")
        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in runtime.contexts
        }
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in outcomes.outcomes
        }
        if set(contexts_by_key) != set(outcomes_by_key):
            raise ValueError("V3 runtime and outcomes must have identical position keys")
        _validate_visible_prefixes(contexts_by_key, outcomes.outcomes)
        return self


def validate_calibration_redesign_v3_replay_case_membership(
    replay_case: CalibrationRedesignV3ReplayCase,
    registry: CalibrationRedesignV3ScenarioFamilyRegistry,
) -> None:
    """Verify the case belongs to an authorised V3 calibration family."""

    if not isinstance(registry, CalibrationRedesignV3ScenarioFamilyRegistry):
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.UNTRUSTED_REGISTRY,
            "V3 case membership requires a trusted V3 scenario-family registry",
        )
    runtime = replay_case.runtime_input
    family = next(
        (
            item
            for item in registry.families
            if item.scenario_family_id == runtime.scenario_family_id
        ),
        None,
    )
    authorised_statuses = {
        "calibration_curve_coverage_authored",
        "calibration_position_spread_authored",
        "calibration_workload_mix_authored",
    }
    if (
        family is None
        or family.split is not TraceSplit.CALIBRATION
        or family.authoring_status not in authorised_statuses
    ):
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V3 runtime case references a family not authorised for current case loading",
        )
    if runtime.case_id not in family.reserved_case_ids:
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V3 runtime case ID is not reserved by its authorised scenario family",
        )


def load_calibration_redesign_v3_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationRedesignV3ReplayCase:
    """Load one authorised V3 calibration case pair."""

    if not _is_v3_case_id(case_id):
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            "V3 case asset loading requires a CRV3-### case identifier",
        )
    resolved_root = root.resolve()
    try:
        registry = load_calibration_redesign_v3_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_calibration_workload_mix_assets=True,
        )
    except CalibrationRedesignV3RegistryLoadError as error:
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V3 case asset root is not authorised for loading: {error}",
        ) from error

    runtime_payload = _read_json_asset(resolved_root / "inputs" / "cases" / f"{case_id}.json")
    outcomes_payload = _read_json_asset(
        resolved_root / "expected_outcomes" / "cases" / f"{case_id}.json"
    )
    try:
        runtime_input = CalibrationRedesignV3RuntimeInput.model_validate(runtime_payload)
    except ValidationError as error:
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.RUNTIME_SCHEMA_ERROR,
            f"V3 runtime case asset schema validation failed: {error}",
        ) from error
    try:
        expected_outcomes = CalibrationRedesignV3ExpectedOutcomes.model_validate(outcomes_payload)
    except ValidationError as error:
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.OUTCOME_SCHEMA_ERROR,
            f"V3 expected-outcome case asset schema validation failed: {error}",
        ) from error
    try:
        replay_case = CalibrationRedesignV3ReplayCase(
            runtime_input=runtime_input,
            expected_outcomes=expected_outcomes,
        )
    except ValidationError as error:
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.CASE_ALIGNMENT_ERROR,
            f"V3 runtime and expected-outcome case assets do not align: {error}",
        ) from error

    validate_calibration_redesign_v3_replay_case_membership(replay_case, registry)
    return replay_case


def _read_json_asset(path: Path) -> Mapping[str, Any]:
    """Read one local V3 case asset with explicit provenance failures."""

    try:
        payload: Any = json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.CASE_ASSET_PROVENANCE_MISMATCH,
            f"unable to read V3 case asset: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"invalid JSON in V3 case asset {path.name}: {error.msg}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationRedesignV3CaseContractError(
            CalibrationRedesignV3CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V3 case asset must be a JSON object: {path.name}",
        )
    return payload


def _is_v3_case_id(case_id: str) -> bool:
    return (
        case_id.startswith("CRV3-")
        and len(case_id) == 8
        and case_id.removeprefix("CRV3-").isdigit()
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
                "V3 visible prefix must match prior evaluation-only candidate token IDs"
            )
        expected_prefix = (*expected_prefix, outcome.candidate_token_id)
