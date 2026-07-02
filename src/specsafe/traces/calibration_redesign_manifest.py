"""Immutable manifest generation and verification for fresh calibration fixtures."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts import TraceDataRole, TraceSourceType, TraceSplit
from specsafe.contracts.models import StrictContract
from specsafe.traces.calibration_redesign import (
    load_calibration_redesign_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_cases import (
    CalibrationRedesignReplayCase,
    load_calibration_redesign_replay_case,
)


class CalibrationRedesignManifestViolationCode(StrEnum):
    """Machine-readable reasons a fresh calibration manifest cannot be trusted."""

    MANIFEST_SCHEMA_ERROR = "calibration_redesign_manifest_schema_error"
    MANIFEST_INTEGRITY_MISMATCH = "calibration_redesign_manifest_integrity_mismatch"
    MANIFEST_PROVENANCE_MISMATCH = "calibration_redesign_manifest_provenance_mismatch"


class CalibrationRedesignManifestLoadError(ValueError):
    """Typed error raised when a manifest or declared asset violates its boundary."""

    def __init__(self, code: CalibrationRedesignManifestViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignManifestArtifactKind(StrEnum):
    """The two structurally separate assets required for one fresh case."""

    RUNTIME_INPUT = "runtime_input"
    EXPECTED_OUTCOMES = "expected_outcomes"


class CalibrationRedesignManifestEntry(StrictContract):
    """Hash-addressed inventory entry for one fresh calibration case asset."""

    artifact_kind: CalibrationRedesignManifestArtifactKind
    relative_path: str = Field(min_length=1, max_length=300)
    case_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    data_role: TraceDataRole
    source_type: TraceSourceType
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_runtime_boundary(self) -> CalibrationRedesignManifestEntry:
        """Keep manifest reads local to its fixture root and calibration role."""

        normalized = self.relative_path.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
            raise ValueError("relative_path must remain inside the fixture root")
        if self.split is not TraceSplit.CALIBRATION:
            raise ValueError("fresh calibration manifest entries must use the calibration split")
        if self.data_role is not TraceDataRole.CALIBRATION:
            raise ValueError(
                "fresh calibration manifest entries must use the calibration data role"
            )
        if self.source_type is not TraceSourceType.SYNTHETIC:
            raise ValueError("fresh calibration manifest entries must use synthetic source type")
        return self


class CalibrationRedesignSplitCount(StrictContract):
    """Declared logical-case count for one manifest split."""

    split: TraceSplit
    case_count: int = Field(ge=0)


class CalibrationRedesignScenarioFamilyCount(StrictContract):
    """Declared logical-case count for one manifest scenario family."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    case_count: int = Field(ge=1)


