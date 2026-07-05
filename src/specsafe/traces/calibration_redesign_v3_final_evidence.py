"""Separate V3 final-evidence index and held-out case loader.

This module records the full 24-case held-out inventory separately from the frozen
calibration registry. Only the light-capacity family is authored in this slice; no
final-evaluation manifest, score, policy, or scheduler behaviour is introduced.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import (
    StrictContract,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
)
from specsafe.traces.calibration_redesign_v3 import (
    CalibrationRedesignV3RegistryLoadError,
    assert_calibration_redesign_v3_calibration_manifest_fixture_root,
)
from specsafe.traces.calibration_redesign_v3_cases import (
    CalibrationRedesignV3ExpectedOutcomes,
    CalibrationRedesignV3ReplayCase,
    CalibrationRedesignV3RuntimeInput,
)

_INDEX_FILENAME = "final_evidence_index.json"
_FINAL_ROOT = "final_evaluation"
_LIGHT_CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(201, 207))
_MODERATE_CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(207, 213))
_SATURATED_CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(213, 219))
_JAGGED_CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(219, 225))
_EXPECTED_CASE_IDS = {
    "CRV3-FINAL-LIGHT-CAPACITY": _LIGHT_CASE_IDS,
    "CRV3-FINAL-MODERATE-CAPACITY": _MODERATE_CASE_IDS,
    "CRV3-FINAL-SATURATED-CAPACITY": _SATURATED_CASE_IDS,
    "CRV3-FINAL-JAGGED-CAPACITY": _JAGGED_CASE_IDS,
}
_CLOSED_MARKERS = (b"crv1-", b"crv2-", b"bounded-platt-scaling-v1", b"heldout_assessment")


class CalibrationRedesignV3FinalEvidenceViolationCode(StrEnum):
    """Machine-readable reasons the V3 held-out boundary cannot be trusted."""

    INDEX_SCHEMA_ERROR = "calibration_redesign_v3_final_evidence_index_schema_error"
    INDEX_INTEGRITY_MISMATCH = "calibration_redesign_v3_final_evidence_index_integrity_mismatch"
    INDEX_PROVENANCE_MISMATCH = "calibration_redesign_v3_final_evidence_index_provenance_mismatch"
    CASE_SCHEMA_ERROR = "calibration_redesign_v3_final_evidence_case_schema_error"
    CASE_ALIGNMENT_ERROR = "calibration_redesign_v3_final_evidence_case_alignment_error"
    CASE_MEMBERSHIP_ERROR = "calibration_redesign_v3_final_evidence_case_membership_error"
    BOUNDARY_VIOLATION = "calibration_redesign_v3_final_evidence_boundary_violation"


class CalibrationRedesignV3FinalEvidenceLoadError(ValueError):
    """Typed error raised when V3 final evidence cannot cross its boundary."""

    def __init__(self, code: CalibrationRedesignV3FinalEvidenceViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV3FinalEvidenceWorkloadAllocation(StrictContract):
    """The fixed 2/2/2 workload split for one capacity family."""

    structured_text_case_count: Literal[2]
    code_case_count: Literal[2]
    open_ended_chat_case_count: Literal[2]


class CalibrationRedesignV3FinalEvidenceFamily(StrictContract):
    """One final-evaluation capacity family, independent of calibration provenance."""

    scenario_family_id: Literal[
        "CRV3-FINAL-LIGHT-CAPACITY",
        "CRV3-FINAL-MODERATE-CAPACITY",
        "CRV3-FINAL-SATURATED-CAPACITY",
        "CRV3-FINAL-JAGGED-CAPACITY",
    ]
    capacity_profile_id: Literal[
        "synthetic-v3-final-light-capacity",
        "synthetic-v3-final-moderate-capacity",
        "synthetic-v3-final-saturated-capacity",
        "synthetic-v3-final-jagged-capacity",
    ]
    split: Literal[TraceSplit.FINAL_EVALUATION]
    data_role: Literal[TraceDataRole.HELD_OUT_EVALUATION]
    reserved_case_ids: tuple[str, ...] = Field(min_length=6, max_length=6)
    authored_case_ids: tuple[str, ...] = Field(max_length=6)
    workload_allocation: CalibrationRedesignV3FinalEvidenceWorkloadAllocation
    authoring_status: Literal["final_light_capacity_authored", "reserved_for_v3_case_authoring"]

    @model_validator(mode="after")
    def validate_family_shape(self) -> CalibrationRedesignV3FinalEvidenceFamily:
        expected_ids = _EXPECTED_CASE_IDS[self.scenario_family_id]
        if self.reserved_case_ids != expected_ids:
            raise ValueError(
                "final family reservation must match the fixed V3 evidence constitution"
            )
        if len(set(self.authored_case_ids)) != len(self.authored_case_ids):
            raise ValueError("authored final case IDs must be unique")
        if not set(self.authored_case_ids).issubset(set(self.reserved_case_ids)):
            raise ValueError("authored final case IDs must be reserved by their family")
        expected_authored = (
            expected_ids if self.scenario_family_id == "CRV3-FINAL-LIGHT-CAPACITY" else ()
        )
        if self.authored_case_ids != expected_authored:
            raise ValueError("only the light-capacity family may be authored in this slice")
        expected_status = (
            "final_light_capacity_authored"
            if self.scenario_family_id == "CRV3-FINAL-LIGHT-CAPACITY"
            else "reserved_for_v3_case_authoring"
        )
        if self.authoring_status != expected_status:
            raise ValueError("final family authoring status does not match this evidence slice")
        return self


class CalibrationRedesignV3FinalEvidenceIndex(StrictContract):
    """Provenance-safe index for held-out V3 evidence, separate from calibration state."""

    schema_version: Literal["calibration-redesign-v3-final-evidence-index-v1"]
    index_status: Literal["light_capacity_authored"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    calibration_registry_path: Literal["scenario_family_registry.json"]
    calibration_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_manifest_path: Literal["calibration_manifest.json"]
    calibration_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_artifact_path: Literal[
        "evidence/calibration/quantile-isotonic-calibration-v1/artifact.json"
    ]
    calibration_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_fit_report_path: Literal[
        "evidence/calibration/quantile-isotonic-calibration-v1/fit_report.json"
    ]
    calibration_fit_report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evaluation_case_count: Literal[24]
    final_evaluation_observation_count: Literal[96]
    candidate_positions_per_case: Literal[4]
    families: tuple[CalibrationRedesignV3FinalEvidenceFamily, ...] = Field(
        min_length=4,
        max_length=4,
    )
    explicit_exclusions: tuple[str, ...] = Field(min_length=6)
    next_authorized_artifact: Literal["v3-final-moderate-capacity-fixtures"]

    @model_validator(mode="after")
    def validate_index_shape(self) -> CalibrationRedesignV3FinalEvidenceIndex:
        family_ids = {family.scenario_family_id for family in self.families}
        if family_ids != set(_EXPECTED_CASE_IDS):
            raise ValueError("final evidence index must contain all four capacity families")
        if sum(len(family.reserved_case_ids) for family in self.families) != 24:
            raise ValueError("final evidence index must reserve exactly 24 cases")
        if sum(len(family.authored_case_ids) for family in self.families) != 6:
            raise ValueError("only six light-capacity cases may be authored in this slice")
        required_exclusions = {
            "No V3 final-evaluation manifest or score is present.",
            (
                "No V3 scheduler, capacity-policy implementation, promotion decision, "
                "or runtime-control claim is present."
            ),
            (
                "No V3 calibration registry, manifest, artifact, or fit report is "
                "modified by final-evidence authoring."
            ),
            "No V1 or V2 data-bearing evidence influenced V3 final-case design.",
            "No V3 adversarial-regression assets are present.",
            "The fitted V3 calibrator must not be run against partial final evidence.",
        }
        if not required_exclusions.issubset(set(self.explicit_exclusions)):
            raise ValueError("final evidence index is missing required isolation exclusions")
        return self


def load_calibration_redesign_v3_final_evidence_index(
    root: Path,
) -> CalibrationRedesignV3FinalEvidenceIndex:
    """Load the separate V3 final-evidence index and verify frozen calibration provenance."""

    resolved_root = root.resolve()
    _assert_root_boundary(resolved_root)
    index_path = resolved_root / _INDEX_FILENAME
    payload = _read_json(index_path)
    try:
        index = CalibrationRedesignV3FinalEvidenceIndex.model_validate(payload)
    except ValidationError as error:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.INDEX_SCHEMA_ERROR,
            f"V3 final evidence index schema validation failed: {error}",
        ) from error
    _verify_frozen_provenance(resolved_root, index)
    return index


def load_calibration_redesign_v3_final_evaluation_replay_case(
    root: Path,
    case_id: str,
) -> CalibrationRedesignV3ReplayCase:
    """Load one currently authorised held-out V3 case pair without scoring it."""

    index = load_calibration_redesign_v3_final_evidence_index(root)
    if case_id not in _LIGHT_CASE_IDS:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_MEMBERSHIP_ERROR,
            "only CRV3-201 through CRV3-206 are authorised for current held-out loading",
        )
    final_root = root.resolve() / _FINAL_ROOT
    runtime_payload = _read_json(final_root / "inputs" / "cases" / f"{case_id}.json")
    outcomes_payload = _read_json(final_root / "expected_outcomes" / "cases" / f"{case_id}.json")
    try:
        runtime = CalibrationRedesignV3RuntimeInput.model_validate(runtime_payload)
    except ValidationError as error:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_SCHEMA_ERROR,
            f"V3 held-out runtime schema validation failed: {error}",
        ) from error
    try:
        outcomes = CalibrationRedesignV3ExpectedOutcomes.model_validate(outcomes_payload)
    except ValidationError as error:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_SCHEMA_ERROR,
            f"V3 held-out outcome schema validation failed: {error}",
        ) from error
    try:
        replay_case = CalibrationRedesignV3ReplayCase(
            runtime_input=runtime,
            expected_outcomes=outcomes,
        )
    except ValidationError as error:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_ALIGNMENT_ERROR,
            f"V3 held-out runtime and outcome assets do not align: {error}",
        ) from error
    _validate_light_case_membership(replay_case, index)
    return replay_case


def _assert_root_boundary(root: Path) -> None:
    try:
        assert_calibration_redesign_v3_calibration_manifest_fixture_root(root)
    except CalibrationRedesignV3RegistryLoadError as error:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.BOUNDARY_VIOLATION,
            f"V3 final evidence root is not authorised: {error}",
        ) from error


def _verify_frozen_provenance(root: Path, index: CalibrationRedesignV3FinalEvidenceIndex) -> None:
    project_root = root.parents[2]
    checks = (
        (root / index.calibration_registry_path, index.calibration_registry_sha256),
        (root / index.calibration_manifest_path, index.calibration_manifest_sha256),
        (project_root / index.calibration_artifact_path, index.calibration_artifact_sha256),
        (project_root / index.calibration_fit_report_path, index.calibration_fit_report_sha256),
    )
    for path, expected_hash in checks:
        actual_hash = _sha256(_read_bytes(path))
        if actual_hash != expected_hash:
            raise CalibrationRedesignV3FinalEvidenceLoadError(
                CalibrationRedesignV3FinalEvidenceViolationCode.INDEX_PROVENANCE_MISMATCH,
                f"frozen calibration provenance does not match final-evidence index: {path}",
            )


def _validate_light_case_membership(
    replay_case: CalibrationRedesignV3ReplayCase,
    index: CalibrationRedesignV3FinalEvidenceIndex,
) -> None:
    runtime = replay_case.runtime_input
    if runtime.case_id not in _LIGHT_CASE_IDS:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_MEMBERSHIP_ERROR,
            "held-out runtime case is not reserved for the light-capacity family",
        )
    if runtime.scenario_family_id != "CRV3-FINAL-LIGHT-CAPACITY":
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_MEMBERSHIP_ERROR,
            "held-out runtime case must use CRV3-FINAL-LIGHT-CAPACITY",
        )
    if (
        runtime.split is not TraceSplit.FINAL_EVALUATION
        or runtime.data_role is not TraceDataRole.HELD_OUT_EVALUATION
    ):
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_MEMBERSHIP_ERROR,
            "held-out runtime case must declare final_evaluation and held_out_evaluation",
        )
    family = next(
        item for item in index.families if item.scenario_family_id == runtime.scenario_family_id
    )
    if runtime.case_id not in family.authored_case_ids:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_MEMBERSHIP_ERROR,
            "held-out runtime case is not authorised by the final-evidence index",
        )
    if any(
        context.capacity_snapshot.profile_id != family.capacity_profile_id
        for context in runtime.contexts
    ):
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.CASE_MEMBERSHIP_ERROR,
            "held-out runtime contexts must use the family capacity profile",
        )


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        raw = _read_bytes(path)
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.BOUNDARY_VIOLATION,
            f"invalid JSON in V3 final-evidence asset {path.name}: {error.msg}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.BOUNDARY_VIOLATION,
            f"V3 final-evidence asset must contain a JSON object: {path.name}",
        )
    return payload


def _read_bytes(path: Path) -> bytes:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.BOUNDARY_VIOLATION,
            f"unable to read V3 final-evidence asset: {path}",
        ) from error
    if any(marker in raw.lower() for marker in _CLOSED_MARKERS):
        raise CalibrationRedesignV3FinalEvidenceLoadError(
            CalibrationRedesignV3FinalEvidenceViolationCode.BOUNDARY_VIOLATION,
            f"V3 final-evidence asset references closed evidence: {path.name}",
        )
    return raw


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
