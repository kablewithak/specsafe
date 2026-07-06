"""Governed V4 calibration capacity-contrast evidence controls.

This module completes the four authorised V4 calibration-only families: curve coverage
(CRV4-101..112), position spread (CRV4-113..124), workload mix (CRV4-125..136), and
capacity contrast (CRV4-137..148). Final evaluation and adversarial evidence remain
absent. This module does not fit calibration, create a manifest, or execute a policy.
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
_V4_PROPOSAL_MANIFEST_FILENAME = "PROPOSAL_MANIFEST.md"
_V4_AUTHORING_LEDGER_FILENAME = "authoring_ledger.md"

_V4_CALIBRATION_CURVE_COVERAGE_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(101, 113))
_V4_CALIBRATION_POSITION_SPREAD_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(113, 125))
_V4_CALIBRATION_WORKLOAD_MIX_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(125, 137))
_V4_CALIBRATION_CAPACITY_CONTRAST_CASE_IDS = tuple(
    f"CRV4-{number:03d}" for number in range(137, 149)
)
_V4_AUTHORISED_WORKLOAD_MIX_CASE_IDS = (
    *_V4_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
    *_V4_CALIBRATION_POSITION_SPREAD_CASE_IDS,
    *_V4_CALIBRATION_WORKLOAD_MIX_CASE_IDS,
)
_V4_AUTHORISED_CALIBRATION_CASE_IDS = (
    *_V4_AUTHORISED_WORKLOAD_MIX_CASE_IDS,
    *_V4_CALIBRATION_CAPACITY_CONTRAST_CASE_IDS,
)
_V4_EXPECTED_CASE_IDS_BY_FAMILY = {
    "CRV4-CAL-CURVE-COVERAGE": _V4_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
    "CRV4-CAL-POSITION-SPREAD": _V4_CALIBRATION_POSITION_SPREAD_CASE_IDS,
    "CRV4-CAL-WORKLOAD-MIX": _V4_CALIBRATION_WORKLOAD_MIX_CASE_IDS,
    "CRV4-CAL-CAPACITY-CONTRAST": _V4_CALIBRATION_CAPACITY_CONTRAST_CASE_IDS,
    "CRV4-FINAL-LIGHT-CAPACITY": tuple(f"CRV4-{number:03d}" for number in range(201, 210)),
    "CRV4-FINAL-MODERATE-CAPACITY": tuple(f"CRV4-{number:03d}" for number in range(210, 219)),
    "CRV4-FINAL-SATURATED-CAPACITY": tuple(f"CRV4-{number:03d}" for number in range(219, 228)),
    "CRV4-FINAL-JAGGED-CAPACITY": tuple(f"CRV4-{number:03d}" for number in range(228, 237)),
    "CRV4-ADV-CAUSAL-GUARD": tuple(f"CRV4-{number:03d}" for number in range(301, 307)),
    "CRV4-ADV-PROVENANCE-GATE": tuple(f"CRV4-{number:03d}" for number in range(307, 313)),
}
_V4_EXPECTED_FAMILY_IDS = frozenset(_V4_EXPECTED_CASE_IDS_BY_FAMILY)
_V4_SCHEMA_ONLY_ROOT_FILENAMES = {
    _V4_PROPOSAL_MANIFEST_FILENAME,
    _V4_AUTHORING_LEDGER_FILENAME,
    _V4_REGISTRY_FILENAME,
}
_V4_ALLOWED_CALIBRATION_DIRECTORIES = {"inputs", "expected_outcomes"}
_V4_FORBIDDEN_ROOT_PATH_NAMES = {
    "calibration_manifest.json",
    "final_evaluation_manifest.json",
    "final_evidence_index.json",
    "adversarial_regression_manifest.json",
    "artifact.json",
    "fit_report.json",
    "heldout_assessment.json",
    "result.json",
    "final_evaluation",
    "adversarial_regression",
}
_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}
_CLOSED_EVIDENCE_MARKERS = (
    b"crv1-",
    b"crv2-",
    b"crv3-",
    b"bounded-platt-scaling-v1",
    b"logit-temperature-scaling-v1",
    b"quantile-isotonic-calibration-v1",
)
_EXPECTED_AUTHORED_STATUS_BY_FAMILY = {
    "CRV4-CAL-CURVE-COVERAGE": "calibration_curve_coverage_authored",
    "CRV4-CAL-POSITION-SPREAD": "calibration_position_spread_authored",
    "CRV4-CAL-WORKLOAD-MIX": "calibration_workload_mix_authored",
    "CRV4-CAL-CAPACITY-CONTRAST": "calibration_capacity_contrast_authored",
}


class CalibrationRedesignV4RegistryViolationCode(StrEnum):
    """Machine-readable failures for V4 authoring-boundary checks."""

    REGISTRY_SCHEMA_ERROR = "calibration_redesign_v4_registry_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = "calibration_redesign_v4_registry_provenance_mismatch"
    CLOSED_EVIDENCE_REFERENCE = "calibration_redesign_v4_closed_evidence_reference"
    SCHEMA_ONLY_BOUNDARY_VIOLATION = "calibration_redesign_v4_schema_only_boundary_violation"
    CALIBRATION_CURVE_COVERAGE_BOUNDARY_VIOLATION = (
        "calibration_redesign_v4_calibration_curve_coverage_boundary_violation"
    )
    CALIBRATION_POSITION_SPREAD_BOUNDARY_VIOLATION = (
        "calibration_redesign_v4_calibration_position_spread_boundary_violation"
    )
    CALIBRATION_WORKLOAD_MIX_BOUNDARY_VIOLATION = (
        "calibration_redesign_v4_calibration_workload_mix_boundary_violation"
    )
    CALIBRATION_CAPACITY_CONTRAST_BOUNDARY_VIOLATION = (
        "calibration_redesign_v4_calibration_capacity_contrast_boundary_violation"
    )


class CalibrationRedesignV4RegistryLoadError(ValueError):
    """Raised when V4 registry metadata or its active authoring root is invalid."""

    def __init__(
        self,
        code: CalibrationRedesignV4RegistryViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV4ObservationBudget(StrictContract):
    """Fixed V4 evidence counts before later authoring stages begin."""

    calibration_case_count: Literal[48]
    final_evaluation_case_count: Literal[36]
    adversarial_regression_case_count: Literal[12]
    candidate_positions_per_case: Literal[4]
    calibration_observation_count: Literal[192]
    final_evaluation_observation_count: Literal[144]
    adversarial_regression_observation_count: Literal[48]
    calibration_quantile_group_count: Literal[12]


class CalibrationRedesignV4WorkloadAllocation(StrictContract):
    """Fixed workload balance for each quarantined V4 final family."""

    structured_text_case_count: Literal[3]
    code_case_count: Literal[3]
    open_ended_chat_case_count: Literal[3]


class CalibrationRedesignV4ScenarioFamilyRecord(StrictContract):
    """One V4 evidence family with explicit stage and quarantine boundaries."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    primary_data_role: TraceDataRole
    reserved_case_ids: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=500)
    target_failure_modes: tuple[str, ...] = Field(min_length=1)
    is_final_evaluation_quarantined: bool
    is_adversarial_regression_quarantined: bool
    workload_allocation: CalibrationRedesignV4WorkloadAllocation | None = None
    authoring_status: Literal[
        "calibration_curve_coverage_authored",
        "calibration_position_spread_authored",
        "calibration_workload_mix_authored",
        "calibration_capacity_contrast_authored",
        "reserved_for_v4_case_authoring",
    ]

    @field_validator("reserved_case_ids")
    @classmethod
    def validate_reserved_case_ids(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        """Keep fresh V4 case reservations unique inside each family."""

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
        if len(set(failure_modes)) != len(failure_modes):
            raise ValueError("V4 target failure modes must be unique within one family")
        return failure_modes

    @model_validator(mode="after")
    def validate_family_governance(self) -> CalibrationRedesignV4ScenarioFamilyRecord:
        """Bind role, quarantine, workload allocation, and authoring stage."""

        if not self.scenario_family_id.startswith("CRV4-"):
            raise ValueError("V4 scenario-family IDs must use the CRV4 namespace")
        expected_role = _EXPECTED_DATA_ROLE_BY_SPLIT.get(self.split)
        if expected_role is None or self.primary_data_role is not expected_role:
            raise ValueError("primary_data_role must match the governed V4 split role")

        final_quarantine_expected = self.split is TraceSplit.FINAL_EVALUATION
        adversarial_quarantine_expected = self.split is TraceSplit.ADVERSARIAL_REGRESSION
        if self.is_final_evaluation_quarantined is not final_quarantine_expected:
            raise ValueError("final-evaluation quarantine must match the declared V4 split")
        if self.is_adversarial_regression_quarantined is not adversarial_quarantine_expected:
            raise ValueError("adversarial-regression quarantine must match the declared V4 split")
        if final_quarantine_expected != (self.workload_allocation is not None):
            raise ValueError("only V4 final-evaluation families may declare workload allocation")

        expected_status = _EXPECTED_AUTHORED_STATUS_BY_FAMILY.get(
            self.scenario_family_id,
            "reserved_for_v4_case_authoring",
        )
        if self.authoring_status != expected_status:
            raise ValueError(
                "V4 family authoring status does not match the active authoring boundary"
            )
        return self


class CalibrationRedesignV4ScenarioFamilyRegistry(StrictContract):
    """V4 registry after all four calibration-only families have been authored."""

    schema_version: Literal["calibration-redesign-v4-scenario-family-registry-v1"]
    registry_status: Literal["calibration_capacity_contrast_authored"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    method_constitution_version: Literal["v4-method-and-evidence-constitution-v1"]
    calibration_method_id: Literal["regularized-isotonic-calibration-v4"]
    adaptive_policy_id: Literal["causal-calibrated-prefix-utility-v4"]
    maximum_candidate_positions: Literal[4]
    v1_v2_v3_data_bearing_evidence_used: Literal[False]
    v4_runtime_or_outcome_assets_authored: Literal[True]
    v4_manifests_authored: Literal[False]
    v4_final_assessment_contract_merged: Literal[True]
    observation_budget: CalibrationRedesignV4ObservationBudget
    families: tuple[CalibrationRedesignV4ScenarioFamilyRecord, ...] = Field(
        min_length=10,
        max_length=10,
    )
    explicit_exclusions: tuple[str, ...] = Field(min_length=9)
    next_authorized_artifact: Literal["v4-calibration-manifest-freeze"]

    @model_validator(mode="after")
    def validate_registry_governance(
        self,
    ) -> CalibrationRedesignV4ScenarioFamilyRegistry:
        """Enforce exact V4 reservation plus all four authored calibration families."""

        if self.v1_v2_v3_data_bearing_evidence_used:
            raise ValueError("closed-programme data-bearing evidence is prohibited in V4")
        if not self.v4_runtime_or_outcome_assets_authored:
            raise ValueError(
                "the V4 capacity-contrast authoring stage requires authored calibration assets"
            )
        if self.v4_manifests_authored:
            raise ValueError(
                "V4 capacity-contrast authoring stage cannot record authored manifests"
            )

        family_ids = tuple(family.scenario_family_id for family in self.families)
        if len(set(family_ids)) != len(family_ids):
            raise ValueError("V4 scenario-family IDs must be unique")
        if set(family_ids) != _V4_EXPECTED_FAMILY_IDS:
            raise ValueError("V4 scenario-family IDs must match the complete reserved plan")

        all_case_ids = tuple(
            case_id for family in self.families for case_id in family.reserved_case_ids
        )
        if len(set(all_case_ids)) != len(all_case_ids):
            raise ValueError("V4 case IDs must be unique across all families")
        for family in self.families:
            if (
                family.reserved_case_ids
                != _V4_EXPECTED_CASE_IDS_BY_FAMILY[family.scenario_family_id]
            ):
                raise ValueError(
                    "V4 family case IDs must match the fixed reservation ranges exactly"
                )

        split_case_counts = {
            split: sum(
                len(family.reserved_case_ids) for family in self.families if family.split is split
            )
            for split in _EXPECTED_DATA_ROLE_BY_SPLIT
        }
        if split_case_counts[TraceSplit.CALIBRATION] != 48:
            raise ValueError("V4 calibration reserved-case count must equal 48")
        if split_case_counts[TraceSplit.FINAL_EVALUATION] != 36:
            raise ValueError("V4 final-evaluation reserved-case count must equal 36")
        if split_case_counts[TraceSplit.ADVERSARIAL_REGRESSION] != 12:
            raise ValueError("V4 adversarial reserved-case count must equal 12")

        for family_id, expected_status in _EXPECTED_AUTHORED_STATUS_BY_FAMILY.items():
            family = next(item for item in self.families if item.scenario_family_id == family_id)
            if family.authoring_status != expected_status:
                raise ValueError(f"V4 {family_id} must remain marked {expected_status}")

        final_families = tuple(
            family for family in self.families if family.split is TraceSplit.FINAL_EVALUATION
        )
        if len(final_families) != 4 or any(
            len(family.reserved_case_ids) != 9 for family in final_families
        ):
            raise ValueError("each V4 final capacity family must reserve exactly nine cases")
        if any(family.workload_allocation is None for family in final_families):
            raise ValueError("each V4 final family requires the fixed workload allocation")

        required_exclusions = {
            "No V4 final-evaluation runtime-input case assets are present.",
            "No V4 final-evaluation expected-outcome assets or labels are present.",
            "No V4 adversarial-regression runtime-input or expected-outcome assets are present.",
            "No V4 calibration or final-evaluation manifest is present.",
            "No V4 calibration artifact or fit report is present.",
            "No V4 final-evidence index or held-out result is present.",
            "No V4 calibrator fitting is authorized by this registry.",
            "No V4 scheduler, baseline, capacity, or replay implementation is authorized.",
            "No closed-programme data-bearing evidence influenced V4 case design.",
            "No V4 performance, calibration, policy, or runtime claim is made.",
        }
        if not required_exclusions.issubset(set(self.explicit_exclusions)):
            raise ValueError("V4 registry must retain every capacity-contrast-stage exclusion")
        return self


def load_calibration_redesign_v4_scenario_family_registry(
    path: Path,
    *,
    allow_calibration_curve_coverage_assets: bool = False,
    allow_calibration_position_spread_assets: bool = False,
    allow_calibration_workload_mix_assets: bool = False,
    allow_calibration_capacity_contrast_assets: bool = False,
) -> CalibrationRedesignV4ScenarioFamilyRegistry:
    """Load V4 registry only through one explicit, governed authoring boundary."""

    selected_boundary_count = sum(
        (
            allow_calibration_curve_coverage_assets,
            allow_calibration_position_spread_assets,
            allow_calibration_workload_mix_assets,
            allow_calibration_capacity_contrast_assets,
        )
    )
    if selected_boundary_count > 1:
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 registry loading must select exactly one authored calibration boundary",
        )

    root = path.parent.resolve()
    if allow_calibration_capacity_contrast_assets:
        assert_calibration_redesign_v4_calibration_capacity_contrast_fixture_root(root)
    elif allow_calibration_workload_mix_assets:
        assert_calibration_redesign_v4_calibration_workload_mix_fixture_root(root)
    elif allow_calibration_position_spread_assets:
        assert_calibration_redesign_v4_calibration_position_spread_fixture_root(root)
    elif allow_calibration_curve_coverage_assets:
        assert_calibration_redesign_v4_calibration_curve_coverage_fixture_root(root)
    else:
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
    """Fail closed when case-bearing paths appear before a stage is selected."""

    resolved_root = _require_fixture_root(root)
    unexpected_paths = []
    for child in resolved_root.iterdir():
        if child.name in _V4_FORBIDDEN_ROOT_PATH_NAMES or child.is_dir():
            unexpected_paths.append(child.name)
        elif child.name not in _V4_SCHEMA_ONLY_ROOT_FILENAMES:
            unexpected_paths.append(child.name)
    if unexpected_paths:
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION,
            "V4 schema-only fixture root contains unauthorised assets: "
            + ", ".join(sorted(unexpected_paths)),
        )
    _reject_closed_references_in_root_metadata(resolved_root)


