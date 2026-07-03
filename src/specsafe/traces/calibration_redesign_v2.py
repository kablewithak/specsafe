"""V2 registry finalization controls for bounded-Platt calibration research.

The module preserves the reviewed proposal as provenance and finalizes its reserved V2
scenario-family inventory. The fixture root stays fail-closed until an explicit
case-asset authoring boundary permits typed runtime and expected-outcome assets.
It never imports V1 data-bearing assets.
"""

from __future__ import annotations

import hashlib
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
_V2_REGISTRY_FILENAME = "scenario_family_registry.json"

_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.DEVELOPMENT: TraceDataRole.SYNTHETIC_FIXTURE,
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}


class CalibrationRedesignV2ProposalViolationCode(StrEnum):
    """Machine-readable reasons proposal evidence cannot cross its reviewed boundary."""

    PROPOSAL_SCHEMA_ERROR = "calibration_redesign_v2_proposal_schema_error"
    PROPOSAL_PROVENANCE_MISMATCH = "calibration_redesign_v2_proposal_provenance_mismatch"
    V1_EVIDENCE_REFERENCE = "calibration_redesign_v2_v1_evidence_reference"
    PROPOSAL_ONLY_BOUNDARY_VIOLATION = "calibration_redesign_v2_proposal_only_boundary_violation"


