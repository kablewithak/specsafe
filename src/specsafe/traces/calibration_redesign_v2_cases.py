"""Typed V2 case contracts and governed local case-pair loading.

The loader may read only separately stored runtime and expected-outcome assets from the V2
case-authoring layout. It validates the finalized registry, typed assets, causal replay
alignment, and registry membership without building manifests, fitting calibration, or
assessing held-out evidence.
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
from specsafe.traces.calibration_redesign_v2 import (
    CalibrationRedesignV2RegistryLoadError,
    CalibrationRedesignV2ScenarioFamilyRegistry,
    load_calibration_redesign_v2_scenario_family_registry,
)


class CalibrationRedesignV2CaseViolationCode(StrEnum):
    """Machine-readable reasons a V2 in-memory case contract is invalid."""

    RUNTIME_SCHEMA_ERROR = "calibration_redesign_v2_runtime_schema_error"
    OUTCOME_SCHEMA_ERROR = "calibration_redesign_v2_outcome_schema_error"
    CASE_ALIGNMENT_ERROR = "calibration_redesign_v2_case_alignment_error"
    REGISTRY_MEMBERSHIP_ERROR = "calibration_redesign_v2_registry_membership_error"
    UNTRUSTED_REGISTRY = "calibration_redesign_v2_untrusted_registry"
    CASE_ASSET_LAYOUT_ERROR = "calibration_redesign_v2_case_asset_layout_error"
    CASE_ASSET_PROVENANCE_MISMATCH = (
        "calibration_redesign_v2_case_asset_provenance_mismatch"
    )


class CalibrationRedesignV2CaseContractError(ValueError):
    """Typed error raised when a V2 in-memory case cannot cross a contract boundary."""

    def __init__(self, code: CalibrationRedesignV2CaseViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV2RuntimeInput(StrictContract):
    """Scheduler-visible V2 input, intentionally excluding post-hoc outcome fields."""

    schema_version: Literal["calibration-redesign-v2-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v2"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CRV2-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: str = Field(pattern=r"^CRV2-[A-Z0-9-]+$")
    split: TraceSplit
    data_role: TraceDataRole
    source_type: Literal[TraceSourceType.SYNTHETIC]
    generation_note: str = Field(min_length=1, max_length=500)
    contexts: tuple[CausalSchedulerContext, ...] = Field(min_length=4)

    @model_validator(mode="after")
    def validate_runtime_contexts(self) -> CalibrationRedesignV2RuntimeInput:
        """Preserve deterministic, causal order without exposing labels at runtime."""

        expected_role = _expected_role(self.split)
        if self.data_role is not expected_role:
            raise ValueError("V2 runtime data_role must match its governed split")
        prior_key: tuple[int, int] | None = None
        seen_keys: set[tuple[int, int]] = set()
        for context in self.contexts:
            if context.trace_id != self.trace_id:
                raise ValueError("all V2 runtime contexts must use the enclosing trace_id")
            if context.request_id != self.request_id:
                raise ValueError("all V2 runtime contexts must use the enclosing request_id")
            key = (context.decode_round, context.block_position_index)
            if key in seen_keys:
                raise ValueError("V2 runtime contexts must not repeat a position key")
            if prior_key is not None and key < prior_key:
                raise ValueError("V2 runtime contexts must be ordered by round and position")
            seen_keys.add(key)
            prior_key = key
        return self


class CalibrationRedesignV2ExpectedOutcomes(StrictContract):
    """Post-hoc V2 labels that remain structurally separate from runtime inputs."""

    schema_version: Literal["calibration-redesign-v2-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v2"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CRV2-[0-9]{3}$")
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: str = Field(pattern=r"^CRV2-[A-Z0-9-]+$")
    split: TraceSplit
    data_role: TraceDataRole
    source_type: Literal[TraceSourceType.SYNTHETIC]
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...] = Field(min_length=4)

    @model_validator(mode="after")
    def validate_outcomes(self) -> CalibrationRedesignV2ExpectedOutcomes:
        """Require ordered post-hoc outcomes and cumulative prefix-survival labels."""

        expected_role = _expected_role(self.split)
        if self.data_role is not expected_role:
            raise ValueError("V2 outcome data_role must match its governed split")
        outcomes_by_round: dict[int, list[SyntheticTraceExpectedOutcome]] = {}
        for outcome in self.outcomes:
            if outcome.trace_id != self.trace_id:
                raise ValueError("all V2 outcomes must use the enclosing trace_id")
            outcomes_by_round.setdefault(outcome.decode_round, []).append(outcome)
        for round_outcomes in outcomes_by_round.values():
            expected_position = 1
            prefix_survives = True
            for outcome in round_outcomes:
                if outcome.block_position_index != expected_position:
                    raise ValueError("V2 outcomes must be contiguous from position one")
                prefix_survives = prefix_survives and outcome.observed_acceptance
                if outcome.prefix_survival_label is not prefix_survives:
                    raise ValueError("V2 prefix_survival_label must equal cumulative acceptance")
                expected_position += 1
        return self


class CalibrationRedesignV2ReplayCase(StrictContract):
    """Typed pairing of V2 runtime input and post-hoc outcomes after both are available."""

    runtime_input: CalibrationRedesignV2RuntimeInput
    expected_outcomes: CalibrationRedesignV2ExpectedOutcomes

    @model_validator(mode="after")
    def validate_runtime_outcome_alignment(self) -> CalibrationRedesignV2ReplayCase:
        """Align fields and positions without making outcomes runtime-visible."""

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
                raise ValueError(f"V2 runtime and outcomes disagree on {field_name}")
        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in runtime.contexts
        }
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in outcomes.outcomes
        }
        if set(contexts_by_key) != set(outcomes_by_key):
            raise ValueError("V2 runtime and outcomes must have identical position keys")
        _validate_visible_prefixes(contexts_by_key, outcomes.outcomes)
        return self


def validate_calibration_redesign_v2_replay_case_membership(
    replay_case: CalibrationRedesignV2ReplayCase,
    registry: CalibrationRedesignV2ScenarioFamilyRegistry,
) -> None:
    """Verify a typed V2 replay case belongs to exactly one finalized registry family."""

    if not isinstance(registry, CalibrationRedesignV2ScenarioFamilyRegistry):
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.UNTRUSTED_REGISTRY,
            "V2 case membership requires a finalized V2 scenario-family registry",
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
    if family is None:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V2 runtime case references an unregistered scenario family",
        )
    if runtime.case_id not in family.case_ids:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V2 runtime case ID is not reserved by its scenario family",
        )
    if runtime.split is not family.split or runtime.data_role is not family.primary_data_role:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V2 runtime split or data role does not match its scenario-family registry",
        )



def load_calibration_redesign_v2_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationRedesignV2ReplayCase:
    """Load one governed V2 case pair and verify its finalized registry membership."""

    if not _is_v2_case_id(case_id):
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            "V2 case asset loading requires a CRV2-### case identifier",
        )

    resolved_root = root.resolve()
    try:
        registry = load_calibration_redesign_v2_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_case_assets=True,
        )
    except CalibrationRedesignV2RegistryLoadError as error:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V2 case asset root is not authorized for loading: {error}",
        ) from error

    runtime_payload = _read_json_asset(resolved_root / "inputs" / "cases" / f"{case_id}.json")
    outcomes_payload = _read_json_asset(
        resolved_root / "expected_outcomes" / "cases" / f"{case_id}.json"
    )
    try:
        runtime_input = CalibrationRedesignV2RuntimeInput.model_validate(runtime_payload)
    except ValidationError as error:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.RUNTIME_SCHEMA_ERROR,
            f"V2 runtime case asset schema validation failed: {error}",
        ) from error
    try:
        expected_outcomes = CalibrationRedesignV2ExpectedOutcomes.model_validate(outcomes_payload)
    except ValidationError as error:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.OUTCOME_SCHEMA_ERROR,
            f"V2 expected-outcome case asset schema validation failed: {error}",
        ) from error
    try:
        replay_case = CalibrationRedesignV2ReplayCase(
            runtime_input=runtime_input,
            expected_outcomes=expected_outcomes,
        )
    except ValidationError as error:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.CASE_ALIGNMENT_ERROR,
            f"V2 runtime and expected-outcome case assets do not align: {error}",
        ) from error

    validate_calibration_redesign_v2_replay_case_membership(replay_case, registry)
    return replay_case


def _read_json_asset(path: Path) -> Mapping[str, Any]:
    """Read one local V2 case asset with explicit schema and provenance failures."""

    try:
        payload: Any = json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.CASE_ASSET_PROVENANCE_MISMATCH,
            f"unable to read V2 case asset: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"invalid JSON in V2 case asset {path.name}: {error.msg}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationRedesignV2CaseContractError(
            CalibrationRedesignV2CaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V2 case asset must be a JSON object: {path.name}",
        )
    return payload


def _is_v2_case_id(case_id: str) -> bool:
    return (
        case_id.startswith("CRV2-")
        and len(case_id) == 8
        and case_id.removeprefix("CRV2-").isdigit()
    )


def _expected_role(split: TraceSplit) -> TraceDataRole:
    expected_roles = {
        TraceSplit.DEVELOPMENT: TraceDataRole.SYNTHETIC_FIXTURE,
        TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
        TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
        TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
    }
    return expected_roles[split]


def _validate_visible_prefixes(
    contexts_by_key: dict[tuple[int, int], CausalSchedulerContext],
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...],
) -> None:
    outcomes_by_round: dict[int, list[SyntheticTraceExpectedOutcome]] = {}
    for outcome in outcomes:
        outcomes_by_round.setdefault(outcome.decode_round, []).append(outcome)
    for decode_round, round_outcomes in outcomes_by_round.items():
        expected_prefix: tuple[int, ...] = ()
        for outcome in round_outcomes:
            context = contexts_by_key[(decode_round, outcome.block_position_index)]
            if context.visible_prefix_token_ids != expected_prefix:
                raise ValueError(
                    "V2 visible prefix must match prior evaluation-only candidate token IDs"
                )
            expected_prefix = (*expected_prefix, outcome.candidate_token_id)
