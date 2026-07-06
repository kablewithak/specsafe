"""Immutable V3 final-evaluation manifest generation and verification.

The manifest freezes the complete 24-case V3 held-out corpus after all four capacity
families are authored. It validates bytes, provenance, split isolation, and case alignment
only. It never fits a calibrator, transforms confidence, calculates a score, invokes a
policy, or makes a promotion decision.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import StrictContract, TraceDataRole, TraceSourceType, TraceSplit
from specsafe.traces.calibration_redesign_v3 import (
    CalibrationRedesignV3RegistryLoadError,
    assert_calibration_redesign_v3_calibration_manifest_fixture_root,
)
from specsafe.traces.calibration_redesign_v3_cases import CalibrationRedesignV3ReplayCase
from specsafe.traces.calibration_redesign_v3_final_evidence import (
    CalibrationRedesignV3FinalEvidenceIndex,
    CalibrationRedesignV3FinalEvidenceLoadError,
    load_calibration_redesign_v3_final_evaluation_replay_case,
    load_calibration_redesign_v3_final_evidence_index,
)

_MANIFEST_FILENAME = "final_evaluation_manifest.json"
_INDEX_FILENAME = "final_evidence_index.json"
_FINAL_ROOT = "final_evaluation"
_EXPECTED_CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(201, 225))
_EXPECTED_FAMILY_CASE_COUNTS = {
    "CRV3-FINAL-JAGGED-CAPACITY": 6,
    "CRV3-FINAL-LIGHT-CAPACITY": 6,
    "CRV3-FINAL-MODERATE-CAPACITY": 6,
    "CRV3-FINAL-SATURATED-CAPACITY": 6,
}


class CalibrationRedesignV3FinalManifestViolationCode(StrEnum):
    """Machine-readable reasons the frozen V3 final corpus cannot be trusted."""

    MANIFEST_SCHEMA_ERROR = "calibration_redesign_v3_final_manifest_schema_error"
    MANIFEST_INTEGRITY_MISMATCH = "calibration_redesign_v3_final_manifest_integrity_mismatch"
    MANIFEST_PROVENANCE_MISMATCH = "calibration_redesign_v3_final_manifest_provenance_mismatch"
    FINAL_EVALUATION_BOUNDARY_VIOLATION = (
        "calibration_redesign_v3_final_manifest_boundary_violation"
    )


class CalibrationRedesignV3FinalManifestLoadError(ValueError):
    """Typed error raised when V3 final-evaluation evidence cannot be trusted."""

    def __init__(self, code: CalibrationRedesignV3FinalManifestViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV3FinalManifestArtifactKind(StrEnum):
    """The two physically separate assets required for every held-out V3 case."""

    RUNTIME_INPUT = "runtime_input"
    EXPECTED_OUTCOMES = "expected_outcomes"


class CalibrationRedesignV3FinalManifestEntry(StrictContract):
    """Hash-addressed inventory entry for one frozen V3 held-out evidence asset."""

    artifact_kind: CalibrationRedesignV3FinalManifestArtifactKind
    relative_path: str = Field(min_length=1, max_length=300)
    case_id: str = Field(pattern=r"^CRV3-2[0-9]{2}$")
    scenario_family_id: Literal[
        "CRV3-FINAL-LIGHT-CAPACITY",
        "CRV3-FINAL-MODERATE-CAPACITY",
        "CRV3-FINAL-SATURATED-CAPACITY",
        "CRV3-FINAL-JAGGED-CAPACITY",
    ]
    split: Literal[TraceSplit.FINAL_EVALUATION]
    data_role: Literal[TraceDataRole.HELD_OUT_EVALUATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_asset_path(self) -> CalibrationRedesignV3FinalManifestEntry:
        expected_directory = {
            CalibrationRedesignV3FinalManifestArtifactKind.RUNTIME_INPUT: (
                "final_evaluation/inputs/cases"
            ),
            CalibrationRedesignV3FinalManifestArtifactKind.EXPECTED_OUTCOMES: (
                "final_evaluation/expected_outcomes/cases"
            ),
        }[self.artifact_kind]
        expected_path = f"{expected_directory}/{self.case_id}.json"
        if self.relative_path.replace("\\", "/") != expected_path:
            raise ValueError("manifest entry path must match its case ID and artifact kind")
        return self


class CalibrationRedesignV3FinalSplitCount(StrictContract):
    """The only split permitted in the V3 final-evaluation manifest."""

    split: Literal[TraceSplit.FINAL_EVALUATION]
    case_count: Literal[24]


class CalibrationRedesignV3FinalScenarioFamilyCount(StrictContract):
    """Declared held-out case count for one finalized V3 final family."""

    scenario_family_id: Literal[
        "CRV3-FINAL-LIGHT-CAPACITY",
        "CRV3-FINAL-MODERATE-CAPACITY",
        "CRV3-FINAL-SATURATED-CAPACITY",
        "CRV3-FINAL-JAGGED-CAPACITY",
    ]
    case_count: Literal[6]


class CalibrationRedesignV3FinalEvaluationFixtureManifest(StrictContract):
    """Immutable, hash-addressed inventory for the V3 held-out evaluation corpus."""

    schema_version: Literal["calibration-redesign-v3-final-evaluation-manifest-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v3"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    final_evidence_index_path: Literal["final_evidence_index.json"]
    final_evidence_index_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evidence_index_byte_count: int = Field(gt=0)
    case_count: Literal[24]
    observation_count: Literal[96]
    candidate_positions_per_case: Literal[4]
    split_counts: tuple[CalibrationRedesignV3FinalSplitCount, ...] = Field(
        min_length=1, max_length=1
    )
    scenario_family_counts: tuple[CalibrationRedesignV3FinalScenarioFamilyCount, ...] = Field(
        min_length=4, max_length=4
    )
    entries: tuple[CalibrationRedesignV3FinalManifestEntry, ...] = Field(
        min_length=48, max_length=48
    )
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_inventory_shape(self) -> CalibrationRedesignV3FinalEvaluationFixtureManifest:
        entry_keys = {(entry.case_id, entry.artifact_kind) for entry in self.entries}
        if len(entry_keys) != len(self.entries):
            raise ValueError("manifest entries must not repeat a case_id/artifact_kind pair")
        if len(self.entries) != 48:
            raise ValueError("V3 final manifest must contain exactly 48 paired asset entries")

        case_ids = {entry.case_id for entry in self.entries}
        if case_ids != set(_EXPECTED_CASE_IDS):
            raise ValueError("V3 final manifest must inventory exactly CRV3-201 through CRV3-224")
        required_kinds = {
            CalibrationRedesignV3FinalManifestArtifactKind.RUNTIME_INPUT,
            CalibrationRedesignV3FinalManifestArtifactKind.EXPECTED_OUTCOMES,
        }
        for case_id in case_ids:
            kinds = {entry.artifact_kind for entry in self.entries if entry.case_id == case_id}
            if kinds != required_kinds:
                raise ValueError("each V3 final case needs one runtime and one outcome asset")

        if self.split_counts != (
            CalibrationRedesignV3FinalSplitCount(
                split=TraceSplit.FINAL_EVALUATION,
                case_count=24,
            ),
        ):
            raise ValueError("V3 final manifest must declare exactly one final-evaluation split")

        family_counts = {
            item.scenario_family_id: item.case_count for item in self.scenario_family_counts
        }
        if family_counts != _EXPECTED_FAMILY_CASE_COUNTS:
            raise ValueError("scenario_family_counts must match all four V3 capacity families")

        actual_family_counts: dict[str, int] = defaultdict(int)
        for case_id in case_ids:
            family_ids = {
                entry.scenario_family_id for entry in self.entries if entry.case_id == case_id
            }
            if len(family_ids) != 1:
                raise ValueError("runtime and outcome entries must agree on scenario family")
            actual_family_counts[family_ids.pop()] += 1
        if dict(actual_family_counts) != _EXPECTED_FAMILY_CASE_COUNTS:
            raise ValueError("manifest case inventory must match fixed V3 family allocation")
        return self


class CalibrationRedesignV3FinalManifestedFixtureSet(StrictContract):
    """Verified V3 final cases loaded only after manifest integrity checks."""

    manifest: CalibrationRedesignV3FinalEvaluationFixtureManifest
    cases: tuple[CalibrationRedesignV3ReplayCase, ...] = Field(min_length=24, max_length=24)

    @model_validator(mode="after")
    def validate_case_identity(self) -> CalibrationRedesignV3FinalManifestedFixtureSet:
        case_ids = {case.runtime_input.case_id for case in self.cases}
        if case_ids != set(_EXPECTED_CASE_IDS):
            raise ValueError("loaded V3 final cases must match the frozen final inventory")
        observation_count = sum(len(case.runtime_input.contexts) for case in self.cases)
        if observation_count != self.manifest.observation_count:
            raise ValueError("loaded V3 final observations must match the manifest")
        return self


def build_calibration_redesign_v3_final_evaluation_manifest(fixture_root: Path) -> Path:
    """Freeze the complete V3 final corpus into deterministic JSON bytes without scoring it."""

    root = fixture_root.resolve()
    _assert_final_manifest_root(root)
    index = _load_final_evidence_index(root)
    runtime_paths = _discover_final_case_assets(root / _FINAL_ROOT / "inputs" / "cases")
    outcome_paths = _discover_final_case_assets(root / _FINAL_ROOT / "expected_outcomes" / "cases")
    expected_case_ids = _expected_final_case_ids(index)
    _validate_case_inventory(runtime_paths, outcome_paths, expected_case_ids)

    entries: list[CalibrationRedesignV3FinalManifestEntry] = []
    family_counts: dict[str, int] = defaultdict(int)
    observation_count = 0
    for case_id in sorted(expected_case_ids):
        replay_case = _load_replay_case(root, case_id)
        runtime = replay_case.runtime_input
        _validate_final_case(replay_case, index)
        entries.extend(
            (
                _manifest_entry(
                    root,
                    runtime_paths[case_id],
                    CalibrationRedesignV3FinalManifestArtifactKind.RUNTIME_INPUT,
                    replay_case,
                ),
                _manifest_entry(
                    root,
                    outcome_paths[case_id],
                    CalibrationRedesignV3FinalManifestArtifactKind.EXPECTED_OUTCOMES,
                    replay_case,
                ),
            )
        )
        family_counts[runtime.scenario_family_id] += 1
        observation_count += len(runtime.contexts)

    index_path = root / _INDEX_FILENAME
    index_bytes = _read_bytes(index_path)
    manifest_without_aggregate: dict[str, Any] = {
        "schema_version": "calibration-redesign-v3-final-evaluation-manifest-v1",
        "fixture_set_id": index.fixture_set_id,
        "fixture_set_version": index.fixture_set_version,
        "source_type": TraceSourceType.SYNTHETIC.value,
        "final_evidence_index_path": _INDEX_FILENAME,
        "final_evidence_index_sha256": _sha256(index_bytes),
        "final_evidence_index_byte_count": len(index_bytes),
        "case_count": len(expected_case_ids),
        "observation_count": observation_count,
        "candidate_positions_per_case": index.candidate_positions_per_case,
        "split_counts": [
            {
                "split": TraceSplit.FINAL_EVALUATION.value,
                "case_count": len(expected_case_ids),
            }
        ],
        "scenario_family_counts": [
            {"scenario_family_id": family_id, "case_count": family_counts[family_id]}
            for family_id in sorted(family_counts)
        ],
        "entries": [
            entry.model_dump(mode="json") for entry in sorted(entries, key=_entry_sort_key)
        ],
    }
    manifest_payload = {
        **manifest_without_aggregate,
        "aggregate_sha256": _aggregate_sha256(manifest_without_aggregate),
    }
    try:
        CalibrationRedesignV3FinalEvaluationFixtureManifest.model_validate(manifest_payload)
    except ValidationError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"generated V3 final manifest schema validation failed: {error}",
        ) from error

    manifest_path = root / _MANIFEST_FILENAME
    manifest_path.write_bytes(_pretty_json_bytes(manifest_payload))
    return manifest_path


def load_calibration_redesign_v3_final_evaluation_manifested_fixture_set(
    fixture_root: Path,
) -> CalibrationRedesignV3FinalManifestedFixtureSet:
    """Load the frozen V3 final corpus without fitting, scoring, or policy execution."""

    root = fixture_root.resolve()
    _assert_final_manifest_root(root)
    manifest_path = root / _MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 final-evaluation manifest is missing",
        )
    manifest_payload = _read_json(manifest_path)
    try:
        manifest = CalibrationRedesignV3FinalEvaluationFixtureManifest.model_validate(
            manifest_payload
        )
    except ValidationError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V3 final manifest schema validation failed: {error}",
        ) from error

    aggregate_payload = dict(manifest_payload)
    declared_aggregate = aggregate_payload.pop("aggregate_sha256", None)
    if declared_aggregate != _aggregate_sha256(aggregate_payload):
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "V3 final manifest aggregate hash does not match its inventory",
        )

    index_path = _resolve_path(root, manifest.final_evidence_index_path)
    index_bytes = _read_bytes(index_path)
    if (
        _sha256(index_bytes) != manifest.final_evidence_index_sha256
        or len(index_bytes) != manifest.final_evidence_index_byte_count
    ):
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "V3 final-evidence index does not match final-manifest provenance",
        )
    index = _load_final_evidence_index(root)
    _validate_manifest_index_identity(manifest, index)

    runtime_paths = _discover_final_case_assets(root / _FINAL_ROOT / "inputs" / "cases")
    outcome_paths = _discover_final_case_assets(root / _FINAL_ROOT / "expected_outcomes" / "cases")
    expected_case_ids = _expected_final_case_ids(index)
    _validate_case_inventory(runtime_paths, outcome_paths, expected_case_ids)

    entries_by_case: dict[
        str,
        dict[
            CalibrationRedesignV3FinalManifestArtifactKind,
            CalibrationRedesignV3FinalManifestEntry,
        ],
    ] = defaultdict(dict)
    for entry in manifest.entries:
        _verify_entry_bytes(root, entry)
        entries_by_case[entry.case_id][entry.artifact_kind] = entry
    if set(entries_by_case) != expected_case_ids:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 final manifest case IDs must match the full held-out reservation",
        )

    cases: list[CalibrationRedesignV3ReplayCase] = []
    for case_id in sorted(expected_case_ids):
        entries = entries_by_case[case_id]
        if (
            entries.get(CalibrationRedesignV3FinalManifestArtifactKind.RUNTIME_INPUT) is None
            or entries.get(CalibrationRedesignV3FinalManifestArtifactKind.EXPECTED_OUTCOMES) is None
        ):
            raise CalibrationRedesignV3FinalManifestLoadError(
                CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"V3 final manifest is missing one asset entry for {case_id}",
            )
        replay_case = _load_replay_case(root, case_id)
        _validate_final_case(replay_case, index)
        if (
            replay_case.runtime_input.scenario_family_id
            != entries[
                CalibrationRedesignV3FinalManifestArtifactKind.RUNTIME_INPUT
            ].scenario_family_id
        ):
            raise CalibrationRedesignV3FinalManifestLoadError(
                CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"V3 final manifest family does not match runtime case for {case_id}",
            )
        cases.append(replay_case)

    try:
        return CalibrationRedesignV3FinalManifestedFixtureSet(manifest=manifest, cases=tuple(cases))
    except ValidationError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"loaded V3 final fixture set does not match its manifest: {error}",
        ) from error


def _assert_final_manifest_root(root: Path) -> None:
    try:
        assert_calibration_redesign_v3_calibration_manifest_fixture_root(root)
    except CalibrationRedesignV3RegistryLoadError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.FINAL_EVALUATION_BOUNDARY_VIOLATION,
            f"V3 final-manifest root is not authorized: {error}",
        ) from error


def _load_final_evidence_index(root: Path) -> CalibrationRedesignV3FinalEvidenceIndex:
    try:
        return load_calibration_redesign_v3_final_evidence_index(root)
    except CalibrationRedesignV3FinalEvidenceLoadError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"unable to load V3 final-evidence index for final manifest: {error}",
        ) from error


def _load_replay_case(root: Path, case_id: str) -> CalibrationRedesignV3ReplayCase:
    try:
        return load_calibration_redesign_v3_final_evaluation_replay_case(root, case_id)
    except CalibrationRedesignV3FinalEvidenceLoadError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 final case {case_id} cannot be loaded: {error}",
        ) from error


def _discover_final_case_assets(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 final asset directory is missing: {directory}",
        )
    assets: dict[str, Path] = {}
    for path in sorted(directory.glob("CRV3-2*.json")):
        payload = _read_json(path)
        if (
            payload.get("split") != TraceSplit.FINAL_EVALUATION.value
            or payload.get("data_role") != TraceDataRole.HELD_OUT_EVALUATION.value
        ):
            raise CalibrationRedesignV3FinalManifestLoadError(
                CalibrationRedesignV3FinalManifestViolationCode.FINAL_EVALUATION_BOUNDARY_VIOLATION,
                f"non-final asset is prohibited in the V3 final manifest: {path.name}",
            )
        case_id = payload.get("case_id")
        if not isinstance(case_id, str) or path.name != f"{case_id}.json":
            raise CalibrationRedesignV3FinalManifestLoadError(
                CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"V3 final asset filename and case_id must agree: {path.name}",
            )
        if case_id in assets:
            raise CalibrationRedesignV3FinalManifestLoadError(
                CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"duplicate V3 final case ID in one asset directory: {case_id}",
            )
        assets[case_id] = path
    if not assets:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 final asset directory contains no case JSON: {directory}",
        )
    return assets


def _expected_final_case_ids(index: CalibrationRedesignV3FinalEvidenceIndex) -> set[str]:
    case_ids = {case_id for family in index.families for case_id in family.authored_case_ids}
    if case_ids != set(_EXPECTED_CASE_IDS):
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 final-evidence index must author exactly CRV3-201 through CRV3-224",
        )
    return case_ids


def _validate_case_inventory(
    runtime_paths: dict[str, Path],
    outcome_paths: dict[str, Path],
    expected_case_ids: set[str],
) -> None:
    if set(runtime_paths) != set(outcome_paths):
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 final runtime and expected-outcome case IDs must match",
        )
    if set(runtime_paths) != expected_case_ids:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 final assets must match exactly the finalized held-out reservation",
        )


def _validate_final_case(
    replay_case: CalibrationRedesignV3ReplayCase,
    index: CalibrationRedesignV3FinalEvidenceIndex,
) -> None:
    runtime = replay_case.runtime_input
    if (
        runtime.split is not TraceSplit.FINAL_EVALUATION
        or runtime.data_role is not TraceDataRole.HELD_OUT_EVALUATION
    ):
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.FINAL_EVALUATION_BOUNDARY_VIOLATION,
            f"V3 manifest case {runtime.case_id} is not held-out final-evaluation evidence",
        )
    family = next(
        (item for item in index.families if item.scenario_family_id == runtime.scenario_family_id),
        None,
    )
    if family is None or runtime.case_id not in family.authored_case_ids:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 manifest case {runtime.case_id} is not authorised by final-evidence index",
        )
    if any(
        context.capacity_snapshot.profile_id != family.capacity_profile_id
        for context in runtime.contexts
    ):
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 manifest case {runtime.case_id} does not match its capacity family",
        )


def _manifest_entry(
    root: Path,
    path: Path,
    artifact_kind: CalibrationRedesignV3FinalManifestArtifactKind,
    replay_case: CalibrationRedesignV3ReplayCase,
) -> CalibrationRedesignV3FinalManifestEntry:
    raw_bytes = _read_bytes(path)
    runtime = replay_case.runtime_input
    return CalibrationRedesignV3FinalManifestEntry(
        artifact_kind=artifact_kind,
        relative_path=path.resolve().relative_to(root).as_posix(),
        case_id=runtime.case_id,
        scenario_family_id=runtime.scenario_family_id,
        split=runtime.split,
        data_role=runtime.data_role,
        source_type=runtime.source_type,
        sha256=_sha256(raw_bytes),
        byte_count=len(raw_bytes),
    )


def _validate_manifest_index_identity(
    manifest: CalibrationRedesignV3FinalEvaluationFixtureManifest,
    index: CalibrationRedesignV3FinalEvidenceIndex,
) -> None:
    if (
        manifest.fixture_set_id != index.fixture_set_id
        or manifest.fixture_set_version != index.fixture_set_version
        or manifest.source_type is not index.source_type
        or manifest.candidate_positions_per_case != index.candidate_positions_per_case
        or manifest.case_count != index.final_evaluation_case_count
        or manifest.observation_count != index.final_evaluation_observation_count
    ):
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "V3 final manifest disagrees with final-evidence index identity",
        )


def _verify_entry_bytes(root: Path, entry: CalibrationRedesignV3FinalManifestEntry) -> None:
    raw_bytes = _read_bytes(_resolve_path(root, entry.relative_path))
    if _sha256(raw_bytes) != entry.sha256 or len(raw_bytes) != entry.byte_count:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            f"V3 final manifest entry does not match current bytes: {entry.relative_path}",
        )


def _resolve_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"V3 final manifest path escapes fixture root: {relative_path}",
        ) from error
    return candidate


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_bytes(path))
    except json.JSONDecodeError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"invalid JSON in {path.name}: {error.msg}",
        ) from error
    if not isinstance(payload, dict):
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V3 final manifest asset must contain a JSON object: {path.name}",
        )
    return payload


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV3FinalManifestLoadError(
            CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"unable to read V3 final fixture asset: {path}",
        ) from error


def _entry_sort_key(entry: CalibrationRedesignV3FinalManifestEntry) -> tuple[str, str]:
    return (entry.case_id, entry.artifact_kind.value)


def _sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def _aggregate_sha256(payload: dict[str, Any]) -> str:
    return _sha256(_canonical_json_bytes(payload))


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _pretty_json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")
