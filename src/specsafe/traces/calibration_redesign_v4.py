"""Schema-only V4 evidence reservation controls.

This module reserves the fresh V4 namespace and evidence plan before a V4 runtime input,
expected outcome, manifest, calibration artifact, or policy implementation exists. It is not a
fixture loader and it must fail closed when any case-bearing path appears at this boundary.
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

_V4_REGISTRY_FILENAME = "scenario_family_registry.json"
_V4_SCHEMA_ONLY_ROOT_FILENAMES = {
    "PROPOSAL_MANIFEST.md",
    "authoring_ledger.md",
    _V4_REGISTRY_FILENAME,
}
_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}
_EXPECTED_FAMILY_IDS = {
    "CRV4-CAL-CURVE-COVERAGE",
    "CRV4-CAL-POSITION-SPREAD",
    "CRV4-CAL-WORKLOAD-MIX",
    "CRV4-CAL-CAPACITY-CONTRAST",
    "CRV4-FINAL-LIGHT-CAPACITY",
    "CRV4-FINAL-MODERATE-CAPACITY",
    "CRV4-FINAL-SATURATED-CAPACITY",
    "CRV4-FINAL-JAGGED-CAPACITY",
    "CRV4-ADV-CAUSAL-GUARD",
    "CRV4-ADV-PROVENANCE-GATE",
}
_EXPECTED_CASE_IDS_BY_FAMILY = {
    "CRV4-CAL-CURVE-COVERAGE": tuple(
        f"CRV4-{number:03d}" for number in range(101, 113)
    ),
    "CRV4-CAL-POSITION-SPREAD": tuple(
        f"CRV4-{number:03d}" for number in range(113, 125)
    ),
    "CRV4-CAL-WORKLOAD-MIX": tuple(f"CRV4-{number:03d}" for number in range(125, 137)),
    "CRV4-CAL-CAPACITY-CONTRAST": tuple(
        f"CRV4-{number:03d}" for number in range(137, 149)
    ),
    "CRV4-FINAL-LIGHT-CAPACITY": tuple(
        f"CRV4-{number:03d}" for number in range(201, 210)
    ),
    "CRV4-FINAL-MODERATE-CAPACITY": tuple(
        f"CRV4-{number:03d}" for number in range(210, 219)
    ),
    "CRV4-FINAL-SATURATED-CAPACITY": tuple(
        f"CRV4-{number:03d}" for number in range(219, 228)
    ),
    "CRV4-FINAL-JAGGED-CAPACITY": tuple(
        f"CRV4-{number:03d}" for number in range(228, 237)
    ),
    "CRV4-ADV-CAUSAL-GUARD": tuple(f"CRV4-{number:03d}" for number in range(301, 307)),
    "CRV4-ADV-PROVENANCE-GATE": tuple(
        f"CRV4-{number:03d}" for number in range(307, 313)
    ),
}
_CLOSED_EVIDENCE_MARKERS = (
    b"crv1-",
    b"crv2-",
    b"crv3-",
    b"bounded-platt-scaling-v1",
    b"logit-temperature-scaling-v1",
    b"quantile-isotonic-calibration-v1",
)


class CalibrationRedesignV4RegistryViolationCode(StrEnum):
    """Machine-readable failures for the V4 schema-only reservation boundary."""

    REGISTRY_SCHEMA_ERROR = "calibration_redesign_v4_registry_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = (
        "calibration_redesign_v4_registry_provenance_mismatch"
    )
    CLOSED_EVIDENCE_REFERENCE = "calibration_redesign_v4_closed_evidence_reference"
    SCHEMA_ONLY_BOUNDARY_VIOLATION = (
        "calibration_redesign_v4_schema_only_boundary_violation"
    )


class CalibrationRedesignV4RegistryLoadError(ValueError):
    """Raised when the V4 registry or schema-only root cannot be trusted."""

    def __init__(
        self,
        code: CalibrationRedesignV4RegistryViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV4ObservationBudget(StrictContract):
    """Fixed V4 split counts reserved before any V4 data is authored."""

    calibration_case_count: Literal[48]
    final_evaluation_case_count: Literal[36]
    adversarial_regression_case_count: Literal[12]
    candidate_positions_per_case: Literal[4]
    calibration_observation_count: Literal[192]
    final_evaluation_observation_count: Literal[144]
    adversarial_regression_observation_count: Literal[48]
    calibration_quantile_group_count: Literal[12]


class CalibrationRedesignV4WorkloadAllocation(StrictContract):
    """Required workload balance for each reserved V4 final capacity family."""

    structured_text_case_count: Literal[3]
    code_case_count: Literal[3]
    open_ended_chat_case_count: Literal[3]


class CalibrationRedesignV4ScenarioFamilyRecord(StrictContract):
    """One reserved V4 family without runtime or outcome assets."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    primary_data_role: TraceDataRole
    reserved_case_ids: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=500)
    target_failure_modes: tuple[str, ...] = Field(min_length=1)
    is_final_evaluation_quarantined: bool
    is_adversarial_regression_quarantined: bool
    workload_allocation: CalibrationRedesignV4WorkloadAllocation | None = None
    authoring_status: Literal["reserved_for_v4_case_authoring"]

    @field_validator("reserved_case_ids")
    @classmethod
    def validate_reserved_case_ids(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        """Reserve only fresh V4 identifiers and preserve deterministic family membership."""

        if len(set(case_ids)) != len(case_ids):
            raise ValueError("V4 case IDs must be unique within one family")
        if any(not case_id.startswith("CRV4-") for case_id in case_ids):
            raise ValueError("V4 case IDs must use the CRV4 namespace")
        return case_ids

    @field_validator("target_failure_modes")
    @classmethod
    def validate_target_failure_modes(
        cls,
        failure_modes: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Keep each family’s failure-purpose declaration unambiguous."""

        if len(set(failure_modes)) != len(failure_modes):
            raise ValueError("V4 target failure modes must be unique within one family")
        return failure_modes

    @model_validator(mode="after")
    def validate_family_governance(self) -> CalibrationRedesignV4ScenarioFamilyRecord:
        """Bind split, role, quarantine state, and workload allocation together."""

        if not self.scenario_family_id.startswith("CRV4-"):
            raise ValueError("V4 scenario-family IDs must use the CRV4 namespace")
        expected_role = _EXPECTED_DATA_ROLE_BY_SPLIT.get(self.split)
        if expected_role is None or self.primary_data_role is not expected_role:
            raise ValueError("primary_data_role must match the governed V4 split role")

        final_quarantine_expected = self.split is TraceSplit.FINAL_EVALUATION
        adversarial_quarantine_expected = (
            self.split is TraceSplit.ADVERSARIAL_REGRESSION
        )
        if self.is_final_evaluation_quarantined is not final_quarantine_expected:
            raise ValueError(
                "final-evaluation quarantine must match the declared V4 split"
            )
        if (
            self.is_adversarial_regression_quarantined
            is not adversarial_quarantine_expected
        ):
            raise ValueError(
                "adversarial-regression quarantine must match the declared V4 split"
            )
        if final_quarantine_expected != (self.workload_allocation is not None):
            raise ValueError(
                "only V4 final-evaluation families may declare workload allocation"
            )
        return self


class CalibrationRedesignV4ScenarioFamilyRegistry(StrictContract):
    """Schema-only V4 registry: complete reservation, zero case-bearing assets."""

    schema_version: Literal["calibration-redesign-v4-scenario-family-registry-v1"]
    registry_status: Literal["schema_only"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    method_constitution_version: Literal["v4-method-and-evidence-constitution-v1"]
    calibration_method_id: Literal["regularized-isotonic-calibration-v4"]
    adaptive_policy_id: Literal["causal-calibrated-prefix-utility-v4"]
    maximum_candidate_positions: Literal[4]
    v1_v2_v3_data_bearing_evidence_used: Literal[False]
    v4_runtime_or_outcome_assets_authored: Literal[False]
    v4_manifests_authored: Literal[False]
    v4_final_assessment_contract_merged: Literal[True]
    observation_budget: CalibrationRedesignV4ObservationBudget
    families: tuple[CalibrationRedesignV4ScenarioFamilyRecord, ...] = Field(
        min_length=10,
        max_length=10,
    )
    explicit_exclusions: tuple[str, ...] = Field(min_length=10)
    next_authorized_artifact: Literal["v4-calibration-curve-coverage-fixtures"]

    @model_validator(mode="after")
    def validate_registry_governance(
        self,
    ) -> CalibrationRedesignV4ScenarioFamilyRegistry:
        """Enforce V4’s fresh, exact, no-case-bytes reservation plan."""

        if self.v1_v2_v3_data_bearing_evidence_used:
            raise ValueError(
                "closed-programme data-bearing evidence is prohibited in V4"
            )
        if self.v4_runtime_or_outcome_assets_authored:
            raise ValueError(
                "schema-only V4 registry cannot record authored case assets"
            )
        if self.v4_manifests_authored:
            raise ValueError("schema-only V4 registry cannot record authored manifests")

        family_ids = tuple(family.scenario_family_id for family in self.families)
        if len(set(family_ids)) != len(family_ids):
            raise ValueError("V4 scenario-family IDs must be unique")
        if set(family_ids) != _EXPECTED_FAMILY_IDS:
            raise ValueError(
                "V4 scenario-family IDs must match the complete reserved plan"
            )

        all_case_ids = tuple(
            case_id for family in self.families for case_id in family.reserved_case_ids
        )
        if len(set(all_case_ids)) != len(all_case_ids):
            raise ValueError("V4 case IDs must be unique across all families")
        for family in self.families:
            if (
                family.reserved_case_ids
                != _EXPECTED_CASE_IDS_BY_FAMILY[family.scenario_family_id]
            ):
                raise ValueError(
                    "V4 family case IDs must match the fixed reservation ranges exactly"
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
            raise ValueError("V4 calibration reserved-case count must equal 48")
        if split_case_counts[TraceSplit.FINAL_EVALUATION] != 36:
            raise ValueError("V4 final-evaluation reserved-case count must equal 36")
        if split_case_counts[TraceSplit.ADVERSARIAL_REGRESSION] != 12:
            raise ValueError("V4 adversarial reserved-case count must equal 12")

        final_families = tuple(
            family
            for family in self.families
            if family.split is TraceSplit.FINAL_EVALUATION
        )
        if len(final_families) != 4 or any(
            len(family.reserved_case_ids) != 9 for family in final_families
        ):
            raise ValueError(
                "each V4 final capacity family must reserve exactly nine cases"
            )
        if any(family.workload_allocation is None for family in final_families):
            raise ValueError(
                "each V4 final family requires the fixed workload allocation"
            )

        required_exclusions = {
            "No V4 runtime-input case assets are present.",
            "No V4 expected-outcome case assets or labels are present.",
            "No V4 calibration or final-evaluation manifest is present.",
            "No V4 calibration artifact or fit report is present.",
            "No V4 final-evidence index or held-out result is present.",
            "No V4 calibrator fitting is authorized by this reservation registry.",
            "No V4 scheduler, baseline, capacity, or replay implementation is authorized.",
            "No closed-programme data-bearing evidence influenced V4 case design.",
            "No V4 performance, calibration, policy, or runtime claim is made.",
            "No V4 adversarial-regression case assets are present.",
        }
        if not required_exclusions.issubset(set(self.explicit_exclusions)):
            raise ValueError("V4 registry must retain every schema-only exclusion")
        return self


def load_calibration_redesign_v4_scenario_family_registry(
    path: Path,
) -> CalibrationRedesignV4ScenarioFamilyRegistry:
    """Load the V4 registry only when the fixture root is still schema-only."""

    root = path.parent.resolve()
    assert_calibration_redesign_v4_schema_only_fixture_root(root)
    if path.resolve() != root / _V4_REGISTRY_FILENAME:
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 registry must be loaded from scenario_family_registry.json at its fixture root",
        )
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            f"unable to read V4 scenario-family registry: {error}",
        ) from error

    _reject_closed_evidence_reference(raw_bytes)
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_SCHEMA_ERROR,
            f"V4 scenario-family registry is not valid UTF-8 JSON: {error}",
        ) from error
    try:
        return CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_SCHEMA_ERROR,
            f"V4 scenario-family registry validation failed: {error}",
        ) from error


def assert_calibration_redesign_v4_schema_only_fixture_root(root: Path) -> None:
    """Reject case-bearing files, directories, manifests, and closed-evidence references."""

    resolved_root = _require_fixture_root(root)
    observed_names = {child.name for child in resolved_root.iterdir()}
    if observed_names != _V4_SCHEMA_ONLY_ROOT_FILENAMES:
        unexpected = ", ".join(sorted(observed_names ^ _V4_SCHEMA_ONLY_ROOT_FILENAMES))
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION,
            "V4 schema-only fixture root must contain only reservation metadata; mismatch: "
            + unexpected,
        )
    for child in resolved_root.iterdir():
        if not child.is_file():
            raise CalibrationRedesignV4RegistryLoadError(
                CalibrationRedesignV4RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION,
                "V4 schema-only fixture root may not contain directories",
            )
        try:
            _reject_closed_evidence_reference(child.read_bytes())
        except OSError as error:
            raise CalibrationRedesignV4RegistryLoadError(
                CalibrationRedesignV4RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
                f"unable to inspect V4 schema-only root asset {child.name}: {error}",
            ) from error


def _require_fixture_root(root: Path) -> Path:
    resolved_root = root.resolve()
    if not resolved_root.is_dir():
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 fixture root must be an existing directory",
        )
    if not (resolved_root / _V4_REGISTRY_FILENAME).is_file():
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 fixture root requires scenario_family_registry.json",
        )
    return resolved_root


def _reject_closed_evidence_reference(raw_bytes: bytes) -> None:
    lowered = raw_bytes.lower()
    if any(marker in lowered for marker in _CLOSED_EVIDENCE_MARKERS):
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.CLOSED_EVIDENCE_REFERENCE,
            "V4 reservation assets must not reference closed-programme data-bearing evidence",
        )
