"""Immutable V4 final-evaluation manifest and evidence-index controls.

This module freezes the quarantined CRV4-201 through CRV4-236 corpus only after its complete
runtime/outcome inventory exists. It records provenance and integrity; it does not run the held-
out calibration assessment, fit a calibrator, execute a policy, compare baselines, or authorize
runtime control.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import (
    StrictContract,
    TraceSourceType,
    WorkloadType,
)
from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4RegistryLoadError,
    CalibrationRedesignV4ScenarioFamilyRegistry,
    assert_calibration_redesign_v4_final_evaluation_fixture_root,
    load_calibration_redesign_v4_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_v4_final_cases import (
    CalibrationRedesignV4FinalExpectedOutcomes,
    CalibrationRedesignV4FinalReplayCase,
    CalibrationRedesignV4FinalRuntimeInput,
)

_FINAL_ROOT = "final_evaluation"
_FINAL_MANIFEST_FILENAME = "final_evaluation_manifest.json"
_FINAL_INDEX_FILENAME = "final_evidence_index.json"
_FINAL_MANIFEST_SCHEMA_VERSION = "calibration-redesign-v4-final-evaluation-manifest-v1"
_FINAL_INDEX_SCHEMA_VERSION = "calibration-redesign-v4-final-evidence-index-v1"
_FINAL_MANIFEST_ID = "v4-final-evaluation-manifest-freeze"
_FINAL_INDEX_ID = "v4-final-evidence-index-freeze"
_FIXTURE_SET_ID = "synthetic-calibration-redesign-v4"
_FIXTURE_SET_VERSION = "1.0.0"
_METHOD_CONSTITUTION_VERSION = "v4-method-and-evidence-constitution-v1"
_CALIBRATION_METHOD_ID = "regularized-isotonic-calibration-v4"
_EXPECTED_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(201, 237))
_EXPECTED_CASE_COUNT = 36
_EXPECTED_ASSET_COUNT = 72
_EXPECTED_OBSERVATION_COUNT = 144
_EXPECTED_POSITION_COUNT = 4
_EXPECTED_FAMILY_IDS = (
    "CRV4-FINAL-LIGHT-CAPACITY",
    "CRV4-FINAL-MODERATE-CAPACITY",
    "CRV4-FINAL-SATURATED-CAPACITY",
    "CRV4-FINAL-JAGGED-CAPACITY",
)
_EXPECTED_CASE_COUNT_BY_FAMILY = {family_id: 9 for family_id in _EXPECTED_FAMILY_IDS}


class CalibrationRedesignV4FinalManifestViolationCode(StrEnum):
    """Machine-readable reasons final held-out provenance cannot be trusted."""

    DESTINATION_ALREADY_EXISTS = "calibration_redesign_v4_final_manifest_destination_exists"
    DESTINATION_WRITE_ERROR = "calibration_redesign_v4_final_manifest_destination_write_error"
    PRE_FREEZE_ROOT_INVALID = "calibration_redesign_v4_final_manifest_pre_freeze_root_invalid"
    MANIFEST_READ_ERROR = "calibration_redesign_v4_final_manifest_read_error"
    MANIFEST_SCHEMA_ERROR = "calibration_redesign_v4_final_manifest_schema_error"
    INDEX_SCHEMA_ERROR = "calibration_redesign_v4_final_index_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = (
        "calibration_redesign_v4_final_manifest_registry_provenance_mismatch"
    )
    INVENTORY_MISMATCH = "calibration_redesign_v4_final_manifest_inventory_mismatch"
    ASSET_INTEGRITY_MISMATCH = "calibration_redesign_v4_final_manifest_asset_integrity_mismatch"
    AGGREGATE_MISMATCH = "calibration_redesign_v4_final_manifest_aggregate_mismatch"
    INDEX_INTEGRITY_MISMATCH = "calibration_redesign_v4_final_manifest_index_integrity_mismatch"


class CalibrationRedesignV4FinalManifestError(ValueError):
    """Raised when V4 final evidence cannot cross the manifest-freeze boundary."""

    def __init__(
        self,
        code: CalibrationRedesignV4FinalManifestViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV4FinalManifestAssetKind(StrEnum):
    """The two physically separated assets retained for every held-out case."""

    RUNTIME_INPUT = "runtime_input"
    EXPECTED_OUTCOME = "expected_outcome"


class CalibrationRedesignV4FinalManifestAsset(StrictContract):
    """One hash-addressed final-evaluation runtime or outcome file."""

    relative_path: str = Field(
        pattern=(r"^final_evaluation/(inputs|expected_outcomes)/cases/CRV4-2[0-9]{2}\.json$")
    )
    case_id: str = Field(pattern=r"^CRV4-2[0-9]{2}$")
    asset_kind: CalibrationRedesignV4FinalManifestAssetKind
    scenario_family_id: Literal[
        "CRV4-FINAL-LIGHT-CAPACITY",
        "CRV4-FINAL-MODERATE-CAPACITY",
        "CRV4-FINAL-SATURATED-CAPACITY",
        "CRV4-FINAL-JAGGED-CAPACITY",
    ]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_path_and_kind(self) -> CalibrationRedesignV4FinalManifestAsset:
        expected_parent = (
            "final_evaluation/inputs/cases"
            if self.asset_kind is CalibrationRedesignV4FinalManifestAssetKind.RUNTIME_INPUT
            else "final_evaluation/expected_outcomes/cases"
        )
        expected_path = f"{expected_parent}/{self.case_id}.json"
        if self.relative_path != expected_path:
            raise ValueError("final manifest asset path must match its case ID and kind")
        return self


class CalibrationRedesignV4FinalManifestCasePair(StrictContract):
    """The paired, separately stored final evidence files for one held-out case."""

    case_id: str = Field(pattern=r"^CRV4-2[0-9]{2}$")
    scenario_family_id: Literal[
        "CRV4-FINAL-LIGHT-CAPACITY",
        "CRV4-FINAL-MODERATE-CAPACITY",
        "CRV4-FINAL-SATURATED-CAPACITY",
        "CRV4-FINAL-JAGGED-CAPACITY",
    ]
    runtime_input_relative_path: str = Field(
        pattern=r"^final_evaluation/inputs/cases/CRV4-2[0-9]{2}\.json$"
    )
    expected_outcome_relative_path: str = Field(
        pattern=r"^final_evaluation/expected_outcomes/cases/CRV4-2[0-9]{2}\.json$"
    )
    runtime_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_outcome_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_paths(self) -> CalibrationRedesignV4FinalManifestCasePair:
        if self.runtime_input_relative_path != (
            f"final_evaluation/inputs/cases/{self.case_id}.json"
        ):
            raise ValueError("final runtime-input pair path does not match its case ID")
        if self.expected_outcome_relative_path != (
            f"final_evaluation/expected_outcomes/cases/{self.case_id}.json"
        ):
            raise ValueError("final expected-outcome pair path does not match its case ID")
        return self


class CalibrationRedesignV4FinalEvidenceIndexEntry(StrictContract):
    """Index-safe metadata for one final case, without post-hoc labels."""

    case_id: str = Field(pattern=r"^CRV4-2[0-9]{2}$")
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CRV4-FINAL-LIGHT-CAPACITY",
        "CRV4-FINAL-MODERATE-CAPACITY",
        "CRV4-FINAL-SATURATED-CAPACITY",
        "CRV4-FINAL-JAGGED-CAPACITY",
    ]
    workload_type: WorkloadType
    capacity_profile_id: str = Field(min_length=1, max_length=128)
    runtime_input_relative_path: str = Field(
        pattern=r"^final_evaluation/inputs/cases/CRV4-2[0-9]{2}\.json$"
    )
    expected_outcome_relative_path: str = Field(
        pattern=r"^final_evaluation/expected_outcomes/cases/CRV4-2[0-9]{2}\.json$"
    )

    @model_validator(mode="after")
    def validate_paths(self) -> CalibrationRedesignV4FinalEvidenceIndexEntry:
        if self.runtime_input_relative_path != (
            f"final_evaluation/inputs/cases/{self.case_id}.json"
        ):
            raise ValueError("final index runtime path must match its case ID")
        if self.expected_outcome_relative_path != (
            f"final_evaluation/expected_outcomes/cases/{self.case_id}.json"
        ):
            raise ValueError("final index outcome path must match its case ID")
        return self


class CalibrationRedesignV4FinalEvidenceIndex(StrictContract):
    """Deterministic label-free index for the frozen V4 held-out case inventory."""

    schema_version: Literal["calibration-redesign-v4-final-evidence-index-v1"] = (
        _FINAL_INDEX_SCHEMA_VERSION
    )
    index_id: Literal["v4-final-evidence-index-freeze"] = _FINAL_INDEX_ID
    index_scope: Literal["final_evaluation_only"] = "final_evaluation_only"
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"] = _FIXTURE_SET_ID
    fixture_set_version: Literal["1.0.0"] = _FIXTURE_SET_VERSION
    source_type: Literal[TraceSourceType.SYNTHETIC] = TraceSourceType.SYNTHETIC
    frozen_final_evaluation_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_ids: tuple[str, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT, max_length=_EXPECTED_CASE_COUNT
    )
    trace_ids: tuple[str, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT, max_length=_EXPECTED_CASE_COUNT
    )
    case_count: Literal[36] = _EXPECTED_CASE_COUNT
    observation_count: Literal[144] = _EXPECTED_OBSERVATION_COUNT
    candidate_positions_per_case: Literal[4] = _EXPECTED_POSITION_COUNT
    entries: tuple[CalibrationRedesignV4FinalEvidenceIndexEntry, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT,
        max_length=_EXPECTED_CASE_COUNT,
    )
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_index_shape(self) -> CalibrationRedesignV4FinalEvidenceIndex:
        if self.case_ids != _EXPECTED_CASE_IDS:
            raise ValueError("V4 final evidence index case IDs must be CRV4-201 through CRV4-236")
        if len(set(self.trace_ids)) != _EXPECTED_CASE_COUNT:
            raise ValueError("V4 final evidence index trace IDs must be unique")
        if tuple(entry.case_id for entry in self.entries) != _EXPECTED_CASE_IDS:
            raise ValueError("V4 final evidence index entries must be ordered by case ID")
        if tuple(entry.trace_id for entry in self.entries) != self.trace_ids:
            raise ValueError("V4 final evidence index trace IDs must match ordered entries")
        family_counts = Counter(entry.scenario_family_id for entry in self.entries)
        if dict(family_counts) != _EXPECTED_CASE_COUNT_BY_FAMILY:
            raise ValueError("V4 final evidence index must retain all four family allocations")
        for family_id in _EXPECTED_FAMILY_IDS:
            family_workloads = Counter(
                entry.workload_type.value
                for entry in self.entries
                if entry.scenario_family_id == family_id
            )
            if family_workloads != Counter({"structured_text": 3, "code": 3, "open_ended_chat": 3}):
                raise ValueError("V4 final evidence index must retain three workloads per family")
        return self


class CalibrationRedesignV4FinalEvaluationManifest(StrictContract):
    """Immutable, hash-addressed inventory for the V4 held-out corpus."""

    schema_version: Literal["calibration-redesign-v4-final-evaluation-manifest-v1"] = (
        _FINAL_MANIFEST_SCHEMA_VERSION
    )
    manifest_id: Literal["v4-final-evaluation-manifest-freeze"] = _FINAL_MANIFEST_ID
    manifest_scope: Literal["final_evaluation_only"] = "final_evaluation_only"
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"] = _FIXTURE_SET_ID
    fixture_set_version: Literal["1.0.0"] = _FIXTURE_SET_VERSION
    source_type: Literal[TraceSourceType.SYNTHETIC] = TraceSourceType.SYNTHETIC
    method_constitution_version: Literal["v4-method-and-evidence-constitution-v1"] = (
        _METHOD_CONSTITUTION_VERSION
    )
    calibration_method_id: Literal["regularized-isotonic-calibration-v4"] = _CALIBRATION_METHOD_ID
    frozen_final_evaluation_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evidence_index_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evidence_index_byte_count: int = Field(ge=1)
    case_ids: tuple[str, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT, max_length=_EXPECTED_CASE_COUNT
    )
    case_pair_count: Literal[36] = _EXPECTED_CASE_COUNT
    asset_count: Literal[72] = _EXPECTED_ASSET_COUNT
    observation_count: Literal[144] = _EXPECTED_OBSERVATION_COUNT
    candidate_positions_per_case: Literal[4] = _EXPECTED_POSITION_COUNT
    aggregate_byte_count: int = Field(ge=1)
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    assets: tuple[CalibrationRedesignV4FinalManifestAsset, ...] = Field(
        min_length=_EXPECTED_ASSET_COUNT,
        max_length=_EXPECTED_ASSET_COUNT,
    )
    case_pairs: tuple[CalibrationRedesignV4FinalManifestCasePair, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT,
        max_length=_EXPECTED_CASE_COUNT,
    )

    @model_validator(mode="after")
    def validate_manifest_shape(self) -> CalibrationRedesignV4FinalEvaluationManifest:
        if self.case_ids != _EXPECTED_CASE_IDS:
            raise ValueError("V4 final manifest case IDs must be CRV4-201 through CRV4-236")
        expected_paths = tuple(
            sorted(
                (
                    *(
                        f"final_evaluation/inputs/cases/{case_id}.json"
                        for case_id in _EXPECTED_CASE_IDS
                    ),
                    *(
                        f"final_evaluation/expected_outcomes/cases/{case_id}.json"
                        for case_id in _EXPECTED_CASE_IDS
                    ),
                )
            )
        )
        if tuple(asset.relative_path for asset in self.assets) != expected_paths:
            raise ValueError("V4 final manifest assets must be complete and sorted")
        if tuple(pair.case_id for pair in self.case_pairs) != _EXPECTED_CASE_IDS:
            raise ValueError("V4 final manifest case pairs must be complete and sorted")
        if self.aggregate_byte_count != sum(asset.byte_count for asset in self.assets):
            raise ValueError("V4 final manifest aggregate byte count must match assets")
        return self


class CalibrationRedesignV4FinalManifestedFixtureSet(StrictContract):
    """Verified V4 held-out cases exposed only after final inventory integrity checks."""

    manifest: CalibrationRedesignV4FinalEvaluationManifest
    index: CalibrationRedesignV4FinalEvidenceIndex
    cases: tuple[CalibrationRedesignV4FinalReplayCase, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT,
        max_length=_EXPECTED_CASE_COUNT,
    )

    @model_validator(mode="after")
    def validate_case_alignment(
        self,
    ) -> CalibrationRedesignV4FinalManifestedFixtureSet:
        case_ids = tuple(case.runtime_input.case_id for case in self.cases)
        trace_ids = tuple(case.runtime_input.trace_id for case in self.cases)
        observation_count = sum(len(case.runtime_input.contexts) for case in self.cases)
        if case_ids != _EXPECTED_CASE_IDS:
            raise ValueError("loaded final cases must match the frozen final inventory")
        if trace_ids != self.index.trace_ids:
            raise ValueError("loaded final trace IDs must match the frozen final index")
        if observation_count != self.manifest.observation_count:
            raise ValueError("loaded final observations must match the final manifest")
        return self


def freeze_calibration_redesign_v4_final_evaluation_manifest(
    root: Path,
) -> tuple[
    CalibrationRedesignV4FinalEvaluationManifest,
    CalibrationRedesignV4FinalEvidenceIndex,
]:
    """Freeze final assets, write both provenance files once, then advance the registry."""

    resolved_root = root.resolve()
    index_path = resolved_root / _FINAL_INDEX_FILENAME
    manifest_path = resolved_root / _FINAL_MANIFEST_FILENAME
    if index_path.exists() or manifest_path.exists():
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.DESTINATION_ALREADY_EXISTS,
            "V4 final evidence index and manifest are write-once and must not be rebuilt",
        )

    registry_payload, registry_bytes = _load_pre_freeze_registry_payload(resolved_root)
    index = _build_final_evidence_index(resolved_root, registry_bytes)
    index_bytes = _index_file_bytes(index)
    manifest = _build_final_manifest(resolved_root, registry_bytes, index_bytes)
    manifest_bytes = _manifest_file_bytes(manifest)

    try:
        _write_exclusive(index_path, index_bytes)
        _write_exclusive(manifest_path, manifest_bytes)
        _write_post_freeze_registry(
            resolved_root,
            registry_payload=registry_payload,
            pre_freeze_registry_bytes=registry_bytes,
            manifest_bytes=manifest_bytes,
            index_bytes=index_bytes,
        )
    except Exception:
        for path in (manifest_path, index_path):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    return manifest, index


def load_calibration_redesign_v4_final_manifested_fixture_set(
    root: Path,
) -> CalibrationRedesignV4FinalManifestedFixtureSet:
    """Load the final corpus only after manifest, index, and root integrity all verify."""

    resolved_root = root.resolve()
    try:
        registry = load_calibration_redesign_v4_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_final_evaluation_manifest_assets=True,
        )
    except CalibrationRedesignV4RegistryLoadError as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V4 final manifest root is not authorised: {error}",
        ) from error

    manifest_bytes = _read_bytes(resolved_root / _FINAL_MANIFEST_FILENAME)
    index_bytes = _read_bytes(resolved_root / _FINAL_INDEX_FILENAME)
    manifest = _load_manifest_bytes(manifest_bytes)
    index = _load_index_bytes(index_bytes)
    _verify_post_freeze_provenance(
        root=resolved_root,
        registry=registry,
        manifest=manifest,
        index=index,
        manifest_bytes=manifest_bytes,
        index_bytes=index_bytes,
    )

    cases = tuple(
        _load_final_case_without_registry(resolved_root, case_id) for case_id in _EXPECTED_CASE_IDS
    )
    _verify_manifest_against_cases_and_root(resolved_root, manifest, index, cases)
    return CalibrationRedesignV4FinalManifestedFixtureSet(
        manifest=manifest,
        index=index,
        cases=cases,
    )


def _load_pre_freeze_registry_payload(root: Path) -> tuple[dict[str, Any], bytes]:
    """Validate raw final-authoring metadata before the post-freeze registry model applies."""

    try:
        assert_calibration_redesign_v4_final_evaluation_fixture_root(root)
        registry_bytes = (root / "scenario_family_registry.json").read_bytes()
        payload: Any = json.loads(registry_bytes.decode("utf-8"))
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        CalibrationRedesignV4RegistryLoadError,
    ) as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V4 final manifest requires a complete pre-freeze final root: {error}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            "V4 pre-freeze registry must be a JSON object",
        )
    required_values = {
        "registry_status": "final_evaluation_fixtures_authored",
        "v4_final_evaluation_runtime_or_outcome_assets_authored": True,
        "v4_final_evaluation_manifest_authored": False,
        "next_authorized_artifact": "v4-final-evaluation-manifest-freeze",
    }
    for field_name, expected in required_values.items():
        if payload.get(field_name) != expected:
            raise CalibrationRedesignV4FinalManifestError(
                CalibrationRedesignV4FinalManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
                f"V4 pre-freeze registry must retain {field_name}={expected!r}",
            )
    return payload, registry_bytes


def _build_final_evidence_index(
    root: Path,
    pre_freeze_registry_bytes: bytes,
) -> CalibrationRedesignV4FinalEvidenceIndex:
    entries = tuple(
        _index_entry_from_case(_load_final_case_without_registry(root, case_id))
        for case_id in _EXPECTED_CASE_IDS
    )
    payload_without_aggregate: dict[str, Any] = {
        "schema_version": _FINAL_INDEX_SCHEMA_VERSION,
        "index_id": _FINAL_INDEX_ID,
        "index_scope": "final_evaluation_only",
        "fixture_set_id": _FIXTURE_SET_ID,
        "fixture_set_version": _FIXTURE_SET_VERSION,
        "source_type": TraceSourceType.SYNTHETIC.value,
        "frozen_final_evaluation_registry_sha256": _sha256_bytes(pre_freeze_registry_bytes),
        "case_ids": list(_EXPECTED_CASE_IDS),
        "trace_ids": [entry.trace_id for entry in entries],
        "case_count": _EXPECTED_CASE_COUNT,
        "observation_count": _EXPECTED_OBSERVATION_COUNT,
        "candidate_positions_per_case": _EXPECTED_POSITION_COUNT,
        "entries": [entry.model_dump(mode="json") for entry in entries],
    }
    return CalibrationRedesignV4FinalEvidenceIndex.model_validate(
        {
            **payload_without_aggregate,
            "aggregate_sha256": _sha256_bytes(_canonical_json_bytes(payload_without_aggregate)),
        }
    )


def _build_final_manifest(
    root: Path,
    pre_freeze_registry_bytes: bytes,
    index_bytes: bytes,
) -> CalibrationRedesignV4FinalEvaluationManifest:
    assets = _collect_final_asset_records(root)
    assets_by_path = {asset.relative_path: asset for asset in assets}
    cases = tuple(
        _load_final_case_without_registry(root, case_id) for case_id in _EXPECTED_CASE_IDS
    )
    families_by_case = {
        case.runtime_input.case_id: case.runtime_input.scenario_family_id for case in cases
    }
    case_pairs = tuple(
        CalibrationRedesignV4FinalManifestCasePair(
            case_id=case_id,
            scenario_family_id=families_by_case[case_id],
            runtime_input_relative_path=(f"final_evaluation/inputs/cases/{case_id}.json"),
            expected_outcome_relative_path=(
                f"final_evaluation/expected_outcomes/cases/{case_id}.json"
            ),
            runtime_input_sha256=assets_by_path[
                f"final_evaluation/inputs/cases/{case_id}.json"
            ].sha256,
            expected_outcome_sha256=assets_by_path[
                f"final_evaluation/expected_outcomes/cases/{case_id}.json"
            ].sha256,
        )
        for case_id in _EXPECTED_CASE_IDS
    )
    return CalibrationRedesignV4FinalEvaluationManifest(
        frozen_final_evaluation_registry_sha256=_sha256_bytes(pre_freeze_registry_bytes),
        final_evidence_index_sha256=_sha256_bytes(index_bytes),
        final_evidence_index_byte_count=len(index_bytes),
        case_ids=_EXPECTED_CASE_IDS,
        aggregate_byte_count=sum(asset.byte_count for asset in assets),
        aggregate_sha256=_aggregate_sha256(assets),
        assets=assets,
        case_pairs=case_pairs,
    )


def _load_final_case_without_registry(
    root: Path,
    case_id: str,
) -> CalibrationRedesignV4FinalReplayCase:
    runtime_payload = _read_json_asset(root / _FINAL_ROOT / "inputs" / "cases" / f"{case_id}.json")
    outcome_payload = _read_json_asset(
        root / _FINAL_ROOT / "expected_outcomes" / "cases" / f"{case_id}.json"
    )
    try:
        runtime = CalibrationRedesignV4FinalRuntimeInput.model_validate(runtime_payload)
        outcomes = CalibrationRedesignV4FinalExpectedOutcomes.model_validate(outcome_payload)
        replay_case = CalibrationRedesignV4FinalReplayCase(
            runtime_input=runtime,
            expected_outcomes=outcomes,
        )
    except ValidationError as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            f"V4 final case {case_id} does not satisfy its typed contract: {error}",
        ) from error
    _validate_case_membership_without_registry(replay_case)
    return replay_case


def _validate_case_membership_without_registry(
    replay_case: CalibrationRedesignV4FinalReplayCase,
) -> None:
    runtime = replay_case.runtime_input
    expected_family_by_case = {
        **{f"CRV4-{number:03d}": "CRV4-FINAL-LIGHT-CAPACITY" for number in range(201, 210)},
        **{f"CRV4-{number:03d}": "CRV4-FINAL-MODERATE-CAPACITY" for number in range(210, 219)},
        **{f"CRV4-{number:03d}": "CRV4-FINAL-SATURATED-CAPACITY" for number in range(219, 228)},
        **{f"CRV4-{number:03d}": "CRV4-FINAL-JAGGED-CAPACITY" for number in range(228, 237)},
    }
    if runtime.case_id not in expected_family_by_case:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            "V4 final manifest may only index CRV4-201 through CRV4-236",
        )
    if runtime.scenario_family_id != expected_family_by_case[runtime.case_id]:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            "V4 final case does not match its fixed family reservation",
        )


def _index_entry_from_case(
    replay_case: CalibrationRedesignV4FinalReplayCase,
) -> CalibrationRedesignV4FinalEvidenceIndexEntry:
    runtime = replay_case.runtime_input
    first_context = runtime.contexts[0]
    if any(
        context.workload_type is not first_context.workload_type for context in runtime.contexts
    ):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            "V4 final case workload type must remain stable across positions",
        )
    if any(
        context.capacity_snapshot.profile_id != first_context.capacity_snapshot.profile_id
        for context in runtime.contexts
    ):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            "V4 final case capacity profile ID must remain stable across positions",
        )
    return CalibrationRedesignV4FinalEvidenceIndexEntry(
        case_id=runtime.case_id,
        trace_id=runtime.trace_id,
        scenario_family_id=runtime.scenario_family_id,
        workload_type=first_context.workload_type,
        capacity_profile_id=first_context.capacity_snapshot.profile_id,
        runtime_input_relative_path=(f"final_evaluation/inputs/cases/{runtime.case_id}.json"),
        expected_outcome_relative_path=(
            f"final_evaluation/expected_outcomes/cases/{runtime.case_id}.json"
        ),
    )


def _collect_final_asset_records(
    root: Path,
) -> tuple[CalibrationRedesignV4FinalManifestAsset, ...]:
    records: list[CalibrationRedesignV4FinalManifestAsset] = []
    for case_id in _EXPECTED_CASE_IDS:
        replay_case = _load_final_case_without_registry(root, case_id)
        family_id = replay_case.runtime_input.scenario_family_id
        records.append(
            _asset_record(
                root,
                relative_path=f"final_evaluation/inputs/cases/{case_id}.json",
                case_id=case_id,
                asset_kind=CalibrationRedesignV4FinalManifestAssetKind.RUNTIME_INPUT,
                scenario_family_id=family_id,
            )
        )
        records.append(
            _asset_record(
                root,
                relative_path=f"final_evaluation/expected_outcomes/cases/{case_id}.json",
                case_id=case_id,
                asset_kind=CalibrationRedesignV4FinalManifestAssetKind.EXPECTED_OUTCOME,
                scenario_family_id=family_id,
            )
        )
    return tuple(sorted(records, key=lambda item: item.relative_path))


def _asset_record(
    root: Path,
    *,
    relative_path: str,
    case_id: str,
    asset_kind: CalibrationRedesignV4FinalManifestAssetKind,
    scenario_family_id: str,
) -> CalibrationRedesignV4FinalManifestAsset:
    raw_bytes = _read_bytes(root / relative_path)
    return CalibrationRedesignV4FinalManifestAsset(
        relative_path=relative_path,
        case_id=case_id,
        asset_kind=asset_kind,
        scenario_family_id=scenario_family_id,
        sha256=_sha256_bytes(raw_bytes),
        byte_count=len(raw_bytes),
    )


def _write_post_freeze_registry(
    root: Path,
    *,
    registry_payload: dict[str, Any],
    pre_freeze_registry_bytes: bytes,
    manifest_bytes: bytes,
    index_bytes: bytes,
) -> None:
    payload = dict(registry_payload)
    payload.update(
        {
            "registry_status": "final_evaluation_manifest_frozen",
            "v4_final_evaluation_manifest_authored": True,
            "frozen_final_evaluation_registry_sha256": _sha256_bytes(pre_freeze_registry_bytes),
            "frozen_final_evaluation_manifest_sha256": _sha256_bytes(manifest_bytes),
            "final_evidence_index_sha256": _sha256_bytes(index_bytes),
            "next_authorized_artifact": "v4-final-heldout-calibration-assessment",
        }
    )
    obsolete_exclusions = {
        "No V4 final-evaluation manifest is present.",
        "No V4 final-evidence index or held-out result is present.",
        "V4 final-evaluation fixtures remain quarantined until their manifest is frozen.",
    }
    retained_exclusions = [
        item for item in payload.get("explicit_exclusions", []) if item not in obsolete_exclusions
    ]
    for item in (
        "No V4 final-evaluation held-out assessment or result is present.",
        "V4 final-evaluation manifest and final-evidence index are frozen provenance boundaries.",
        (
            "V4 final-evaluation manifest freeze does not author an "
            "assessment, baseline, or policy result."
        ),
    ):
        if item not in retained_exclusions:
            retained_exclusions.append(item)
    payload["explicit_exclusions"] = retained_exclusions
    try:
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V4 post-freeze registry does not satisfy the typed contract: {error}",
        ) from error
    registry_path = root / "scenario_family_registry.json"
    temporary_path = registry_path.with_name("scenario_family_registry.json.freeze-tmp")
    try:
        with temporary_path.open("xb") as file_handle:
            file_handle.write(_pretty_json_bytes(payload))
        temporary_path.replace(registry_path)
    except OSError as error:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.DESTINATION_WRITE_ERROR,
            f"unable to advance V4 final registry after provenance freeze: {error}",
        ) from error


def _verify_post_freeze_provenance(
    *,
    root: Path,
    registry: CalibrationRedesignV4ScenarioFamilyRegistry,
    manifest: CalibrationRedesignV4FinalEvaluationManifest,
    index: CalibrationRedesignV4FinalEvidenceIndex,
    manifest_bytes: bytes,
    index_bytes: bytes,
) -> None:
    if registry.frozen_final_evaluation_registry_sha256 != (
        manifest.frozen_final_evaluation_registry_sha256
    ):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 active registry does not carry forward the frozen final registry SHA-256",
        )
    if registry.frozen_final_evaluation_registry_sha256 != (
        index.frozen_final_evaluation_registry_sha256
    ):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 final evidence index does not carry forward the frozen final registry SHA-256",
        )
    if registry.frozen_final_evaluation_manifest_sha256 != _sha256_bytes(manifest_bytes):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 active registry does not carry forward the final manifest SHA-256",
        )
    if registry.final_evidence_index_sha256 != _sha256_bytes(index_bytes):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 active registry does not carry forward the final evidence index SHA-256",
        )
    if manifest.final_evidence_index_sha256 != _sha256_bytes(index_bytes):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INDEX_INTEGRITY_MISMATCH,
            "V4 final manifest does not bind the final evidence index bytes",
        )
    if manifest.final_evidence_index_byte_count != len(index_bytes):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INDEX_INTEGRITY_MISMATCH,
            "V4 final manifest does not retain the final evidence index byte count",
        )
    index_payload = index.model_dump(mode="json")
    actual_index_aggregate = _sha256_bytes(
        _canonical_json_bytes(
            {key: value for key, value in index_payload.items() if key != "aggregate_sha256"}
        )
    )
    if index.aggregate_sha256 != actual_index_aggregate:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.AGGREGATE_MISMATCH,
            "V4 final evidence index aggregate SHA-256 does not match its retained content",
        )


def _verify_manifest_against_cases_and_root(
    root: Path,
    manifest: CalibrationRedesignV4FinalEvaluationManifest,
    index: CalibrationRedesignV4FinalEvidenceIndex,
    cases: tuple[CalibrationRedesignV4FinalReplayCase, ...],
) -> None:
    actual_assets = _collect_final_asset_records(root)
    if manifest.assets != actual_assets:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.ASSET_INTEGRITY_MISMATCH,
            "V4 final manifest asset hashes or byte counts do not match the fixture root",
        )
    if manifest.aggregate_byte_count != sum(asset.byte_count for asset in actual_assets):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            "V4 final manifest aggregate byte count does not match the fixture root",
        )
    if manifest.aggregate_sha256 != _aggregate_sha256(actual_assets):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.AGGREGATE_MISMATCH,
            "V4 final manifest aggregate SHA-256 does not match the fixture root",
        )
    expected_pairs = _expected_case_pairs(actual_assets, cases)
    if manifest.case_pairs != expected_pairs:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            "V4 final manifest case-pair inventory does not match the fixture root",
        )
    expected_index_entries = tuple(_index_entry_from_case(case) for case in cases)
    if index.entries != expected_index_entries:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INDEX_INTEGRITY_MISMATCH,
            "V4 final evidence index does not match the final case inventory",
        )


def _expected_case_pairs(
    assets: tuple[CalibrationRedesignV4FinalManifestAsset, ...],
    cases: tuple[CalibrationRedesignV4FinalReplayCase, ...],
) -> tuple[CalibrationRedesignV4FinalManifestCasePair, ...]:
    assets_by_path = {asset.relative_path: asset for asset in assets}
    family_by_case = {
        case.runtime_input.case_id: case.runtime_input.scenario_family_id for case in cases
    }
    return tuple(
        CalibrationRedesignV4FinalManifestCasePair(
            case_id=case_id,
            scenario_family_id=family_by_case[case_id],
            runtime_input_relative_path=(f"final_evaluation/inputs/cases/{case_id}.json"),
            expected_outcome_relative_path=(
                f"final_evaluation/expected_outcomes/cases/{case_id}.json"
            ),
            runtime_input_sha256=assets_by_path[
                f"final_evaluation/inputs/cases/{case_id}.json"
            ].sha256,
            expected_outcome_sha256=assets_by_path[
                f"final_evaluation/expected_outcomes/cases/{case_id}.json"
            ].sha256,
        )
        for case_id in _EXPECTED_CASE_IDS
    )


def _load_manifest_bytes(
    raw_bytes: bytes,
) -> CalibrationRedesignV4FinalEvaluationManifest:
    try:
        payload: Any = json.loads(raw_bytes.decode("utf-8"))
        return CalibrationRedesignV4FinalEvaluationManifest.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V4 final evaluation manifest is invalid: {error}",
        ) from error


def _load_index_bytes(raw_bytes: bytes) -> CalibrationRedesignV4FinalEvidenceIndex:
    try:
        payload: Any = json.loads(raw_bytes.decode("utf-8"))
        return CalibrationRedesignV4FinalEvidenceIndex.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INDEX_SCHEMA_ERROR,
            f"V4 final evidence index is invalid: {error}",
        ) from error


def _read_json_asset(path: Path) -> Mapping[str, Any]:
    try:
        payload: Any = json.loads(_read_bytes(path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            f"V4 final asset is not valid JSON: {path.name}: {error}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.INVENTORY_MISMATCH,
            f"V4 final asset must be a JSON object: {path.name}",
        )
    return payload


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.MANIFEST_READ_ERROR,
            f"unable to read V4 final provenance input {path}: {error}",
        ) from error


def _write_exclusive(path: Path, payload: bytes) -> None:
    try:
        with path.open("xb") as file_handle:
            file_handle.write(payload)
    except FileExistsError as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.DESTINATION_ALREADY_EXISTS,
            f"V4 final provenance destination already exists: {path.name}",
        ) from error
    except OSError as error:
        raise CalibrationRedesignV4FinalManifestError(
            CalibrationRedesignV4FinalManifestViolationCode.DESTINATION_WRITE_ERROR,
            f"unable to write V4 final provenance file {path.name}: {error}",
        ) from error


def _manifest_file_bytes(
    manifest: CalibrationRedesignV4FinalEvaluationManifest,
) -> bytes:
    return _pretty_json_bytes(manifest.model_dump(mode="json"))


def _index_file_bytes(index: CalibrationRedesignV4FinalEvidenceIndex) -> bytes:
    return _pretty_json_bytes(index.model_dump(mode="json"))


def _pretty_json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _aggregate_sha256(
    assets: tuple[CalibrationRedesignV4FinalManifestAsset, ...],
) -> str:
    return _sha256_bytes(_canonical_json_bytes([asset.model_dump(mode="json") for asset in assets]))


def _sha256_bytes(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()