class CalibrationRedesignFixtureManifest(StrictContract):
    """Deterministic inventory for immutable fresh calibration evidence."""

    schema_version: Literal["calibration-redesign-manifest-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v1"]
    fixture_set_version: str = Field(min_length=1, max_length=64)
    source_type: Literal[TraceSourceType.SYNTHETIC]
    authoring_protocol_version: Literal["calibration-redesign-protocol-v1"]
    scenario_family_registry_path: Literal["scenario_family_registry.json"]
    scenario_family_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenario_family_registry_byte_count: int = Field(gt=0)
    case_count: int = Field(gt=0)
    split_counts: tuple[CalibrationRedesignSplitCount, ...] = Field(min_length=1)
    scenario_family_counts: tuple[CalibrationRedesignScenarioFamilyCount, ...] = Field(
        min_length=1
    )
    entries: tuple[CalibrationRedesignManifestEntry, ...] = Field(min_length=2)
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_inventory_shape(self) -> CalibrationRedesignFixtureManifest:
        """Require complete paired evidence and accurate declared case counts."""

        entry_keys = {(entry.case_id, entry.artifact_kind) for entry in self.entries}
        if len(entry_keys) != len(self.entries):
            raise ValueError("manifest entries must not repeat a case_id/artifact_kind pair")

        case_ids = {entry.case_id for entry in self.entries}
        if len(case_ids) != self.case_count:
            raise ValueError("case_count must equal the number of unique manifest case IDs")

        for case_id in case_ids:
            kinds = {entry.artifact_kind for entry in self.entries if entry.case_id == case_id}
            if kinds != {
                CalibrationRedesignManifestArtifactKind.RUNTIME_INPUT,
                CalibrationRedesignManifestArtifactKind.EXPECTED_OUTCOMES,
            }:
                raise ValueError("each case must include one runtime input and expected outcomes")

        split_count_map = {count.split: count.case_count for count in self.split_counts}
        if len(split_count_map) != len(self.split_counts):
            raise ValueError("split_counts must not repeat a split")
        declared_calibration_count = split_count_map.get(TraceSplit.CALIBRATION, 0)
        if declared_calibration_count != self.case_count:
            raise ValueError("calibration split count must equal manifest case_count")
        if any(split is not TraceSplit.CALIBRATION for split in split_count_map):
            raise ValueError("fresh calibration manifest may declare only the calibration split")

        family_count_map = {
            count.scenario_family_id: count.case_count for count in self.scenario_family_counts
        }
        if len(family_count_map) != len(self.scenario_family_counts):
            raise ValueError("scenario_family_counts must not repeat a scenario family")
        actual_family_counts: dict[str, int] = defaultdict(int)
        for case_id in case_ids:
            entries = [entry for entry in self.entries if entry.case_id == case_id]
            family_ids = {entry.scenario_family_id for entry in entries}
            if len(family_ids) != 1:
                raise ValueError("runtime and outcome entries must agree on scenario family")
            actual_family_counts[family_ids.pop()] += 1
        if dict(actual_family_counts) != family_count_map:
            raise ValueError("scenario_family_counts must match manifest case families")
        return self


class CalibrationRedesignManifestedFixtureSet(StrictContract):
    """Immutable fresh calibration cases loaded only after manifest verification."""

    manifest: CalibrationRedesignFixtureManifest
    cases: tuple[CalibrationRedesignReplayCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case_identity(self) -> CalibrationRedesignManifestedFixtureSet:
        """Ensure each manifest case was loaded exactly once after integrity checks."""

        case_ids = {case.runtime_input.case_id for case in self.cases}
        if len(case_ids) != len(self.cases):
            raise ValueError("loaded fresh cases must have unique case IDs")
        if len(case_ids) != self.manifest.case_count:
            raise ValueError("loaded fresh case count must match manifest case_count")
        return self


def build_calibration_redesign_manifest(fixture_root: Path) -> Path:
    """Build a deterministic manifest from already-authored fresh calibration evidence."""

    root = fixture_root.resolve()
    registry_path = root / "scenario_family_registry.json"
    registry = load_calibration_redesign_scenario_family_registry(registry_path)
    runtime_paths = _discover_calibration_case_assets(root / "inputs" / "cases")
    outcome_paths = _discover_calibration_case_assets(root / "expected_outcomes")
    if set(runtime_paths) != set(outcome_paths):
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "runtime and outcome asset case IDs must match before manifest generation",
        )

    entries: list[CalibrationRedesignManifestEntry] = []
    family_counts: dict[str, int] = defaultdict(int)
    for case_id in sorted(runtime_paths):
        replay_case = load_calibration_redesign_replay_case(
            runtime_paths[case_id],
            outcome_paths[case_id],
            registry,
        )
        runtime = replay_case.runtime_input
        entries.extend(
            (
                _manifest_entry(
                    root,
                    runtime_paths[case_id],
                    CalibrationRedesignManifestArtifactKind.RUNTIME_INPUT,
                    runtime,
                ),
                _manifest_entry(
                    root,
                    outcome_paths[case_id],
                    CalibrationRedesignManifestArtifactKind.EXPECTED_OUTCOMES,
                    runtime,
                ),
            )
        )
        family_counts[runtime.scenario_family_id] += 1

    registry_bytes = _read_bytes(registry_path)
    manifest_without_aggregate: dict[str, Any] = {
        "schema_version": "calibration-redesign-manifest-v1",
        "fixture_set_id": registry.fixture_set_id,
        "fixture_set_version": registry.fixture_set_version,
        "source_type": TraceSourceType.SYNTHETIC.value,
        "authoring_protocol_version": registry.authoring_protocol_version,
        "scenario_family_registry_path": "scenario_family_registry.json",
        "scenario_family_registry_sha256": _sha256(registry_bytes),
        "scenario_family_registry_byte_count": len(registry_bytes),
        "case_count": len(runtime_paths),
        "split_counts": [
            {"split": TraceSplit.CALIBRATION.value, "case_count": len(runtime_paths)}
        ],
        "scenario_family_counts": [
            {"scenario_family_id": family_id, "case_count": family_counts[family_id]}
            for family_id in sorted(family_counts)
        ],
        "entries": [
            entry.model_dump(mode="json")
            for entry in sorted(entries, key=_entry_sort_key)
        ],
    }
    manifest_payload = {
        **manifest_without_aggregate,
        "aggregate_sha256": _aggregate_sha256(manifest_without_aggregate),
    }
    try:
        CalibrationRedesignFixtureManifest.model_validate(manifest_payload)
    except ValidationError as error:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"generated manifest schema validation failed: {error}",
        ) from error

    manifest_path = root / "manifest.json"
    manifest_path.write_bytes(_pretty_json_bytes(manifest_payload))
    return manifest_path


