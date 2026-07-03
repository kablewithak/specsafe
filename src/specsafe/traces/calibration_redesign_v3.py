"""V3 schema-only registry controls for the full north-star programme.

This module creates the first V3 engineering boundary: a typed registry and a
fail-closed fixture-root guard. It deliberately contains no V3 case payloads,
outcomes, manifests, calibration fitting, or scheduler behaviour.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from specsafe.contracts.models import StrictContract, TraceDataRole, TraceSourceType, TraceSplit

_V3_REGISTRY_FILENAME = "scenario_family_registry.json"
_ALLOWED_SCHEMA_ONLY_FILENAMES = {
    "PROPOSAL_MANIFEST.md",
    "authoring_ledger.md",
    _V3_REGISTRY_FILENAME,
}
_FORBIDDEN_SCHEMA_ONLY_PATH_NAMES = {
    "inputs",
    "expected_outcomes",
    "calibration_manifest.json",
    "final_evaluation_manifest.json",
    "artifact.json",
    "fit_report.json",
    "heldout_assessment.json",
}
_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}


class CalibrationRedesignV3RegistryViolationCode(StrEnum):
    """Machine-readable reasons the V3 schema-only boundary cannot be trusted."""

    REGISTRY_SCHEMA_ERROR = "calibration_redesign_v3_registry_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = "calibration_redesign_v3_registry_provenance_mismatch"
    V1_OR_V2_EVIDENCE_REFERENCE = "calibration_redesign_v3_v1_or_v2_evidence_reference"
    SCHEMA_ONLY_BOUNDARY_VIOLATION = "calibration_redesign_v3_schema_only_boundary_violation"


class CalibrationRedesignV3RegistryLoadError(ValueError):
    """Typed error raised when V3 registry metadata violates the active boundary."""

    def __init__(
        self,
        code: CalibrationRedesignV3RegistryViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV3ObservationBudget(StrictContract):
    """The predeclared V3 observation plan before any case bytes are authored."""

    calibration_case_count: Literal[36]
    final_evaluation_case_count: Literal[24]
    adversarial_regression_case_count: Literal[8]
    candidate_positions_per_case: Literal[4]
    calibration_observation_count: Literal[144]
    final_evaluation_observation_count: Literal[96]
    adversarial_regression_observation_count: Literal[32]
    calibration_quantile_group_count: Literal[8]


class CalibrationRedesignV3WorkloadAllocation(StrictContract):
    """Required workload balance for one final-evaluation capacity family."""

    structured_text_case_count: Literal[2]
    code_case_count: Literal[2]
    open_ended_chat_case_count: Literal[2]


class CalibrationRedesignV3ScenarioFamilyRecord(StrictContract):
    """One reserved V3 family with IDs but without authored runtime or outcome bytes."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    primary_data_role: TraceDataRole
    reserved_case_ids: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=500)
    target_failure_modes: tuple[str, ...] = Field(min_length=1)
    is_final_evaluation_quarantined: bool
    workload_allocation: CalibrationRedesignV3WorkloadAllocation | None = None
    authoring_status: Literal["reserved_for_v3_case_authoring"]

    @field_validator("reserved_case_ids")
    @classmethod
    def validate_reserved_case_ids(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        """Keep V3 IDs unique and insulated from closed V1 and V2 namespaces."""

        if len(set(case_ids)) != len(case_ids):
            raise ValueError("V3 case IDs must be unique within one family")
        if any(not case_id.startswith("CRV3-") for case_id in case_ids):
            raise ValueError("V3 case IDs must use the CRV3- namespace")
        if any(case_id.startswith(("CRV1-", "CRV2-", "STF-")) for case_id in case_ids):
            raise ValueError("closed V1 and V2 case namespaces are prohibited in V3")
        return case_ids

    @field_validator("target_failure_modes")
    @classmethod
    def validate_target_failure_modes(
        cls,
        target_failure_modes: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Prevent duplicate claims of diagnostic coverage in one family."""

        if len(set(target_failure_modes)) != len(target_failure_modes):
            raise ValueError("target failure modes must be unique within one V3 family")
        return target_failure_modes

    @model_validator(mode="after")
    def validate_family_governance(self) -> CalibrationRedesignV3ScenarioFamilyRecord:
        """Bind split, role, quarantine status, and workload allocation together."""

        if not self.scenario_family_id.startswith("CRV3-"):
            raise ValueError("V3 scenario-family IDs must use the CRV3- namespace")
        expected_role = _EXPECTED_DATA_ROLE_BY_SPLIT.get(self.split)
        if expected_role is None or self.primary_data_role is not expected_role:
            raise ValueError("primary_data_role must match the governed V3 split role")
        expected_quarantine = self.split is TraceSplit.FINAL_EVALUATION
        if self.is_final_evaluation_quarantined is not expected_quarantine:
            raise ValueError("final-evaluation quarantine must match the declared V3 split")
        if expected_quarantine != (self.workload_allocation is not None):
            raise ValueError(
                "only final-evaluation V3 families may declare the required workload allocation"
            )
        return self


class CalibrationRedesignV3ScenarioFamilyRegistry(StrictContract):
    """The frozen V3 schema-only registry before data authoring begins."""

    schema_version: Literal["calibration-redesign-v3-scenario-family-registry-v1"]
    registry_status: Literal["schema_only_frozen"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    method_constitution_version: Literal["v3-method-and-evidence-constitution-v1"]
    calibration_method_id: Literal["quantile-isotonic-calibration-v1"]
    adaptive_policy_id: Literal["causal-marginal-prefix-v1"]
    maximum_candidate_positions: Literal[4]
    v1_or_v2_data_bearing_evidence_used: Literal[False]
    v3_runtime_or_outcome_assets_authored: Literal[False]
    v3_manifests_authored: Literal[False]
    observation_budget: CalibrationRedesignV3ObservationBudget
    families: tuple[CalibrationRedesignV3ScenarioFamilyRecord, ...] = Field(min_length=1)
    explicit_exclusions: tuple[str, ...] = Field(min_length=6)
    next_authorized_artifact: Literal["v3-calibration-runtime-and-outcome-fixture-authoring"]

    @model_validator(mode="after")
    def validate_registry_governance(self) -> CalibrationRedesignV3ScenarioFamilyRegistry:
        """Enforce the predeclared V3 corpus shape without accepting evidence bytes."""

        if self.v1_or_v2_data_bearing_evidence_used:
            raise ValueError("V1 and V2 data-bearing evidence is prohibited in V3")
        if self.v3_runtime_or_outcome_assets_authored:
            raise ValueError("V3 runtime or outcome assets are not allowed at schema-only stage")
        if self.v3_manifests_authored:
            raise ValueError("V3 manifests are not allowed at schema-only stage")

        family_ids = [family.scenario_family_id for family in self.families]
        if len(set(family_ids)) != len(family_ids):
            raise ValueError("V3 scenario-family IDs must be unique")

        case_ids = [case_id for family in self.families for case_id in family.reserved_case_ids]
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("V3 case IDs must be unique across all families")

        split_case_counts = {
            split: sum(
                len(family.reserved_case_ids) for family in self.families if family.split is split
            )
            for split in _EXPECTED_DATA_ROLE_BY_SPLIT
        }
        if (
            split_case_counts[TraceSplit.CALIBRATION]
            != self.observation_budget.calibration_case_count
        ):
            raise ValueError("V3 calibration reserved-case count must equal 36")
        if (
            split_case_counts[TraceSplit.FINAL_EVALUATION]
            != self.observation_budget.final_evaluation_case_count
        ):
            raise ValueError("V3 final-evaluation reserved-case count must equal 24")
        if (
            split_case_counts[TraceSplit.ADVERSARIAL_REGRESSION]
            != self.observation_budget.adversarial_regression_case_count
        ):
            raise ValueError("V3 adversarial reserved-case count must equal 8")

        final_families = [
            family for family in self.families if family.split is TraceSplit.FINAL_EVALUATION
        ]
        expected_final_families = {
            "CRV3-FINAL-LIGHT-CAPACITY",
            "CRV3-FINAL-MODERATE-CAPACITY",
            "CRV3-FINAL-SATURATED-CAPACITY",
            "CRV3-FINAL-JAGGED-CAPACITY",
        }
        if {family.scenario_family_id for family in final_families} != expected_final_families:
            raise ValueError("V3 final families must match the frozen four-capacity constitution")
        if any(len(family.reserved_case_ids) != 6 for family in final_families):
            raise ValueError("each V3 final capacity family must reserve exactly six cases")

        required_exclusions = {
            "No V3 runtime-input fixture bytes are present.",
            "No V3 expected-outcome assets or labels are present.",
            "No V3 calibration or final-evaluation manifest is present.",
            "No V3 calibration fitting or scheduler code is authorized by this registry.",
            "No V1 or V2 data-bearing evidence influenced V3 method, thresholds, or case design.",
            "No V3 performance or promotion claim is made.",
        }
        if not required_exclusions.issubset(set(self.explicit_exclusions)):
            raise ValueError("V3 registry must retain every required schema-only exclusion")
        return self


def load_calibration_redesign_v3_scenario_family_registry(
    path: Path,
) -> CalibrationRedesignV3ScenarioFamilyRegistry:
    """Load the V3 registry only while its root remains free of data-bearing assets."""

    root = path.parent.resolve()
    assert_calibration_redesign_v3_schema_only_fixture_root(root)
    if path.resolve() != root / _V3_REGISTRY_FILENAME:
        raise CalibrationRedesignV3RegistryLoadError(
            CalibrationRedesignV3RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V3 registry must be loaded from scenario_family_registry.json at its fixture root",
        )
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV3RegistryLoadError(
            CalibrationRedesignV3RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            f"unable to read V3 scenario-family registry: {error}",
        ) from error

    _reject_closed_evidence_reference(raw_bytes)
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CalibrationRedesignV3RegistryLoadError(
            CalibrationRedesignV3RegistryViolationCode.REGISTRY_SCHEMA_ERROR,
            f"V3 scenario-family registry is not valid UTF-8 JSON: {error}",
        ) from error
    try:
        return CalibrationRedesignV3ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        raise CalibrationRedesignV3RegistryLoadError(
            _registry_violation_code(error),
            f"V3 scenario-family registry validation failed: {error}",
        ) from error


def assert_calibration_redesign_v3_schema_only_fixture_root(root: Path) -> None:
    """Fail closed when V3 case bytes or manifests appear before their authorised phase."""

    resolved_root = root.resolve()
    if not resolved_root.is_dir():
        raise CalibrationRedesignV3RegistryLoadError(
            CalibrationRedesignV3RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V3 fixture root must be an existing directory",
        )
    registry_path = resolved_root / _V3_REGISTRY_FILENAME
    if not registry_path.is_file():
        raise CalibrationRedesignV3RegistryLoadError(
            CalibrationRedesignV3RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V3 schema-only fixture root requires scenario_family_registry.json",
        )

    unexpected_paths = []
    for child in resolved_root.iterdir():
        if child.name in _FORBIDDEN_SCHEMA_ONLY_PATH_NAMES:
            unexpected_paths.append(child.name)
        elif child.is_dir():
            unexpected_paths.append(child.name)
        elif child.name not in _ALLOWED_SCHEMA_ONLY_FILENAMES:
            unexpected_paths.append(child.name)
    if unexpected_paths:
        rendered = ", ".join(sorted(unexpected_paths))
        raise CalibrationRedesignV3RegistryLoadError(
            CalibrationRedesignV3RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION,
            "V3 schema-only fixture root contains unauthorised assets: " + rendered,
        )


def _reject_closed_evidence_reference(raw_bytes: bytes) -> None:
    lowered = raw_bytes.lower()
    forbidden_markers = (
        b"crv1-",
        b"crv2-",
        b"bounded-platt-scaling-v1",
        b"logit-temperature-scaling-v1",
        b"heldout_assessment",
    )
    if any(marker in lowered for marker in forbidden_markers):
        raise CalibrationRedesignV3RegistryLoadError(
            CalibrationRedesignV3RegistryViolationCode.V1_OR_V2_EVIDENCE_REFERENCE,
            "V3 registry must not reference closed V1 or V2 data-bearing evidence",
        )


def _registry_violation_code(error: ValidationError) -> CalibrationRedesignV3RegistryViolationCode:
    rendered = str(error).lower()
    if "v1" in rendered or "v2" in rendered or "closed" in rendered:
        return CalibrationRedesignV3RegistryViolationCode.V1_OR_V2_EVIDENCE_REFERENCE
    return CalibrationRedesignV3RegistryViolationCode.REGISTRY_SCHEMA_ERROR
