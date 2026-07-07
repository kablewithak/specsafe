"""Quarantined V5 quarantined final-evaluation case contracts and loaders.

CSV5-201 through CSV5-236 are fresh held-out final-evaluation case pairs. They are
physically separate from V5 calibration assets and may not be supplied to fitting,
threshold selection, scheduling, policy execution, or a held-out assessment. This
module authorizes fixture loading only; it does not create a final manifest.
"""

from __future__ import annotations

import json
from collections import Counter
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

_V5_FINAL_CURVE_COVERAGE_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(201, 210))
_V5_FINAL_POSITION_SPREAD_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(210, 219))
_V5_FINAL_WORKLOAD_VARIATION_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(219, 228))
_V5_FINAL_MIXED_RELIABILITY_CONTRAST_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(228, 237)
)
_V5_FINAL_CURVE_COVERAGE_FAMILY_ID = "CSV5-FINAL-CURVE-COVERAGE"
_V5_FINAL_POSITION_SPREAD_FAMILY_ID = "CSV5-FINAL-POSITION-SPREAD"
_V5_FINAL_WORKLOAD_VARIATION_FAMILY_ID = "CSV5-FINAL-WORKLOAD-VARIATION"
_V5_FINAL_MIXED_RELIABILITY_CONTRAST_FAMILY_ID = "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST"
_FINAL_FAMILY_CONFIGURATION = {
    _V5_FINAL_CURVE_COVERAGE_FAMILY_ID: (
        _V5_FINAL_CURVE_COVERAGE_CASE_IDS,
        "final_curve_coverage_authored",
    ),
    _V5_FINAL_POSITION_SPREAD_FAMILY_ID: (
        _V5_FINAL_POSITION_SPREAD_CASE_IDS,
        "final_position_spread_authored",
    ),
    _V5_FINAL_WORKLOAD_VARIATION_FAMILY_ID: (
        _V5_FINAL_WORKLOAD_VARIATION_CASE_IDS,
        "final_workload_variation_authored",
    ),
    _V5_FINAL_MIXED_RELIABILITY_CONTRAST_FAMILY_ID: (
        _V5_FINAL_MIXED_RELIABILITY_CONTRAST_CASE_IDS,
        "final_mixed_reliability_contrast_authored",
    ),
}


class CalibrationSuccessorV5FinalCaseViolationCode(StrEnum):
    """Machine-readable reasons a held-out V5 final case cannot cross this boundary."""

    RUNTIME_SCHEMA_ERROR = "calibration_successor_v5_final_runtime_schema_error"
    OUTCOME_SCHEMA_ERROR = "calibration_successor_v5_final_outcome_schema_error"
    CASE_ALIGNMENT_ERROR = "calibration_successor_v5_final_case_alignment_error"
    REGISTRY_MEMBERSHIP_ERROR = "calibration_successor_v5_final_registry_membership_error"
    UNTRUSTED_REGISTRY = "calibration_successor_v5_final_untrusted_registry"
    CASE_ASSET_LAYOUT_ERROR = "calibration_successor_v5_final_case_asset_layout_error"
    CASE_ASSET_PROVENANCE_MISMATCH = "calibration_successor_v5_final_case_asset_provenance_mismatch"