def assert_calibration_redesign_v4_calibration_curve_coverage_fixture_root(
    root: Path,
) -> None:
    """Validate exactly the first twelve V4 calibration case pairs."""

    _assert_v4_calibration_fixture_root(
        root,
        expected_case_ids=_V4_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
        violation_code=(
            CalibrationRedesignV4RegistryViolationCode.CALIBRATION_CURVE_COVERAGE_BOUNDARY_VIOLATION
        ),
        boundary_name="curve-coverage",
    )


def assert_calibration_redesign_v4_calibration_position_spread_fixture_root(
    root: Path,
) -> None:
    """Validate the first twenty-four V4 calibration case pairs."""

    _assert_v4_calibration_fixture_root(
        root,
        expected_case_ids=(
            *_V4_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
            *_V4_CALIBRATION_POSITION_SPREAD_CASE_IDS,
        ),
        violation_code=(
            CalibrationRedesignV4RegistryViolationCode.CALIBRATION_POSITION_SPREAD_BOUNDARY_VIOLATION
        ),
        boundary_name="position-spread",
    )


def assert_calibration_redesign_v4_calibration_workload_mix_fixture_root(
    root: Path,
) -> None:
    """Validate exactly the first thirty-six V4 calibration case pairs."""

    _assert_v4_calibration_fixture_root(
        root,
        expected_case_ids=_V4_AUTHORISED_WORKLOAD_MIX_CASE_IDS,
        violation_code=(
            CalibrationRedesignV4RegistryViolationCode.CALIBRATION_WORKLOAD_MIX_BOUNDARY_VIOLATION
        ),
        boundary_name="workload-mix",
    )


