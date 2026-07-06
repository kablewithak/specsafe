"""V5 schema-only evidence namespace and scenario-family registry.

This module establishes only the fresh V5 fixture root, exact case reservations, split
roles, and a fail-closed authoring boundary. It does not author runtime inputs, expected
outcomes, manifests, calibration artifacts, fit diagnostics, final evidence, and
scheduling or policy-comparison controls.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from specsafe.contracts.models import (
    StrictContract,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
)

_V5_REGISTRY_FILENAME = "scenario_family_registry.json"
_V5_PROPOSAL_MANIFEST_FILENAME = "PROPOSAL_MANIFEST.md"
_V5_AUTHORING_LEDGER_FILENAME = "authoring_ledger.md"
_V5_SCHEMA_ONLY_ROOT_FILENAMES = {
    _V5_REGISTRY_FILENAME,
    _V5_PROPOSAL_MANIFEST_FILENAME,
    _V5_AUTHORING_LEDGER_FILENAME,
}
_V5_FORBIDDEN_ROOT_PATH_NAMES = {
    "inputs",
    "expected_outcomes",
    "final_evaluation",
    "adversarial_regression",
    "calibration_manifest.json",
    "final_evaluation_manifest.json",
    "final_evidence_index.json",
    "artifact.json",
    "fit_report.json",
    "heldout_assessment.json",
    "result.json",
}

_V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(101, 113)
)
_V5_CALIBRATION_POSITION_SPREAD_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(113, 125)
)
_V5_CALIBRATION_WORKLOAD_VARIATION_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(125, 137)
)
_V5_CALIBRATION_MIXED_RELIABILITY_CONTRAST_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(137, 149)
)
_V5_FINAL_CURVE_COVERAGE_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(201, 210)
)
_V5_FINAL_POSITION_SPREAD_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(210, 219)
)
_V5_FINAL_WORKLOAD_VARIATION_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(219, 228)
)
_V5_FINAL_MIXED_RELIABILITY_CONTRAST_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(228, 237)
)
_V5_ADVERSARIAL_CAUSAL_GUARD_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(301, 307)
)
_V5_ADVERSARIAL_PROVENANCE_GATE_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(307, 313)
)

_V5_EXPECTED_CASE_IDS_BY_FAMILY = {
    "CSV5-CAL-CURVE-COVERAGE": _V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
    "CSV5-CAL-POSITION-SPREAD": _V5_CALIBRATION_POSITION_SPREAD_CASE_IDS,
    "CSV5-CAL-WORKLOAD-VARIATION": _V5_CALIBRATION_WORKLOAD_VARIATION_CASE_IDS,
    "CSV5-CAL-MIXED-RELIABILITY-CONTRAST": (
        _V5_CALIBRATION_MIXED_RELIABILITY_CONTRAST_CASE_IDS
    ),
    "CSV5-FINAL-CURVE-COVERAGE": _V5_FINAL_CURVE_COVERAGE_CASE_IDS,
    "CSV5-FINAL-POSITION-SPREAD": _V5_FINAL_POSITION_SPREAD_CASE_IDS,
    "CSV5-FINAL-WORKLOAD-VARIATION": _V5_FINAL_WORKLOAD_VARIATION_CASE_IDS,
    "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST": (
        _V5_FINAL_MIXED_RELIABILITY_CONTRAST_CASE_IDS
    ),
    "CSV5-ADV-CAUSAL-GUARD": _V5_ADVERSARIAL_CAUSAL_GUARD_CASE_IDS,
    "CSV5-ADV-PROVENANCE-GATE": _V5_ADVERSARIAL_PROVENANCE_GATE_CASE_IDS,
}
_V5_EXPECTED_FAMILY_IDS = frozenset(_V5_EXPECTED_CASE_IDS_BY_FAMILY)
_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}
_HISTORICAL_DATA_BEARING_MARKERS = (
    b"crv1-",
    b"crv2-",
    b"crv3-",
    b"crv4-",
    b"synthetic-calibration-redesign-v4",
    b"bounded-platt-scaling-v1",
    b"regularized-isotonic-calibration-v4",
)


class CalibrationSuccessorV5RegistryViolationCode(StrEnum):
    """Machine-readable V5 namespace and schema-only boundary violations."""

    REGISTRY_SCHEMA_ERROR = "calibration_successor_v5_registry_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = (
        "calibration_successor_v5_registry_provenance_mismatch"
    )
    HISTORICAL_EVIDENCE_REFERENCE = (
        "calibration_successor_v5_historical_evidence_reference"
    )
    SCHEMA_ONLY_BOUNDARY_VIOLATION = (
        "calibration_successor_v5_schema_only_boundary_violation"
    )


class CalibrationSuccessorV5RegistryLoadError(ValueError):
    """Raised when V5 registry metadata or its schema-only root is invalid."""

    def __init__(
        self,
        code: CalibrationSuccessorV5RegistryViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationSuccessorV5ObservationBudget(StrictContract):
    """Predeclared V5 corpus sizes before any case bytes exist."""

    calibration_case_count: Literal[48]
    final_evaluation_case_count: Literal[36]
    adversarial_regression_case_count: Literal[12]
    candidate_positions_per_case: Literal[4]
    calibration_observation_count: Literal[192]
    final_evaluation_observation_count: Literal[144]
    adversarial_regression_observation_count: Literal[48]


class CalibrationSuccessorV5WorkloadAllocation(StrictContract):
    """Fixed workload balance for every V5 final-evaluation family."""

    structured_text_case_count: Literal[3]
    code_case_count: Literal[3]
    open_ended_chat_case_count: Literal[3]


class CalibrationSuccessorV5ScenarioFamilyRecord(StrictContract):
    """One V5 family reservation with split and quarantine controls."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    primary_data_role: TraceDataRole
    reserved_case_ids: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=500)
    target_failure_modes: tuple[str, ...] = Field(min_length=1)
    is_final_evaluation_quarantined: bool
    is_adversarial_regression_quarantined: bool
    workload_allocation: CalibrationSuccessorV5WorkloadAllocation | None = None
    authoring_status: Literal["reserved_for_v5_case_authoring"]

    @field_validator("reserved_case_ids")
    @classmethod
    def validate_reserved_case_ids(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("V5 case IDs must be unique within one family")
        if any(not case_id.startswith("CSV5-") for case_id in case_ids):
            raise ValueError("V5 case IDs must use the CSV5 namespace")
        return case_ids

    @field_validator("target_failure_modes")
    @classmethod
    def validate_target_failure_modes(
        cls,
        failure_modes: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(set(failure_modes)) != len(failure_modes):
            raise ValueError("V5 target failure modes must be unique within one family")
        return failure_modes

    @model_validator(mode="after")
    def validate_family_governance(
        self,
    ) -> "CalibrationSuccessorV5ScenarioFamilyRecord":
        if not self.scenario_family_id.startswith("CSV5-"):
            raise ValueError("V5 scenario-family IDs must use the CSV5 namespace")

        expected_role = _EXPECTED_DATA_ROLE_BY_SPLIT.get(self.split)
        if expected_role is None or self.primary_data_role is not expected_role:
            raise ValueError("primary_data_role must match the governed V5 split role")

        final_quarantine_expected = self.split is TraceSplit.FINAL_EVALUATION
        adversarial_quarantine_expected = (
            self.split is TraceSplit.ADVERSARIAL_REGRESSION
        )
        if self.is_final_evaluation_quarantined is not final_quarantine_expected:
            raise ValueError(
                "final-evaluation quarantine must match the declared V5 split"
            )
        if (
            self.is_adversarial_regression_quarantined
            is not adversarial_quarantine_expected
        ):
            raise ValueError(
                "adversarial-regression quarantine must match the declared V5 split"
            )
        if final_quarantine_expected != (self.workload_allocation is not None):
            raise ValueError(
                "only V5 final-evaluation families may declare workload allocation"
            )
        if self.authoring_status != "reserved_for_v5_case_authoring":
            raise ValueError(
                "V5 schema-only registry cannot claim authored case assets"
            )
        return self


class CalibrationSuccessorV5ScenarioFamilyRegistry(StrictContract):
    """Schema-only V5 programme registry before any runtime or outcome asset exists."""

    schema_version: Literal["calibration-successor-v5-scenario-family-registry-v1"]
    registry_status: Literal["schema_only"]
    fixture_set_id: Literal["synthetic-calibration-successor-v5"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    method_constitution_version: Literal[
        "v5-bounded-monotone-beta-calibration-eligibility-charter-v1"
    ]
    calibration_method_id: Literal["bounded-monotone-beta-calibration-v5"]
    maximum_candidate_positions: Literal[4]
    historical_data_bearing_evidence_used: Literal[False]
    v5_runtime_or_outcome_assets_authored: Literal[False]
    v5_calibration_manifest_authored: Literal[False]
    v5_calibration_artifact_authored: Literal[False]
    v5_calibration_fit_diagnostics_authored: Literal[False]
    v5_final_evaluation_runtime_or_outcome_assets_authored: Literal[False]
    v5_final_evaluation_manifest_authored: Literal[False]
    v5_final_assessment_contract_merged: Literal[True]
    v5_final_heldout_calibration_assessment_authored: Literal[False]
    observation_budget: CalibrationSuccessorV5ObservationBudget
    families: tuple[CalibrationSuccessorV5ScenarioFamilyRecord, ...] = Field(
        min_length=10,
        max_length=10,
    )
    explicit_exclusions: tuple[str, ...] = Field(min_length=10)
    next_authorized_artifact: Literal["v5-calibration-curve-coverage-fixtures"]

    @model_validator(mode="after")
    def validate_registry_governance(
        self,
    ) -> "CalibrationSuccessorV5ScenarioFamilyRegistry":
        if self.historical_data_bearing_evidence_used:
            raise ValueError("historical data-bearing evidence is prohibited in V5")
        if self.v5_runtime_or_outcome_assets_authored:
            raise ValueError("V5 schema-only registry cannot claim calibration assets")
        if self.v5_calibration_manifest_authored:
            raise ValueError("V5 schema-only registry cannot claim a frozen manifest")
        if self.v5_calibration_artifact_authored:
            raise ValueError("V5 schema-only registry cannot claim a fitted artifact")
        if self.v5_calibration_fit_diagnostics_authored:
            raise ValueError("V5 schema-only registry cannot claim fit diagnostics")
        if self.v5_final_evaluation_runtime_or_outcome_assets_authored:
            raise ValueError("V5 schema-only registry cannot claim final assets")
        if self.v5_final_evaluation_manifest_authored:
            raise ValueError("V5 schema-only registry cannot claim a final manifest")
        if self.v5_final_heldout_calibration_assessment_authored:
            raise ValueError(
                "V5 schema-only registry cannot claim a held-out assessment"
            )

        family_ids = tuple(family.scenario_family_id for family in self.families)
        if len(set(family_ids)) != len(family_ids):
            raise ValueError("V5 scenario-family IDs must be unique")
        if set(family_ids) != _V5_EXPECTED_FAMILY_IDS:
            raise ValueError(
                "V5 scenario-family IDs must match the complete reserved plan"
            )

        all_case_ids = tuple(
            case_id for family in self.families for case_id in family.reserved_case_ids
        )
        if len(set(all_case_ids)) != len(all_case_ids):
            raise ValueError("V5 case IDs must be unique across all families")
        for family in self.families:
            expected_case_ids = _V5_EXPECTED_CASE_IDS_BY_FAMILY[
                family.scenario_family_id
            ]
            if family.reserved_case_ids != expected_case_ids:
                raise ValueError(
                    "V5 family case IDs must match the fixed reservation ranges exactly"
                )

        split_case_counts = {
            split: sum(
                len(family.reserved_case_ids)
                for family in self.families
                if family.split is split
            )
            for split in _EXPECTED_DATA_ROLE_BY_SPLIT
        }
        if split_case_counts[TraceSplit.CALIBRATION] != 48:
            raise ValueError("V5 calibration reserved-case count must equal 48")
        if split_case_counts[TraceSplit.FINAL_EVALUATION] != 36:
            raise ValueError("V5 final-evaluation reserved-case count must equal 36")
        if split_case_counts[TraceSplit.ADVERSARIAL_REGRESSION] != 12:
            raise ValueError("V5 adversarial reserved-case count must equal 12")

        final_families = tuple(
            family
            for family in self.families
            if family.split is TraceSplit.FINAL_EVALUATION
        )
        if len(final_families) != 4 or any(
            len(family.reserved_case_ids) != 9 for family in final_families
        ):
            raise ValueError("each V5 final family must reserve exactly nine cases")
        if any(family.workload_allocation is None for family in final_families):
            raise ValueError(
                "each V5 final family requires a fixed workload allocation"
            )

        required_exclusions = {
            "No V5 runtime-input or expected-outcome assets are present.",
            "No V5 calibration or final-evaluation manifest is present.",
            (
                "No V5 calibration artifact, fit diagnostic, or final assessment "
                "result is present."
            ),
            "No V5 fitter, threshold selection, or parameter mutation is authorized.",
            (
                "No V5 scheduler, baseline comparison, capacity profile, utility "
                "scorer, or runtime control is authorized."
            ),
            "No historical data-bearing evidence influenced V5 fixture reservations.",
            "V5 final-evaluation and adversarial reservations remain quarantined.",
            (
                "The V5 final-assessment contract does not authorize evidence loading "
                "or assessment execution."
            ),
        }
        if not required_exclusions.issubset(set(self.explicit_exclusions)):
            raise ValueError("V5 registry must retain its schema-only exclusions")
        return self


def load_calibration_successor_v5_scenario_family_registry(
    path: Path,
) -> CalibrationSuccessorV5ScenarioFamilyRegistry:
    """Load only the V5 schema-only registry through its fail-closed root boundary."""

    root = path.parent.resolve()
    assert_calibration_successor_v5_schema_only_fixture_root(root)
    if path.resolve() != root / _V5_REGISTRY_FILENAME:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            (
                "V5 registry must be loaded from scenario_family_registry.json "
                "at its fixture root"
            ),
        )

    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            f"unable to read V5 scenario-family registry: {error}",
        ) from error

    _reject_historical_data_bearing_reference(raw_bytes)
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_SCHEMA_ERROR,
            f"V5 scenario-family registry is not valid UTF-8 JSON: {error}",
        ) from error
    try:
        return CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_SCHEMA_ERROR,
            f"V5 scenario-family registry validation failed: {error}",
        ) from error