def load_calibration_redesign_manifested_fixture_set(
    fixture_root: Path,
) -> CalibrationRedesignManifestedFixtureSet:
    """Load fresh calibration cases only after strict manifest and registry verification."""

    root = fixture_root.resolve()
    manifest_path = root / "manifest.json"
    manifest_payload = _read_json(manifest_path)
    try:
        manifest = CalibrationRedesignFixtureManifest.model_validate(manifest_payload)
    except ValidationError as error:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"manifest schema validation failed: {error}",
        ) from error

    aggregate_payload = dict(manifest_payload)
    actual_aggregate = aggregate_payload.pop("aggregate_sha256", None)
    expected_aggregate = _aggregate_sha256(aggregate_payload)
    if actual_aggregate != expected_aggregate:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "manifest aggregate hash does not match its declared inventory",
        )

    registry_path = _resolve_path(root, manifest.scenario_family_registry_path)
    registry_bytes = _read_bytes(registry_path)
    if (
        _sha256(registry_bytes) != manifest.scenario_family_registry_sha256
        or len(registry_bytes) != manifest.scenario_family_registry_byte_count
    ):
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "scenario-family registry does not match manifest integrity metadata",
        )
    registry = load_calibration_redesign_scenario_family_registry(registry_path)
    if (
        registry.fixture_set_id != manifest.fixture_set_id
        or registry.fixture_set_version != manifest.fixture_set_version
    ):
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "scenario-family registry fixture identity does not match manifest",
        )

    entries_by_case: dict[
        str,
        dict[CalibrationRedesignManifestArtifactKind, CalibrationRedesignManifestEntry],
    ] = defaultdict(dict)
    for entry in manifest.entries:
        _verify_entry_bytes(root, entry)
        entries_by_case[entry.case_id][entry.artifact_kind] = entry

    cases: list[CalibrationRedesignReplayCase] = []
    for case_id in sorted(entries_by_case):
        entries = entries_by_case[case_id]
        runtime_entry = entries[CalibrationRedesignManifestArtifactKind.RUNTIME_INPUT]
        outcomes_entry = entries[CalibrationRedesignManifestArtifactKind.EXPECTED_OUTCOMES]
        replay_case = load_calibration_redesign_replay_case(
            _resolve_path(root, runtime_entry.relative_path),
            _resolve_path(root, outcomes_entry.relative_path),
            registry,
        )
        if replay_case.runtime_input.scenario_family_id != runtime_entry.scenario_family_id:
            raise CalibrationRedesignManifestLoadError(
                CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"manifest family does not match runtime case for {case_id}",
            )
        cases.append(replay_case)

    try:
        return CalibrationRedesignManifestedFixtureSet(manifest=manifest, cases=tuple(cases))
    except ValidationError as error:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"loaded fresh fixture set does not match its manifest: {error}",
        ) from error