def assert_calibration_redesign_v4_calibration_capacity_contrast_fixture_root(
    root: Path,
) -> None:
    """Validate the complete forty-eight-case V4 calibration corpus."""

    _assert_v4_calibration_fixture_root(
        root,
        expected_case_ids=_V4_AUTHORISED_CALIBRATION_CASE_IDS,
        violation_code=(
            CalibrationRedesignV4RegistryViolationCode.CALIBRATION_CAPACITY_CONTRAST_BOUNDARY_VIOLATION
        ),
        boundary_name="capacity-contrast",
    )


def _assert_v4_calibration_fixture_root(
    root: Path,
    *,
    expected_case_ids: tuple[str, ...],
    violation_code: CalibrationRedesignV4RegistryViolationCode,
    boundary_name: str,
) -> None:
    resolved_root = _require_fixture_root(root)
    unexpected_root_paths = []
    for child in resolved_root.iterdir():
        if child.name in _V4_FORBIDDEN_ROOT_PATH_NAMES:
            unexpected_root_paths.append(child.name)
        elif child.is_dir() and child.name not in _V4_ALLOWED_CALIBRATION_DIRECTORIES:
            unexpected_root_paths.append(child.name)
        elif not child.is_dir() and child.name not in _V4_SCHEMA_ONLY_ROOT_FILENAMES:
            unexpected_root_paths.append(child.name)
    if unexpected_root_paths:
        raise CalibrationRedesignV4RegistryLoadError(
            violation_code,
            f"V4 {boundary_name} fixture root contains unauthorised assets: "
            + ", ".join(sorted(unexpected_root_paths)),
        )

    expected_names = {f"{case_id}.json" for case_id in expected_case_ids}
    for artifact_directory in sorted(_V4_ALLOWED_CALIBRATION_DIRECTORIES):
        cases_path = resolved_root / artifact_directory / "cases"
        if not cases_path.is_dir():
            raise CalibrationRedesignV4RegistryLoadError(
                violation_code,
                f"V4 {boundary_name} root requires {artifact_directory}/cases",
            )
        names = {path.name for path in cases_path.iterdir()}
        if names != expected_names:
            raise CalibrationRedesignV4RegistryLoadError(
                violation_code,
                f"V4 {artifact_directory}/cases must contain exactly "
                f"{expected_case_ids[0]} through {expected_case_ids[-1]}",
            )
        for asset_path in cases_path.iterdir():
            if not asset_path.is_file() or asset_path.suffix != ".json":
                raise CalibrationRedesignV4RegistryLoadError(
                    violation_code,
                    f"V4 {artifact_directory}/cases may contain only JSON case files",
                )
            _reject_closed_evidence_reference(asset_path.read_bytes())
        _reject_nested_or_sibling_assets(
            resolved_root / artifact_directory,
            allowed_child_name="cases",
            violation_code=violation_code,
        )
    _reject_closed_references_in_root_metadata(resolved_root)