def assert_calibration_successor_v5_schema_only_fixture_root(root: Path) -> None:
    """Reject all case-bearing or assessment assets before the V5 authoring stage."""

    resolved_root = root.resolve()
    if not resolved_root.is_dir():
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V5 fixture root must be an existing directory",
        )

    unexpected_paths = []
    present_names = set()
    for child in resolved_root.iterdir():
        present_names.add(child.name)
        if child.name in _V5_FORBIDDEN_ROOT_PATH_NAMES or child.is_dir():
            unexpected_paths.append(child.name)
        elif child.name not in _V5_SCHEMA_ONLY_ROOT_FILENAMES:
            unexpected_paths.append(child.name)
    missing_names = _V5_SCHEMA_ONLY_ROOT_FILENAMES - present_names
    if missing_names:
        unexpected_paths.extend(f"missing:{name}" for name in sorted(missing_names))
    if unexpected_paths:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION,
            "V5 schema-only fixture root contains unauthorised assets: "
            + ", ".join(sorted(unexpected_paths)),
        )

    for filename in sorted(_V5_SCHEMA_ONLY_ROOT_FILENAMES):
        try:
            _reject_historical_data_bearing_reference(
                (resolved_root / filename).read_bytes()
            )
        except OSError as error:
            raise CalibrationSuccessorV5RegistryLoadError(
                (
                    CalibrationSuccessorV5RegistryViolationCode
                    .REGISTRY_PROVENANCE_MISMATCH
                ),
                f"unable to read V5 schema-only metadata {filename}: {error}",
            ) from error


def _reject_historical_data_bearing_reference(raw_bytes: bytes) -> None:
    normalized = raw_bytes.lower()
    if any(marker in normalized for marker in _HISTORICAL_DATA_BEARING_MARKERS):
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.HISTORICAL_EVIDENCE_REFERENCE,
            (
                "V5 schema-only metadata must not reference historical "
                "data-bearing evidence"
            ),
        )
