"""Strict proposal-only contracts for the V2 calibration-redesign evidence boundary.

This module validates reserved V2 scenario-family metadata before any V2 runtime input,
expected outcome, manifest, fitting, or assessment asset exists. It must not import or read
V1 data-bearing evidence.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from specsafe.contracts.models import (
    StrictContract,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
)

_V2_PROPOSAL_FILENAME = "scenario_family_registry_proposal.json"

_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.DEVELOPMENT: TraceDataRole.SYNTHETIC_FIXTURE,
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}


class CalibrationRedesignV2ProposalViolationCode(StrEnum):
    """Machine-readable reasons V2 planning evidence cannot cross its boundary."""

    PROPOSAL_SCHEMA_ERROR = "calibration_redesign_v2_proposal_schema_error"
    PROPOSAL_PROVENANCE_MISMATCH = (
        "calibration_redesign_v2_proposal_provenance_mismatch"
    )
    V1_EVIDENCE_REFERENCE = "calibration_redesign_v2_v1_evidence_reference"
    PROPOSAL_ONLY_BOUNDARY_VIOLATION = (
        "calibration_redesign_v2_proposal_only_boundary_violation"
    )


class CalibrationRedesignV2ProposalLoadError(ValueError):
    """Typed error raised when V2 proposal metadata is unsafe or incomplete."""

    def __init__(
        self,
        code: CalibrationRedesignV2ProposalViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV2ObservationBudget(StrictContract):
    """Predeclared minimum observation budget without encoding any fixture values."""

    minimum_observations_per_reserved_calibration_case: int = Field(ge=1)
    minimum_observations_per_reserved_final_evaluation_case: int = Field(ge=1)
    minimum_calibration_observation_count: int = Field(ge=1)
    minimum_final_evaluation_observation_count: int = Field(ge=1)


class CalibrationRedesignV2ScenarioFamilyProposal(StrictContract):
    """One V2 scenario family reserved before runtime or outcome authoring begins."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    primary_data_role: TraceDataRole
    parent_scenario_family_id: None = None
    source_template_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    reserved_case_ids: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=500)
    target_failure_modes: tuple[str, ...] = Field(min_length=1)
    is_final_evaluation_quarantined: bool
    authoring_status: Literal["proposed"]

    @field_validator("reserved_case_ids")
    @classmethod
    def validate_reserved_case_ids(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        """Require unique V2-only case identifiers before any case asset exists."""

        if len(set(case_ids)) != len(case_ids):
            raise ValueError("reserved case IDs must be unique within one V2 family")
        for case_id in case_ids:
            if case_id.startswith(("CRV1-", "STF-")):
                raise ValueError("V1 data-bearing case references are prohibited in V2")
            if (
                not case_id.startswith("CRV2-")
                or len(case_id) != 8
                or not case_id.removeprefix("CRV2-").isdigit()
            ):
                raise ValueError("reserved case IDs must use the CRV2-### namespace")
        return case_ids

    @field_validator("target_failure_modes")
    @classmethod
    def validate_target_failure_modes(
        cls,
        target_failure_modes: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Prevent duplicate diagnostics from being presented as additional coverage."""

        if len(set(target_failure_modes)) != len(target_failure_modes):
            raise ValueError("target failure modes must be unique within one V2 family")
        return target_failure_modes

    @model_validator(mode="after")
    def validate_v2_family_governance(
        self,
    ) -> CalibrationRedesignV2ScenarioFamilyProposal:
        """Bind each reserved family to its V2 split and quarantine role."""

        if self.scenario_family_id.startswith("CRV1-"):
            raise ValueError("V1 data-bearing family references are prohibited in V2")
        if not self.scenario_family_id.startswith("CRV2-"):
            raise ValueError("V2 scenario-family IDs must use the CRV2 namespace")
        expected_role = _EXPECTED_DATA_ROLE_BY_SPLIT[self.split]
        if self.primary_data_role is not expected_role:
            raise ValueError("primary_data_role must match the governed V2 split role")
        expected_quarantine = self.split is TraceSplit.FINAL_EVALUATION
        if self.is_final_evaluation_quarantined is not expected_quarantine:
            raise ValueError(
                "final-evaluation quarantine must match the declared V2 split"
            )
        return self


class CalibrationRedesignV2ScenarioFamilyRegistryProposal(StrictContract):
    """Strict planning contract for V2 registry metadata before fixture authoring."""

    schema_version: Literal["v2-scenario-family-registry-proposal-v1"]
    proposal_status: Literal["accepted_for_contract_enforcement"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v2"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    authoring_protocol_version: Literal["calibration-redesign-v2-entry-protocol-v1"]
    candidate_artifact_id: Literal["bounded-platt-scaling-v1"]
    v1_data_bearing_evidence_used: Literal[False]
    v2_runtime_or_outcome_assets_authored: Literal[False]
    observation_budget: CalibrationRedesignV2ObservationBudget
    families: tuple[CalibrationRedesignV2ScenarioFamilyProposal, ...] = Field(
        min_length=1
    )
    explicit_exclusions: tuple[str, ...] = Field(min_length=5)
    next_authorized_artifact: Literal[
        "v2-controlled-registry-finalization-and-case-contracts"
    ]

    @model_validator(mode="after")
    def validate_proposal_only_governance(
        self,
    ) -> CalibrationRedesignV2ScenarioFamilyRegistryProposal:
        """Enforce V2 planning floors without accepting runtime or outcome evidence."""

        if self.source_type is not TraceSourceType.SYNTHETIC:
            raise ValueError("V2 proposal source_type must be synthetic")
        if self.v1_data_bearing_evidence_used:
            raise ValueError("V1 data-bearing evidence is prohibited in V2")
        if self.v2_runtime_or_outcome_assets_authored:
            raise ValueError(
                "V2 runtime or outcome assets are prohibited in this proposal"
            )

        required_exclusions = {
            "No runtime-input fixture bytes are present.",
            "No expected-outcome assets or labels are present.",
        }
        if not required_exclusions.issubset(self.explicit_exclusions):
            raise ValueError(
                "V2 proposal must explicitly exclude runtime and outcome assets"
            )

        family_ids = [family.scenario_family_id for family in self.families]
        if len(set(family_ids)) != len(family_ids):
            raise ValueError("V2 scenario-family IDs must be unique")

        fingerprints = [family.source_template_fingerprint for family in self.families]
        if len(set(fingerprints)) != len(fingerprints):
            raise ValueError("V2 source-template fingerprints must be globally unique")

        case_ids: set[str] = set()
        families_by_split: dict[
            TraceSplit, list[CalibrationRedesignV2ScenarioFamilyProposal]
        ] = {split: [] for split in TraceSplit}
        for family in self.families:
            families_by_split[family.split].append(family)
            for case_id in family.reserved_case_ids:
                if case_id in case_ids:
                    raise ValueError(
                        "V2 reserved case IDs must not repeat across families"
                    )
                case_ids.add(case_id)

        calibration_families = families_by_split[TraceSplit.CALIBRATION]
        final_families = families_by_split[TraceSplit.FINAL_EVALUATION]
        development_families = families_by_split[TraceSplit.DEVELOPMENT]
        adversarial_families = families_by_split[TraceSplit.ADVERSARIAL_REGRESSION]

        if len(calibration_families) < 3:
            raise ValueError("V2 proposal requires at least three calibration families")
        if any(len(family.reserved_case_ids) < 4 for family in calibration_families):
            raise ValueError(
                "each V2 calibration family requires at least four reserved cases"
            )
        if len(final_families) < 3:
            raise ValueError(
                "V2 proposal requires at least three final-evaluation families"
            )
        if any(len(family.reserved_case_ids) < 3 for family in final_families):
            raise ValueError(
                "each V2 final-evaluation family requires at least three reserved cases"
            )
        if sum(len(family.reserved_case_ids) for family in development_families) < 2:
            raise ValueError("V2 proposal requires at least two development cases")
        if not adversarial_families:
            raise ValueError("V2 proposal requires an adversarial-regression family")

        calibration_case_count = sum(
            len(family.reserved_case_ids) for family in calibration_families
        )
        final_case_count = sum(
            len(family.reserved_case_ids) for family in final_families
        )
        calibration_observation_budget = (
            calibration_case_count
            * self.observation_budget.minimum_observations_per_reserved_calibration_case
        )
        final_observation_budget = (
            final_case_count
            * self.observation_budget.minimum_observations_per_reserved_final_evaluation_case
        )
        minimum_calibration_observations = (
            self.observation_budget.minimum_calibration_observation_count
        )
        minimum_final_observations = (
            self.observation_budget.minimum_final_evaluation_observation_count
        )
        if calibration_observation_budget < minimum_calibration_observations:
            raise ValueError(
                "V2 calibration observation budget does not meet its declared floor"
            )
        if final_observation_budget < minimum_final_observations:
            raise ValueError(
                "V2 final-evaluation observation budget does not meet its declared floor"
            )
        return self


def load_calibration_redesign_v2_scenario_family_registry_proposal(
    path: Path,
) -> CalibrationRedesignV2ScenarioFamilyRegistryProposal:
    """Load V2 planning metadata only after the fixture root passes the proposal-only gate."""

    assert_calibration_redesign_v2_proposal_only_fixture_root(path.parent)
    payload = _read_json(path)
    try:
        return CalibrationRedesignV2ScenarioFamilyRegistryProposal.model_validate(
            payload
        )
    except ValidationError as error:
        error_text = str(error)
        violation_code = (
            CalibrationRedesignV2ProposalViolationCode.V1_EVIDENCE_REFERENCE
            if "V1 data-bearing" in error_text
            else CalibrationRedesignV2ProposalViolationCode.PROPOSAL_SCHEMA_ERROR
        )
        raise CalibrationRedesignV2ProposalLoadError(
            violation_code,
            f"V2 scenario-family registry proposal validation failed: {error_text}",
        ) from error


def assert_calibration_redesign_v2_proposal_only_fixture_root(root: Path) -> None:
    """Reject V2 fixture content before the proposal-only contract boundary is superseded."""

    resolved_root = root.resolve()
    if not resolved_root.is_dir():
        raise CalibrationRedesignV2ProposalLoadError(
            CalibrationRedesignV2ProposalViolationCode.PROPOSAL_PROVENANCE_MISMATCH,
            f"V2 proposal fixture root is missing: {resolved_root}",
        )

    proposal_path = resolved_root / _V2_PROPOSAL_FILENAME
    if not proposal_path.is_file():
        raise CalibrationRedesignV2ProposalLoadError(
            CalibrationRedesignV2ProposalViolationCode.PROPOSAL_PROVENANCE_MISMATCH,
            f"V2 registry proposal is missing: {proposal_path}",
        )

    prohibited_asset_paths = (
        resolved_root / "calibration_manifest.json",
        resolved_root / "final_evaluation_manifest.json",
    )
    if any(path.exists() for path in prohibited_asset_paths):
        raise CalibrationRedesignV2ProposalLoadError(
            CalibrationRedesignV2ProposalViolationCode.PROPOSAL_ONLY_BOUNDARY_VIOLATION,
            "V2 manifests are prohibited before controlled registry finalization",
        )

    prohibited_asset_directories = (
        resolved_root / "inputs",
        resolved_root / "expected_outcomes",
    )
    for directory in prohibited_asset_directories:
        if directory.is_dir() and any(path.is_file() for path in directory.rglob("*")):
            raise CalibrationRedesignV2ProposalLoadError(
                CalibrationRedesignV2ProposalViolationCode.PROPOSAL_ONLY_BOUNDARY_VIOLATION,
                (
                    "V2 runtime or outcome assets are prohibited before controlled registry "
                    "finalization"
                ),
            )

    for path in resolved_root.rglob("*.json"):
        if path.resolve() != proposal_path.resolve():
            raise CalibrationRedesignV2ProposalLoadError(
                CalibrationRedesignV2ProposalViolationCode.PROPOSAL_ONLY_BOUNDARY_VIOLATION,
                "only the V2 registry proposal JSON is allowed at this contract boundary",
            )


def _read_json(path: Path) -> Any:
    """Read local planning metadata without fallback or silent recovery behavior."""

    try:
        return json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationRedesignV2ProposalLoadError(
            CalibrationRedesignV2ProposalViolationCode.PROPOSAL_PROVENANCE_MISMATCH,
            f"unable to read V2 registry proposal: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV2ProposalLoadError(
            CalibrationRedesignV2ProposalViolationCode.PROPOSAL_SCHEMA_ERROR,
            f"invalid JSON in V2 registry proposal: {error.msg}",
        ) from error