class CalibrationSuccessorV5FinalCaseContractError(ValueError):
    """Raised when one V5 held-out final case pair is malformed or unauthorised."""

    def __init__(self, code: CalibrationSuccessorV5FinalCaseViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CalibrationSuccessorV5FinalRuntimeInput(StrictContract):
    """Scheduler-visible inputs for one quarantined V5 held-out replay case."""

    schema_version: Literal["calibration-successor-v5-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-successor-v5"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CSV5-2[0-9]{2}$")
    trace_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CSV5-FINAL-CURVE-COVERAGE",
        "CSV5-FINAL-POSITION-SPREAD",
        "CSV5-FINAL-WORKLOAD-VARIATION",
        "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST",
    ]
    split: Literal[TraceSplit.FINAL_EVALUATION]
    data_role: Literal[TraceDataRole.HELD_OUT_EVALUATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    generation_note: str = Field(min_length=1, max_length=500)
    contexts: tuple[CausalSchedulerContext, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_runtime_contexts(self) -> CalibrationSuccessorV5FinalRuntimeInput:
        for expected_position, context in enumerate(self.contexts, start=1):
            if context.trace_id != self.trace_id:
                raise ValueError("all V5 final runtime contexts must use the enclosing trace_id")
            if context.request_id != self.request_id:
                raise ValueError("all V5 final runtime contexts must use the enclosing request_id")
            if context.decode_round != 0:
                raise ValueError("V5 final-evaluation cases must use decode round zero")
            if context.block_position_index != expected_position:
                raise ValueError("V5 final runtime contexts must be contiguous from position one")
        return self


class CalibrationSuccessorV5FinalExpectedOutcomes(StrictContract):
    """Evaluation-only V5 held-out outcomes kept separate from runtime inputs."""

    schema_version: Literal["calibration-successor-v5-case-v1"]
    fixture_set_id: Literal["synthetic-calibration-successor-v5"]
    fixture_set_version: Literal["1.0.0"]
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(pattern=r"^CSV5-2[0-9]{2}$")
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CSV5-FINAL-CURVE-COVERAGE",
        "CSV5-FINAL-POSITION-SPREAD",
        "CSV5-FINAL-WORKLOAD-VARIATION",
        "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST",
    ]
    split: Literal[TraceSplit.FINAL_EVALUATION]
    data_role: Literal[TraceDataRole.HELD_OUT_EVALUATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    outcomes: tuple[SyntheticTraceExpectedOutcome, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_outcomes(self) -> CalibrationSuccessorV5FinalExpectedOutcomes:
        prefix_survives = True
        for expected_position, outcome in enumerate(self.outcomes, start=1):
            if outcome.trace_id != self.trace_id:
                raise ValueError("all V5 final outcomes must use the enclosing trace_id")
            if outcome.decode_round != 0:
                raise ValueError("V5 final outcomes must use decode round zero")
            if outcome.block_position_index != expected_position:
                raise ValueError("V5 final outcomes must be contiguous from position one")
            prefix_survives = prefix_survives and outcome.observed_acceptance
            if outcome.prefix_survival_label is not prefix_survives:
                raise ValueError("V5 final prefix_survival_label must equal cumulative acceptance")
        return self


class CalibrationSuccessorV5FinalReplayCase(StrictContract):
    """One held-out V5 case joined only after its separate evidence halves load."""

    runtime_input: CalibrationSuccessorV5FinalRuntimeInput
    expected_outcomes: CalibrationSuccessorV5FinalExpectedOutcomes

    @model_validator(mode="after")
    def validate_alignment(self) -> CalibrationSuccessorV5FinalReplayCase:
        runtime = self.runtime_input
        outcomes = self.expected_outcomes
        for field_name in (
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
        ):
            if getattr(runtime, field_name) != getattr(outcomes, field_name):
                raise ValueError(f"V5 final runtime and outcomes disagree on {field_name}")
        contexts_by_key = {
            (context.decode_round, context.block_position_index): context
            for context in runtime.contexts
        }
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in outcomes.outcomes
        }
        if set(contexts_by_key) != set(outcomes_by_key):
            raise ValueError("V5 final runtime and outcomes must have identical position keys")
        expected_prefix: tuple[int, ...] = ()
        for outcome in outcomes.outcomes:
            context = contexts_by_key[(outcome.decode_round, outcome.block_position_index)]
            if context.visible_prefix_token_ids != expected_prefix:
                raise ValueError(
                    "V5 final visible prefix must match prior evaluation-only candidate token IDs"
                )
            expected_prefix = (*expected_prefix, outcome.candidate_token_id)
        return self


def validate_calibration_successor_v5_final_replay_case_membership(
    replay_case: CalibrationSuccessorV5FinalReplayCase,
    registry: CalibrationSuccessorV5ScenarioFamilyRegistry,
) -> None:
    """Verify a held-out case belongs to an authored, still-quarantined final family."""

    if type(registry) is not CalibrationSuccessorV5ScenarioFamilyRegistry:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.UNTRUSTED_REGISTRY,
            "V5 final case membership requires the exact V5 scenario-family registry",
        )
    runtime = replay_case.runtime_input
    configuration = _FINAL_FAMILY_CONFIGURATION.get(runtime.scenario_family_id)
    if configuration is None:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V5 final replay case uses an unauthorised final family",
        )
    expected_case_ids, expected_authoring_status = configuration
    if runtime.case_id not in expected_case_ids:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V5 final replay case identifier is outside its declared family reservation",
        )
    family = next(
        item for item in registry.families if item.scenario_family_id == runtime.scenario_family_id
    )
    if family.authoring_status != expected_authoring_status:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V5 final family is not authorised for loading at the current stage",
        )
    if (
        family.split is not TraceSplit.FINAL_EVALUATION
        or not family.is_final_evaluation_quarantined
    ):
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            "V5 final family must remain held-out and quarantined",
        )