class CalibrationRedesignV2ProposalLoadError(ValueError):
    """Typed error raised when V2 proposal metadata is unsafe or incomplete."""

    def __init__(
        self,
        code: CalibrationRedesignV2ProposalViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV2RegistryViolationCode(StrEnum):
    """Machine-readable reasons a finalized V2 registry cannot be trusted."""

    REGISTRY_SCHEMA_ERROR = "calibration_redesign_v2_registry_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = "calibration_redesign_v2_registry_provenance_mismatch"
    V1_EVIDENCE_REFERENCE = "calibration_redesign_v2_registry_v1_evidence_reference"
    FINALIZATION_BOUNDARY_VIOLATION = (
        "calibration_redesign_v2_registry_finalization_boundary_violation"
    )
    CASE_AUTHORING_BOUNDARY_VIOLATION = "calibration_redesign_v2_case_authoring_boundary_violation"
    CALIBRATION_MANIFEST_BOUNDARY_VIOLATION = (
        "calibration_redesign_v2_calibration_manifest_boundary_violation"
    )
    FINAL_EVALUATION_MANIFEST_BOUNDARY_VIOLATION = (
        "calibration_redesign_v2_final_evaluation_manifest_boundary_violation"
    )


class CalibrationRedesignV2RegistryLoadError(ValueError):
    """Typed error raised when a finalized V2 registry violates its evidence boundary."""

    def __init__(
        self,
        code: CalibrationRedesignV2RegistryViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV2ObservationBudget(StrictContract):
    """Predeclared minimum observation budget without encoding fixture values."""

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
        """Require unique V2-only case identifiers before case asset creation."""

        _validate_v2_case_ids(case_ids)
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

        _validate_v2_family_id(self.scenario_family_id)
        _validate_split_role_and_quarantine(
            split=self.split,
            primary_data_role=self.primary_data_role,
            is_final_evaluation_quarantined=self.is_final_evaluation_quarantined,
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
    families: tuple[CalibrationRedesignV2ScenarioFamilyProposal, ...] = Field(min_length=1)
    explicit_exclusions: tuple[str, ...] = Field(min_length=5)
    next_authorized_artifact: Literal["v2-controlled-registry-finalization-and-case-contracts"]

    @model_validator(mode="after")
    def validate_proposal_only_governance(
        self,
    ) -> CalibrationRedesignV2ScenarioFamilyRegistryProposal:
        """Enforce V2 planning floors without accepting runtime or outcome evidence."""

        _validate_common_v2_registry_governance(
            families=self.families,
            observation_budget=self.observation_budget,
            explicit_exclusions=self.explicit_exclusions,
        )
        return self


class CalibrationRedesignV2ScenarioFamilyRecord(StrictContract):
    """One finalized V2 family reserved for typed case-contract authoring."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    primary_data_role: TraceDataRole
    parent_scenario_family_id: None = None
    source_template_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_ids: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=500)
    target_failure_modes: tuple[str, ...] = Field(min_length=1)
    is_final_evaluation_quarantined: bool
    authoring_status: Literal["reserved_for_case_contract_authoring"]

    @field_validator("case_ids")
    @classmethod
    def validate_case_ids(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        """Require finalized case IDs to remain unique and V2-only."""

        _validate_v2_case_ids(case_ids)
        return case_ids

    @field_validator("target_failure_modes")
    @classmethod
    def validate_unique_target_failure_modes(
        cls,
        target_failure_modes: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Retain one stated diagnostic purpose per declared failure mode."""

        if len(set(target_failure_modes)) != len(target_failure_modes):
            raise ValueError("target failure modes must be unique within one V2 family")
        return target_failure_modes

    @model_validator(mode="after")
    def validate_finalized_family_governance(
        self,
    ) -> CalibrationRedesignV2ScenarioFamilyRecord:
        """Bind a finalized V2 family to its governed split and quarantine role."""

        _validate_v2_family_id(self.scenario_family_id)
        _validate_split_role_and_quarantine(
            split=self.split,
            primary_data_role=self.primary_data_role,
            is_final_evaluation_quarantined=self.is_final_evaluation_quarantined,
        )
        return self


class CalibrationRedesignV2ScenarioFamilyRegistry(StrictContract):
    """Finalized V2 registry that precedes typed runtime and outcome fixture authoring."""

    schema_version: Literal["calibration-redesign-v2-scenario-family-registry-v1"]
    registry_status: Literal["finalized_for_case_contract_authoring"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v2"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    authoring_protocol_version: Literal["calibration-redesign-v2-entry-protocol-v1"]
    candidate_artifact_id: Literal["bounded-platt-scaling-v1"]
    proposal_relative_path: Literal["scenario_family_registry_proposal.json"]
    proposal_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    v1_data_bearing_evidence_used: Literal[False]
    v2_runtime_or_outcome_assets_authored: Literal[False]
    v2_manifests_authored: Literal[False]
    observation_budget: CalibrationRedesignV2ObservationBudget
    families: tuple[CalibrationRedesignV2ScenarioFamilyRecord, ...] = Field(min_length=1)
    explicit_exclusions: tuple[str, ...] = Field(min_length=5)
    next_authorized_artifact: Literal["v2-runtime-and-outcome-fixture-authoring"]

    @model_validator(mode="after")
    def validate_finalized_registry_governance(
        self,
    ) -> CalibrationRedesignV2ScenarioFamilyRegistry:
        """Prevent V2 registry finalization from smuggling in authored evidence or manifests."""

        _validate_common_v2_registry_governance(
            families=self.families,
            observation_budget=self.observation_budget,
            explicit_exclusions=self.explicit_exclusions,
        )
        if self.v1_data_bearing_evidence_used:
            raise ValueError("V1 data-bearing evidence is prohibited in V2")
        if self.v2_runtime_or_outcome_assets_authored:
            raise ValueError("V2 runtime or outcome assets are not allowed at finalization")
        if self.v2_manifests_authored:
            raise ValueError("V2 manifests are not allowed at registry finalization")
        return self


def load_calibration_redesign_v2_scenario_family_registry_proposal(
    path: Path,
) -> CalibrationRedesignV2ScenarioFamilyRegistryProposal:
    """Load retained V2 proposal metadata without reading V1 evidence or fixture assets."""

    payload = _read_json(
        path,
        error_type=CalibrationRedesignV2ProposalLoadError,
        schema_code=CalibrationRedesignV2ProposalViolationCode.PROPOSAL_SCHEMA_ERROR,
        provenance_code=(CalibrationRedesignV2ProposalViolationCode.PROPOSAL_PROVENANCE_MISMATCH),
        asset_label="V2 registry proposal",
    )
    try:
        return CalibrationRedesignV2ScenarioFamilyRegistryProposal.model_validate(payload)
    except ValidationError as error:
        raise CalibrationRedesignV2ProposalLoadError(
            _proposal_violation_code(error),
            f"V2 scenario-family registry proposal validation failed: {error}",
        ) from error


def build_calibration_redesign_v2_scenario_family_registry(root: Path) -> Path:
    """Finalize the reviewed V2 proposal into a hash-linked registry without fixtures."""

    resolved_root = root.resolve()
    assert_calibration_redesign_v2_proposal_only_fixture_root(resolved_root)
    proposal_path = resolved_root / _V2_PROPOSAL_FILENAME
    proposal_bytes = _read_bytes(
        proposal_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        provenance_code=(CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH),
        asset_label="V2 registry proposal",
    )
    proposal = load_calibration_redesign_v2_scenario_family_registry_proposal(proposal_path)
    registry = CalibrationRedesignV2ScenarioFamilyRegistry(
        schema_version="calibration-redesign-v2-scenario-family-registry-v1",
        registry_status="finalized_for_case_contract_authoring",
        fixture_set_id=proposal.fixture_set_id,
        fixture_set_version=proposal.fixture_set_version,
        source_type=proposal.source_type,
        authoring_protocol_version=proposal.authoring_protocol_version,
        candidate_artifact_id=proposal.candidate_artifact_id,
        proposal_relative_path=_V2_PROPOSAL_FILENAME,
        proposal_sha256=_sha256(proposal_bytes),
        v1_data_bearing_evidence_used=False,
        v2_runtime_or_outcome_assets_authored=False,
        v2_manifests_authored=False,
        observation_budget=proposal.observation_budget,
        families=tuple(
            CalibrationRedesignV2ScenarioFamilyRecord(
                scenario_family_id=family.scenario_family_id,
                split=family.split,
                primary_data_role=family.primary_data_role,
                parent_scenario_family_id=family.parent_scenario_family_id,
                source_template_fingerprint=family.source_template_fingerprint,
                case_ids=family.reserved_case_ids,
                rationale=family.rationale,
                target_failure_modes=family.target_failure_modes,
                is_final_evaluation_quarantined=(family.is_final_evaluation_quarantined),
                authoring_status="reserved_for_case_contract_authoring",
            )
            for family in proposal.families
        ),
        explicit_exclusions=proposal.explicit_exclusions,
        next_authorized_artifact="v2-runtime-and-outcome-fixture-authoring",
    )
    registry_path = resolved_root / _V2_REGISTRY_FILENAME
    registry_path.write_text(
        json.dumps(registry.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    return registry_path


def load_calibration_redesign_v2_scenario_family_registry(
    path: Path,
    *,
    allow_case_assets: bool = False,
    allow_calibration_manifest: bool = False,
    allow_final_evaluation_manifest: bool = False,
) -> CalibrationRedesignV2ScenarioFamilyRegistry:
    """Load a finalized V2 registry under its active governed fixture-root boundary."""

    active_modes = sum(
        (
            allow_case_assets,
            allow_calibration_manifest,
            allow_final_evaluation_manifest,
        )
    )
    if active_modes > 1:
        raise ValueError("only one V2 fixture-root mode may be selected")

    root = path.parent
    if allow_final_evaluation_manifest:
        assert_calibration_redesign_v2_final_evaluation_manifest_fixture_root(root)
    elif allow_calibration_manifest:
        assert_calibration_redesign_v2_calibration_manifest_fixture_root(root)
    elif allow_case_assets:
        assert_calibration_redesign_v2_case_authoring_fixture_root(root)
    else:
        assert_calibration_redesign_v2_registry_finalization_fixture_root(root)
    payload = _read_json(
        path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        schema_code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_SCHEMA_ERROR,
        provenance_code=(CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH),
        asset_label="V2 finalized registry",
    )
    try:
        registry = CalibrationRedesignV2ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        raise CalibrationRedesignV2RegistryLoadError(
            _registry_violation_code(error),
            f"V2 scenario-family registry validation failed: {error}",
        ) from error

    proposal_path = root / registry.proposal_relative_path
    proposal_bytes = _read_bytes(
        proposal_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        provenance_code=(CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH),
        asset_label="V2 registry proposal",
    )
    if _sha256(proposal_bytes) != registry.proposal_sha256:
        raise CalibrationRedesignV2RegistryLoadError(
            CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V2 finalized registry proposal hash does not match the retained proposal bytes",
        )

    proposal = load_calibration_redesign_v2_scenario_family_registry_proposal(proposal_path)
    _validate_registry_matches_proposal(registry, proposal)
    return registry


def assert_calibration_redesign_v2_proposal_only_fixture_root(root: Path) -> None:
    """Reject V2 content beyond planning metadata before registry finalization occurs."""

    resolved_root = root.resolve()
    _require_directory(resolved_root, CalibrationRedesignV2ProposalLoadError)
    proposal_path = resolved_root / _V2_PROPOSAL_FILENAME
    _require_file(
        proposal_path,
        error_type=CalibrationRedesignV2ProposalLoadError,
        code=CalibrationRedesignV2ProposalViolationCode.PROPOSAL_PROVENANCE_MISMATCH,
        asset_label="V2 registry proposal",
    )
    _reject_v2_fixture_asset_paths(
        resolved_root,
        error_type=CalibrationRedesignV2ProposalLoadError,
        code=CalibrationRedesignV2ProposalViolationCode.PROPOSAL_ONLY_BOUNDARY_VIOLATION,
        message="V2 fixture assets or manifests are prohibited before registry finalization",
    )
    allowed_json_paths = {proposal_path.resolve()}
    _assert_only_allowed_json_paths(
        resolved_root,
        allowed_paths=allowed_json_paths,
        error_type=CalibrationRedesignV2ProposalLoadError,
        code=CalibrationRedesignV2ProposalViolationCode.PROPOSAL_ONLY_BOUNDARY_VIOLATION,
        message="only the V2 registry proposal JSON is allowed at the proposal-only boundary",
    )


def assert_calibration_redesign_v2_registry_finalization_fixture_root(
    root: Path,
) -> None:
    """Verify finalized registry metadata exists while fixture bytes still do not exist."""

    resolved_root = root.resolve()
    _require_directory(resolved_root, CalibrationRedesignV2RegistryLoadError)
    proposal_path = resolved_root / _V2_PROPOSAL_FILENAME
    registry_path = resolved_root / _V2_REGISTRY_FILENAME
    _require_file(
        proposal_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
        asset_label="V2 registry proposal",
    )
    _require_file(
        registry_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
        asset_label="V2 finalized registry",
    )
    _reject_v2_fixture_asset_paths(
        resolved_root,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=(CalibrationRedesignV2RegistryViolationCode.FINALIZATION_BOUNDARY_VIOLATION),
        message=(
            "V2 fixture assets or manifests are prohibited until a later fixture-authoring boundary"
        ),
    )
    _assert_only_allowed_json_paths(
        resolved_root,
        allowed_paths={proposal_path.resolve(), registry_path.resolve()},
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=(CalibrationRedesignV2RegistryViolationCode.FINALIZATION_BOUNDARY_VIOLATION),
        message="only V2 proposal and finalized registry JSON are allowed at finalization",
    )


def assert_calibration_redesign_v2_case_authoring_fixture_root(root: Path) -> None:
    """Permit only governed V2 case paths while keeping manifests and extra JSON blocked.

    The finalized registry remains immutable provenance for the reviewed reservation state. This
    authoring boundary permits separate runtime and expected-outcome JSON assets only at their
    exact future locations; it does not authorize manifest construction, fitting, or assessment.
    """

    resolved_root = root.resolve()
    _require_directory(resolved_root, CalibrationRedesignV2RegistryLoadError)
    proposal_path = resolved_root / _V2_PROPOSAL_FILENAME
    registry_path = resolved_root / _V2_REGISTRY_FILENAME
    _require_file(
        proposal_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
        asset_label="V2 registry proposal",
    )
    _require_file(
        registry_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
        asset_label="V2 finalized registry",
    )
    _reject_v2_manifest_paths(
        resolved_root,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.CASE_AUTHORING_BOUNDARY_VIOLATION,
        message="V2 manifests are prohibited during case-asset authoring",
    )
    _assert_only_allowed_v2_case_authoring_json_paths(resolved_root)


def assert_calibration_redesign_v2_calibration_manifest_fixture_root(root: Path) -> None:
    """Permit frozen calibration evidence and quarantined final case pairs before assessment.

    The calibration manifest remains calibration-only, but later held-out case authoring must
    coexist in the same governed fixture root so that the frozen calibration artifact remains
    reproducible. This boundary permits only exact V2 calibration or final-evaluation case
    directories plus an optional ``calibration_manifest.json``. A final-evaluation manifest
    remains prohibited until every held-out family is authored and the assessment boundary is
    explicitly implemented.
    """

    resolved_root = root.resolve()
    _require_directory(resolved_root, CalibrationRedesignV2RegistryLoadError)
    proposal_path = resolved_root / _V2_PROPOSAL_FILENAME
    registry_path = resolved_root / _V2_REGISTRY_FILENAME
    _require_file(
        proposal_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
        asset_label="V2 registry proposal",
    )
    _require_file(
        registry_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
        asset_label="V2 finalized registry",
    )
    _assert_only_allowed_v2_calibration_manifest_json_paths(resolved_root)


def assert_calibration_redesign_v2_final_evaluation_manifest_fixture_root(root: Path) -> None:
    """Permit both frozen manifests and governed case pairs before the read-only assessment.

    The calibration manifest and bounded-Platt artifact were frozen before held-out case
    authoring. This later boundary permits a separate final-evaluation manifest that locks
    the quarantined corpus, but it neither loads the artifact nor evaluates it.
    """

    resolved_root = root.resolve()
    _require_directory(resolved_root, CalibrationRedesignV2RegistryLoadError)
    proposal_path = resolved_root / _V2_PROPOSAL_FILENAME
    registry_path = resolved_root / _V2_REGISTRY_FILENAME
    calibration_manifest = resolved_root / "calibration_manifest.json"
    _require_file(
        proposal_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
        asset_label="V2 registry proposal",
    )
    _require_file(
        registry_path,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
        asset_label="V2 finalized registry",
    )
    _require_file(
        calibration_manifest,
        error_type=CalibrationRedesignV2RegistryLoadError,
        code=(
            CalibrationRedesignV2RegistryViolationCode.FINAL_EVALUATION_MANIFEST_BOUNDARY_VIOLATION
        ),
        asset_label="V2 calibration manifest",
    )
    _assert_only_allowed_v2_final_evaluation_manifest_json_paths(resolved_root)


def _validate_v2_case_ids(case_ids: tuple[str, ...]) -> None:
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("V2 case IDs must be unique within one family")
    for case_id in case_ids:
        if case_id.startswith(("CRV1-", "STF-")):
            raise ValueError("V1 data-bearing case references are prohibited in V2")
        if (
            not case_id.startswith("CRV2-")
            or len(case_id) != 8
            or not case_id.removeprefix("CRV2-").isdigit()
        ):
            raise ValueError("V2 case IDs must use the CRV2-### namespace")


def _validate_v2_family_id(scenario_family_id: str) -> None:
    if scenario_family_id.startswith("CRV1-"):
        raise ValueError("V1 data-bearing family references are prohibited in V2")
    if not scenario_family_id.startswith("CRV2-"):
        raise ValueError("V2 scenario-family IDs must use the CRV2 namespace")


def _validate_split_role_and_quarantine(
    *,
    split: TraceSplit,
    primary_data_role: TraceDataRole,
    is_final_evaluation_quarantined: bool,
) -> None:
    expected_role = _EXPECTED_DATA_ROLE_BY_SPLIT[split]
    if primary_data_role is not expected_role:
        raise ValueError("primary_data_role must match the governed V2 split role")
    expected_quarantine = split is TraceSplit.FINAL_EVALUATION
    if is_final_evaluation_quarantined is not expected_quarantine:
        raise ValueError("final-evaluation quarantine must match the declared V2 split")


def _validate_common_v2_registry_governance(
    *,
    families: tuple[
        CalibrationRedesignV2ScenarioFamilyProposal | CalibrationRedesignV2ScenarioFamilyRecord,
        ...,
    ],
    observation_budget: CalibrationRedesignV2ObservationBudget,
    explicit_exclusions: tuple[str, ...],
) -> None:
    required_exclusions = {
        "No runtime-input fixture bytes are present.",
        "No expected-outcome assets or labels are present.",
    }
    if not required_exclusions.issubset(explicit_exclusions):
        raise ValueError("V2 registry must explicitly exclude runtime and outcome assets")

    family_ids = [family.scenario_family_id for family in families]
    if len(set(family_ids)) != len(family_ids):
        raise ValueError("V2 scenario-family IDs must be unique")

    fingerprints = [family.source_template_fingerprint for family in families]
    if len(set(fingerprints)) != len(fingerprints):
        raise ValueError("V2 source-template fingerprints must be globally unique")

    case_ids: set[str] = set()
    families_by_split: dict[TraceSplit, list[Any]] = {split: [] for split in TraceSplit}
    for family in families:
        families_by_split[family.split].append(family)
        for case_id in _family_case_ids(family):
            if case_id in case_ids:
                raise ValueError("V2 case IDs must not repeat across families")
            case_ids.add(case_id)

    calibration_families = families_by_split[TraceSplit.CALIBRATION]
    final_families = families_by_split[TraceSplit.FINAL_EVALUATION]
    development_families = families_by_split[TraceSplit.DEVELOPMENT]
    adversarial_families = families_by_split[TraceSplit.ADVERSARIAL_REGRESSION]

    if len(calibration_families) < 3:
        raise ValueError("V2 registry requires at least three calibration families")
    if any(_family_case_count(family) < 4 for family in calibration_families):
        raise ValueError("each V2 calibration family requires at least four case IDs")
    if len(final_families) < 3:
        raise ValueError("V2 registry requires at least three final-evaluation families")
    if any(_family_case_count(family) < 3 for family in final_families):
        raise ValueError("each V2 final-evaluation family requires at least three case IDs")
    if sum(_family_case_count(family) for family in development_families) < 2:
        raise ValueError("V2 registry requires at least two development cases")
    if not adversarial_families:
        raise ValueError("V2 registry requires an adversarial-regression family")

    calibration_case_count = sum(_family_case_count(family) for family in calibration_families)
    final_case_count = sum(_family_case_count(family) for family in final_families)
    calibration_observations = (
        calibration_case_count
        * observation_budget.minimum_observations_per_reserved_calibration_case
    )
    final_observations = (
        final_case_count
        * observation_budget.minimum_observations_per_reserved_final_evaluation_case
    )
    if calibration_observations < observation_budget.minimum_calibration_observation_count:
        raise ValueError("V2 calibration observation budget does not meet its declared floor")
    if final_observations < observation_budget.minimum_final_evaluation_observation_count:
        raise ValueError("V2 final-evaluation observation budget does not meet its declared floor")


def _family_case_ids(
    family: CalibrationRedesignV2ScenarioFamilyProposal | CalibrationRedesignV2ScenarioFamilyRecord,
) -> tuple[str, ...]:
    if isinstance(family, CalibrationRedesignV2ScenarioFamilyProposal):
        return family.reserved_case_ids
    return family.case_ids


def _family_case_count(
    family: CalibrationRedesignV2ScenarioFamilyProposal | CalibrationRedesignV2ScenarioFamilyRecord,
) -> int:
    return len(_family_case_ids(family))


def _validate_registry_matches_proposal(
    registry: CalibrationRedesignV2ScenarioFamilyRegistry,
    proposal: CalibrationRedesignV2ScenarioFamilyRegistryProposal,
) -> None:
    aligned_fields = (
        "fixture_set_id",
        "fixture_set_version",
        "source_type",
        "authoring_protocol_version",
        "candidate_artifact_id",
        "observation_budget",
        "explicit_exclusions",
    )
    for field_name in aligned_fields:
        if getattr(registry, field_name) != getattr(proposal, field_name):
            raise CalibrationRedesignV2RegistryLoadError(
                CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
                f"V2 finalized registry disagrees with retained proposal on {field_name}",
            )

    proposal_by_id = {family.scenario_family_id: family for family in proposal.families}
    registry_by_id = {family.scenario_family_id: family for family in registry.families}
    if set(proposal_by_id) != set(registry_by_id):
        raise CalibrationRedesignV2RegistryLoadError(
            CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V2 finalized registry must preserve exactly the reviewed proposal family IDs",
        )
    for family_id, proposal_family in proposal_by_id.items():
        registry_family = registry_by_id[family_id]
        aligned_family_fields = (
            "scenario_family_id",
            "split",
            "primary_data_role",
            "parent_scenario_family_id",
            "source_template_fingerprint",
            "rationale",
            "target_failure_modes",
            "is_final_evaluation_quarantined",
        )
        for field_name in aligned_family_fields:
            if getattr(registry_family, field_name) != getattr(proposal_family, field_name):
                raise CalibrationRedesignV2RegistryLoadError(
                    CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
                    (
                        "V2 finalized registry disagrees with retained proposal family "
                        f"{family_id} on {field_name}"
                    ),
                )
        if registry_family.case_ids != proposal_family.reserved_case_ids:
            raise CalibrationRedesignV2RegistryLoadError(
                CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
                f"V2 finalized registry changed reserved case IDs for family {family_id}",
            )


def _assert_only_allowed_v2_calibration_manifest_json_paths(root: Path) -> None:
    """Permit calibration assets and quarantined held-out pairs before final assessment.

    A frozen calibration manifest must stay reproducible after final-case authoring. This
    root guard therefore permits only governed calibration or final-evaluation case JSON
    pairs, plus the retained proposal, registry, calibration manifest, and optional final
    manifest. It still blocks every arbitrary JSON path.
    """

    allowed_governance_paths = {
        (root / _V2_PROPOSAL_FILENAME).resolve(),
        (root / _V2_REGISTRY_FILENAME).resolve(),
        (root / "calibration_manifest.json").resolve(),
        (root / "final_evaluation_manifest.json").resolve(),
    }
    runtime_directory = root / "inputs" / "cases"
    outcomes_directory = root / "expected_outcomes" / "cases"
    for path in root.rglob("*.json"):
        resolved_path = path.resolve()
        if resolved_path in allowed_governance_paths:
            continue
        is_case_asset = path.parent in {runtime_directory, outcomes_directory}
        if is_case_asset and (
            _is_v2_calibration_case_asset_name(path)
            or _is_v2_final_evaluation_case_asset_name(path)
        ):
            continue
        raise CalibrationRedesignV2RegistryLoadError(
            CalibrationRedesignV2RegistryViolationCode.CALIBRATION_MANIFEST_BOUNDARY_VIOLATION,
            (
                "V2 calibration-manifest boundary permits only governed calibration or "
                "quarantined final-evaluation case pairs and approved manifest JSON"
            ),
        )


def _assert_only_allowed_v2_final_evaluation_manifest_json_paths(root: Path) -> None:
    """Permit only governed V2 evidence assets plus the two explicit manifests."""

    allowed_governance_paths = {
        (root / _V2_PROPOSAL_FILENAME).resolve(),
        (root / _V2_REGISTRY_FILENAME).resolve(),
        (root / "calibration_manifest.json").resolve(),
        (root / "final_evaluation_manifest.json").resolve(),
    }
    runtime_directory = root / "inputs" / "cases"
    outcomes_directory = root / "expected_outcomes" / "cases"
    for path in root.rglob("*.json"):
        resolved_path = path.resolve()
        if resolved_path in allowed_governance_paths:
            continue
        is_case_asset = path.parent in {runtime_directory, outcomes_directory}
        if is_case_asset and (
            _is_v2_calibration_case_asset_name(path)
            or _is_v2_final_evaluation_case_asset_name(path)
        ):
            continue
        raise CalibrationRedesignV2RegistryLoadError(
            CalibrationRedesignV2RegistryViolationCode.FINAL_EVALUATION_MANIFEST_BOUNDARY_VIOLATION,
            (
                "V2 final-manifest boundary permits only governed case pairs and approved "
                "manifest JSON"
            ),
        )


def _is_v2_calibration_case_asset_name(path: Path) -> bool:
    if path.suffix != ".json" or not _is_v2_case_asset_name(path):
        return False
    case_number = int(path.stem.removeprefix("CRV2-"))
    return 100 <= case_number < 200


def _is_v2_final_evaluation_case_asset_name(path: Path) -> bool:
    if path.suffix != ".json" or not _is_v2_case_asset_name(path):
        return False
    case_number = int(path.stem.removeprefix("CRV2-"))
    return 200 <= case_number < 300


def _reject_v2_manifest_paths(
    root: Path,
    *,
    error_type: type[CalibrationRedesignV2ProposalLoadError]
    | type[CalibrationRedesignV2RegistryLoadError],
    code: CalibrationRedesignV2ProposalViolationCode | CalibrationRedesignV2RegistryViolationCode,
    message: str,
) -> None:
    prohibited_paths = (
        root / "calibration_manifest.json",
        root / "final_evaluation_manifest.json",
    )
    if any(path.exists() for path in prohibited_paths):
        raise error_type(code, message)


def _assert_only_allowed_v2_case_authoring_json_paths(root: Path) -> None:
    allowed_governance_paths = {
        (root / _V2_PROPOSAL_FILENAME).resolve(),
        (root / _V2_REGISTRY_FILENAME).resolve(),
    }
    runtime_directory = root / "inputs" / "cases"
    outcomes_directory = root / "expected_outcomes" / "cases"
    for path in root.rglob("*.json"):
        resolved_path = path.resolve()
        if resolved_path in allowed_governance_paths:
            continue
        if path.parent in {runtime_directory, outcomes_directory} and _is_v2_case_asset_name(path):
            continue
        raise CalibrationRedesignV2RegistryLoadError(
            CalibrationRedesignV2RegistryViolationCode.CASE_AUTHORING_BOUNDARY_VIOLATION,
            "V2 case authoring permits JSON only in governed runtime and outcome case directories",
        )


def _is_v2_case_asset_name(path: Path) -> bool:
    case_id = path.stem
    return (
        case_id.startswith("CRV2-")
        and len(case_id) == 8
        and case_id.removeprefix("CRV2-").isdigit()
    )


def _reject_v2_fixture_asset_paths(
    root: Path,
    *,
    error_type: type[CalibrationRedesignV2ProposalLoadError]
    | type[CalibrationRedesignV2RegistryLoadError],
    code: CalibrationRedesignV2ProposalViolationCode | CalibrationRedesignV2RegistryViolationCode,
    message: str,
) -> None:
    _reject_v2_manifest_paths(
        root,
        error_type=error_type,
        code=code,
        message=message,
    )
    for directory in (root / "inputs", root / "expected_outcomes"):
        if directory.is_dir() and any(path.is_file() for path in directory.rglob("*")):
            raise error_type(code, message)


def _assert_only_allowed_json_paths(
    root: Path,
    *,
    allowed_paths: set[Path],
    error_type: type[CalibrationRedesignV2ProposalLoadError]
    | type[CalibrationRedesignV2RegistryLoadError],
    code: CalibrationRedesignV2ProposalViolationCode | CalibrationRedesignV2RegistryViolationCode,
    message: str,
) -> None:
    for path in root.rglob("*.json"):
        if path.resolve() not in allowed_paths:
            raise error_type(code, message)


def _require_directory(
    root: Path,
    error_type: type[CalibrationRedesignV2ProposalLoadError]
    | type[CalibrationRedesignV2RegistryLoadError],
) -> None:
    if not root.is_dir():
        if error_type is CalibrationRedesignV2ProposalLoadError:
            code: (
                CalibrationRedesignV2ProposalViolationCode
                | CalibrationRedesignV2RegistryViolationCode
            ) = CalibrationRedesignV2ProposalViolationCode.PROPOSAL_PROVENANCE_MISMATCH
        else:
            code = CalibrationRedesignV2RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH
        raise error_type(code, f"V2 fixture root is missing: {root}")


def _require_file(
    path: Path,
    *,
    error_type: type[CalibrationRedesignV2ProposalLoadError]
    | type[CalibrationRedesignV2RegistryLoadError],
    code: CalibrationRedesignV2ProposalViolationCode | CalibrationRedesignV2RegistryViolationCode,
    asset_label: str,
) -> None:
    if not path.is_file():
        raise error_type(code, f"{asset_label} is missing: {path}")


def _read_json(
    path: Path,
    *,
    error_type: type[CalibrationRedesignV2ProposalLoadError]
    | type[CalibrationRedesignV2RegistryLoadError],
    schema_code: CalibrationRedesignV2ProposalViolationCode
    | CalibrationRedesignV2RegistryViolationCode,
    provenance_code: CalibrationRedesignV2ProposalViolationCode
    | CalibrationRedesignV2RegistryViolationCode,
    asset_label: str,
) -> Any:
    try:
        return json.loads(path.read_bytes())
    except OSError as error:
        raise error_type(provenance_code, f"unable to read {asset_label}: {path}") from error
    except json.JSONDecodeError as error:
        raise error_type(schema_code, f"invalid JSON in {asset_label}: {error.msg}") from error


def _read_bytes(
    path: Path,
    *,
    error_type: type[CalibrationRedesignV2RegistryLoadError],
    provenance_code: CalibrationRedesignV2RegistryViolationCode,
    asset_label: str,
) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise error_type(provenance_code, f"unable to read {asset_label}: {path}") from error


def _proposal_violation_code(
    error: ValidationError,
) -> CalibrationRedesignV2ProposalViolationCode:
    error_text = str(error)
    if "V1 data-bearing" in error_text:
        return CalibrationRedesignV2ProposalViolationCode.V1_EVIDENCE_REFERENCE
    return CalibrationRedesignV2ProposalViolationCode.PROPOSAL_SCHEMA_ERROR


def _registry_violation_code(
    error: ValidationError,
) -> CalibrationRedesignV2RegistryViolationCode:
    error_text = str(error)
    if "V1 data-bearing" in error_text:
        return CalibrationRedesignV2RegistryViolationCode.V1_EVIDENCE_REFERENCE
    return CalibrationRedesignV2RegistryViolationCode.REGISTRY_SCHEMA_ERROR


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