def _require_fixture_root(root: Path) -> Path:
    resolved_root = root.resolve()
    if not resolved_root.is_dir():
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 fixture root must be an existing directory",
        )
    registry_path = resolved_root / _V4_REGISTRY_FILENAME
    if not registry_path.is_file():
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 fixture root requires scenario_family_registry.json",
        )
    return resolved_root


def _reject_nested_or_sibling_assets(
    parent: Path,
    *,
    allowed_child_name: str,
    violation_code: CalibrationRedesignV4RegistryViolationCode,
) -> None:
    child_names = {child.name for child in parent.iterdir()}
    if child_names != {allowed_child_name}:
        raise CalibrationRedesignV4RegistryLoadError(
            violation_code,
            f"V4 {parent.name} directory may contain only {allowed_child_name}",
        )


def _reject_closed_references_in_root_metadata(root: Path) -> None:
    for filename in _V4_SCHEMA_ONLY_ROOT_FILENAMES:
        path = root / filename
        if path.is_file():
            _reject_closed_evidence_reference(path.read_bytes())


def _reject_closed_evidence_reference(raw_bytes: bytes) -> None:
    lowered = raw_bytes.lower()
    if any(marker in lowered for marker in _CLOSED_EVIDENCE_MARKERS):
        raise CalibrationRedesignV4RegistryLoadError(
            CalibrationRedesignV4RegistryViolationCode.CLOSED_EVIDENCE_REFERENCE,
            "V4 assets must not reference closed-programme data-bearing evidence",
        )