def load_calibration_successor_v5_final_curve_coverage_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5FinalReplayCase:
    """Load one CSV5-201..CSV5-209 final curve pair without assessment execution."""

    return _load_final_replay_case(
        root,
        case_id,
        expected_case_ids=_V5_FINAL_CURVE_COVERAGE_CASE_IDS,
        family_id=_V5_FINAL_CURVE_COVERAGE_FAMILY_ID,
        boundary_label="final curve-coverage",
    )


def load_calibration_successor_v5_final_position_spread_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5FinalReplayCase:
    """Load one CSV5-210..CSV5-218 final position pair without assessment execution."""

    return _load_final_replay_case(
        root,
        case_id,
        expected_case_ids=_V5_FINAL_POSITION_SPREAD_CASE_IDS,
        family_id=_V5_FINAL_POSITION_SPREAD_FAMILY_ID,
        boundary_label="final position-spread",
    )


def load_calibration_successor_v5_final_workload_variation_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5FinalReplayCase:
    """Load one CSV5-219..CSV5-227 final workload pair without assessment execution."""

    return _load_final_replay_case(
        root,
        case_id,
        expected_case_ids=_V5_FINAL_WORKLOAD_VARIATION_CASE_IDS,
        family_id=_V5_FINAL_WORKLOAD_VARIATION_FAMILY_ID,
        boundary_label="final workload-variation",
    )


def load_calibration_successor_v5_final_mixed_reliability_contrast_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationSuccessorV5FinalReplayCase:
    """Load one CSV5-228..CSV5-236 final mixed-reliability pair without assessment."""

    return _load_final_replay_case(
        root,
        case_id,
        expected_case_ids=_V5_FINAL_MIXED_RELIABILITY_CONTRAST_CASE_IDS,
        family_id=_V5_FINAL_MIXED_RELIABILITY_CONTRAST_FAMILY_ID,
        boundary_label="final mixed-reliability contrast",
    )