def _discover_calibration_case_assets(directory: Path) -> dict[str, Path]:
    """Discover calibration-only assets without reading quarantined final-evaluation cases."""

    if not directory.is_dir():
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"fixture asset directory is missing: {directory}",
        )

    assets: dict[str, Path] = {}
    for path in sorted(directory.glob("*.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise CalibrationRedesignManifestLoadError(
                CalibrationRedesignManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"fixture asset must contain a JSON object: {path.name}",
            )

        if (
            payload.get("split") != TraceSplit.CALIBRATION.value
            or payload.get("data_role") != TraceDataRole.CALIBRATION.value
        ):
            continue

        case_id = payload.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise CalibrationRedesignManifestLoadError(
                CalibrationRedesignManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"fixture asset lacks a valid calibration case_id: {path.name}",
            )
        if case_id in assets:
            raise CalibrationRedesignManifestLoadError(
                CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"duplicate calibration fixture asset case ID in one directory: {case_id}",
            )
        assets[case_id] = path

    if not assets:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"fixture asset directory contains no calibration JSON assets: {directory}",
        )
    return assets


def _manifest_entry(
    root: Path,
    path: Path,
    artifact_kind: CalibrationRedesignManifestArtifactKind,
    runtime: Any,
) -> CalibrationRedesignManifestEntry:
    """Create one manifest entry from immutable local bytes and runtime provenance."""

    raw_bytes = _read_bytes(path)
    return CalibrationRedesignManifestEntry(
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


def _verify_entry_bytes(root: Path, entry: CalibrationRedesignManifestEntry) -> None:
    """Reject any declared asset whose current bytes differ from the frozen inventory."""

    raw_bytes = _read_bytes(_resolve_path(root, entry.relative_path))
    if _sha256(raw_bytes) != entry.sha256 or len(raw_bytes) != entry.byte_count:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            f"manifest mismatch for {entry.relative_path}",
        )


def _resolve_path(root: Path, relative_path: str) -> Path:
    """Resolve one manifest path while forbidding reads outside its fixture root."""

    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"manifest path escapes fixture root: {relative_path}",
        ) from error
    return candidate


def _read_json(path: Path) -> Any:
    """Read JSON with a typed error that preserves the local fixture boundary."""

    raw_bytes = _read_bytes(path)
    try:
        return json.loads(raw_bytes)
    except json.JSONDecodeError as error:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"invalid JSON in {path.name}: {error.msg}",
        ) from error


def _read_bytes(path: Path) -> bytes:
    """Read immutable local bytes without masking absent fixture artifacts."""

    try:
        return path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignManifestLoadError(
            CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"unable to read fixture asset: {path}",
        ) from error


def _entry_sort_key(entry: CalibrationRedesignManifestEntry) -> tuple[str, str]:
    """Keep manifest entries deterministic across supported local platforms."""

    return (entry.case_id, entry.artifact_kind.value)


def _sha256(raw_bytes: bytes) -> str:
    """Return the repository-standard SHA-256 digest for immutable fixture bytes."""

    return hashlib.sha256(raw_bytes).hexdigest()


def _aggregate_sha256(payload: dict[str, Any]) -> str:
    """Hash canonical manifest content while excluding the aggregate field itself."""

    return _sha256(_canonical_json_bytes(payload))


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    """Create stable bytes for manifest aggregate verification."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _pretty_json_bytes(payload: dict[str, Any]) -> bytes:
    """Write human-reviewable JSON while retaining a separately canonical aggregate hash."""

    return (json.dumps(payload, indent=2, sort_keys=False) + "\n").encode("utf-8")