def _load_final_replay_case(
    root: Path,
    case_id: str,
    *,
    expected_case_ids: tuple[str, ...],
    family_id: str,
    boundary_label: str,
) -> CalibrationSuccessorV5FinalReplayCase:
    if case_id not in expected_case_ids:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"{boundary_label} loading requires a case identifier from its reserved range",
        )
    resolved_root = root.resolve()
    try:
        registry = load_calibration_successor_v5_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_final_mixed_reliability_contrast_assets=True,
        )
    except CalibrationSuccessorV5RegistryLoadError as error:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V5 {boundary_label} root is not authorised for loading: {error}",
        ) from error
    runtime_payload = _read_json_asset(
        resolved_root / "final_evaluation" / "inputs" / "cases" / f"{case_id}.json"
    )
    outcomes_payload = _read_json_asset(
        resolved_root / "final_evaluation" / "expected_outcomes" / "cases" / f"{case_id}.json"
    )
    try:
        runtime_input = CalibrationSuccessorV5FinalRuntimeInput.model_validate(runtime_payload)
    except ValidationError as error:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.RUNTIME_SCHEMA_ERROR,
            f"V5 {boundary_label} runtime case asset schema validation failed: {error}",
        ) from error
    try:
        expected_outcomes = CalibrationSuccessorV5FinalExpectedOutcomes.model_validate(
            outcomes_payload
        )
    except ValidationError as error:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.OUTCOME_SCHEMA_ERROR,
            f"V5 {boundary_label} expected-outcome asset schema validation failed: {error}",
        ) from error
    try:
        replay_case = CalibrationSuccessorV5FinalReplayCase(
            runtime_input=runtime_input,
            expected_outcomes=expected_outcomes,
        )
    except ValidationError as error:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.CASE_ALIGNMENT_ERROR,
            f"V5 {boundary_label} runtime and expected-outcome assets do not align: {error}",
        ) from error
    if replay_case.runtime_input.scenario_family_id != family_id:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.REGISTRY_MEMBERSHIP_ERROR,
            f"V5 {boundary_label} case has the wrong scenario family identifier",
        )
    validate_calibration_successor_v5_final_replay_case_membership(replay_case, registry)
    return replay_case


def summarize_final_curve_coverage_workloads(
    replay_cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...],
) -> dict[str, int]:
    """Return held-out curve workload counts without using labels for decisions."""

    return _summarize_final_family_workloads(
        replay_cases,
        _V5_FINAL_CURVE_COVERAGE_CASE_IDS,
        "V5 final curve workload summary",
    )


def summarize_final_position_spread_workloads(
    replay_cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...],
) -> dict[str, int]:
    """Return held-out position-spread workload counts without using labels for decisions."""

    return _summarize_final_family_workloads(
        replay_cases,
        _V5_FINAL_POSITION_SPREAD_CASE_IDS,
        "V5 final position workload summary",
    )


def summarize_final_workload_variation_workloads(
    replay_cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...],
) -> dict[str, int]:
    """Return held-out workload-variation counts without using labels for decisions."""

    return _summarize_final_family_workloads(
        replay_cases,
        _V5_FINAL_WORKLOAD_VARIATION_CASE_IDS,
        "V5 final workload summary",
    )


def summarize_final_mixed_reliability_contrast_workloads(
    replay_cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...],
) -> dict[str, int]:
    """Return held-out mixed-reliability workload counts without policy execution."""

    return _summarize_final_family_workloads(
        replay_cases,
        _V5_FINAL_MIXED_RELIABILITY_CONTRAST_CASE_IDS,
        "V5 final mixed-reliability workload summary",
    )


def _summarize_final_family_workloads(
    replay_cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...],
    expected_case_ids: tuple[str, ...],
    label: str,
) -> dict[str, int]:
    replay_case_ids = tuple(case.runtime_input.case_id for case in replay_cases)
    if replay_case_ids != expected_case_ids:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"{label} requires all nine ordered cases",
        )
    counts = Counter(case.runtime_input.contexts[0].workload_type.value for case in replay_cases)
    return dict(sorted(counts.items()))


def _read_json_asset(path: Path) -> Mapping[str, Any]:
    try:
        payload: Any = json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.CASE_ASSET_PROVENANCE_MISMATCH,
            f"unable to read V5 final case asset: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"invalid JSON in V5 final case asset {path.name}: {error.msg}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationSuccessorV5FinalCaseContractError(
            CalibrationSuccessorV5FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR,
            f"V5 final case asset must be a JSON object: {path.name}",
        )
    return payload
