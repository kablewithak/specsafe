"""Immutable manifest generation and verification for quarantined final-evaluation fixtures."""

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
    ScenarioFamilyRegistry,
    load_calibration_redesign_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_cases import (
    CalibrationRedesignReplayCase,
    load_calibration_redesign_replay_case,
)

_FINAL_MANIFEST_FILENAME = "final_evaluation_manifest.json"
_FINAL_SPLIT = TraceSplit.FINAL_EVALUATION
_FINAL_DATA_ROLE = TraceDataRole.HELD_OUT_EVALUATION


class CalibrationRedesignFinalManifestViolationCode(StrEnum):
    """Machine-readable reasons a quarantined final manifest cannot be trusted."""

    MANIFEST_SCHEMA_ERROR = "calibration_redesign_final_manifest_schema_error"
    MANIFEST_INTEGRITY_MISMATCH = (
        "calibration_redesign_final_manifest_integrity_mismatch"
    )
    MANIFEST_PROVENANCE_MISMATCH = (
        "calibration_redesign_final_manifest_provenance_mismatch"
    )


class CalibrationRedesignFinalManifestLoadError(ValueError):
    """Typed error raised when final-evaluation manifest evidence violates its boundary."""

    def __init__(
        self, code: CalibrationRedesignFinalManifestViolationCode, message: str
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignFinalManifestArtifactKind(StrEnum):
    """The two structurally separate assets required for one final-evaluation case."""

    RUNTIME_INPUT = "runtime_input"
    EXPECTED_OUTCOMES = "expected_outcomes"


class CalibrationRedesignFinalManifestEntry(StrictContract):
    """Hash-addressed inventory entry for one quarantined final-evaluation asset."""

    artifact_kind: CalibrationRedesignFinalManifestArtifactKind
    relative_path: str = Field(min_length=1, max_length=300)
    case_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: Literal[TraceSplit.FINAL_EVALUATION]
    data_role: Literal[TraceDataRole.HELD_OUT_EVALUATION]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    is_final_evaluation_quarantined: Literal[True]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_path_boundary(self) -> CalibrationRedesignFinalManifestEntry:
        """Keep manifest reads local to the fixture root."""

        normalized = self.relative_path.replace("\\", "/")
        if (
            normalized.startswith("/")
            or normalized.startswith("../")
            or "/../" in normalized
        ):
            raise ValueError("relative_path must remain inside the fixture root")
        return self


class CalibrationRedesignFinalEvaluationSplitCount(StrictContract):
    """Declared logical-case count for the quarantined final-evaluation split."""

    split: Literal[TraceSplit.FINAL_EVALUATION]
    case_count: int = Field(gt=0)


class CalibrationRedesignFinalScenarioFamilyCount(StrictContract):
    """Declared logical-case count for one quarantined final-evaluation family."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    case_count: int = Field(gt=0)


class CalibrationRedesignFinalEvaluationFixtureManifest(StrictContract):
    """Deterministic inventory for immutable quarantined final-evaluation evidence."""

    schema_version: Literal["calibration-redesign-final-evaluation-manifest-v1"]
    fixture_set_id: Literal["synthetic-calibration-redesign-v1"]
    fixture_set_version: str = Field(min_length=1, max_length=64)
    source_type: Literal[TraceSourceType.SYNTHETIC]
    authoring_protocol_version: Literal["calibration-redesign-protocol-v1"]
    scenario_family_registry_path: Literal["scenario_family_registry.json"]
    scenario_family_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenario_family_registry_byte_count: int = Field(gt=0)
    case_count: int = Field(gt=0)
    split_counts: tuple[CalibrationRedesignFinalEvaluationSplitCount, ...] = Field(
        min_length=1
    )
    scenario_family_counts: tuple[CalibrationRedesignFinalScenarioFamilyCount, ...] = (
        Field(min_length=1)
    )
    entries: tuple[CalibrationRedesignFinalManifestEntry, ...] = Field(min_length=2)
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_inventory_shape(
        self,
    ) -> CalibrationRedesignFinalEvaluationFixtureManifest:
        """Require complete paired quarantined evidence and accurate declared case counts."""

        entry_keys = {(entry.case_id, entry.artifact_kind) for entry in self.entries}
        if len(entry_keys) != len(self.entries):
            raise ValueError(
                "manifest entries must not repeat a case_id/artifact_kind pair"
            )

        case_ids = {entry.case_id for entry in self.entries}
        if len(case_ids) != self.case_count:
            raise ValueError(
                "case_count must equal the number of unique manifest case IDs"
            )

        required_kinds = {
            CalibrationRedesignFinalManifestArtifactKind.RUNTIME_INPUT,
            CalibrationRedesignFinalManifestArtifactKind.EXPECTED_OUTCOMES,
        }
        for case_id in case_ids:
            kinds = {
                entry.artifact_kind
                for entry in self.entries
                if entry.case_id == case_id
            }
            if kinds != required_kinds:
                raise ValueError(
                    "each case must include one runtime input and expected outcomes"
                )

        split_count_map = {count.split: count.case_count for count in self.split_counts}
        if len(split_count_map) != len(self.split_counts):
            raise ValueError("split_counts must not repeat a split")
        if split_count_map.get(_FINAL_SPLIT) != self.case_count:
            raise ValueError(
                "final-evaluation split count must equal manifest case_count"
            )

        family_count_map = {
            count.scenario_family_id: count.case_count
            for count in self.scenario_family_counts
        }
        if len(family_count_map) != len(self.scenario_family_counts):
            raise ValueError("scenario_family_counts must not repeat a scenario family")
        actual_family_counts: dict[str, int] = defaultdict(int)
        for case_id in case_ids:
            entries = [entry for entry in self.entries if entry.case_id == case_id]
            family_ids = {entry.scenario_family_id for entry in entries}
            if len(family_ids) != 1:
                raise ValueError(
                    "runtime and outcome entries must agree on scenario family"
                )
            actual_family_counts[family_ids.pop()] += 1
        if dict(actual_family_counts) != family_count_map:
            raise ValueError("scenario_family_counts must match manifest case families")
        return self


class CalibrationRedesignFinalManifestedFixtureSet(StrictContract):
    """Immutable final-evaluation cases loaded only after strict manifest verification."""

    manifest: CalibrationRedesignFinalEvaluationFixtureManifest
    cases: tuple[CalibrationRedesignReplayCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case_identity(self) -> CalibrationRedesignFinalManifestedFixtureSet:
        """Ensure each manifest case was loaded exactly once after integrity checks."""

        case_ids = {case.runtime_input.case_id for case in self.cases}
        if len(case_ids) != len(self.cases):
            raise ValueError("loaded final cases must have unique case IDs")
        if len(case_ids) != self.manifest.case_count:
            raise ValueError("loaded final case count must match manifest case_count")
        return self


def build_calibration_redesign_final_evaluation_manifest(fixture_root: Path) -> Path:
    """Build a deterministic manifest from all predeclared quarantined final evidence."""

    root = fixture_root.resolve()
    registry_path = root / "scenario_family_registry.json"
    registry = load_calibration_redesign_scenario_family_registry(registry_path)
    expected_case_ids = _expected_final_case_ids(registry)
    runtime_paths = _discover_final_evaluation_case_assets(
        root / "inputs" / "cases", expected_case_ids
    )
    outcome_paths = _discover_final_evaluation_case_assets(
        root / "expected_outcomes", expected_case_ids
    )
    _require_complete_final_case_inventory("runtime", runtime_paths, expected_case_ids)
    _require_complete_final_case_inventory("outcome", outcome_paths, expected_case_ids)

    entries: list[CalibrationRedesignFinalManifestEntry] = []
    family_counts: dict[str, int] = defaultdict(int)
    family_by_id = {family.scenario_family_id: family for family in registry.families}
    for case_id in sorted(expected_case_ids):
        replay_case = load_calibration_redesign_replay_case(
            runtime_paths[case_id],
            outcome_paths[case_id],
            registry,
        )
        runtime = replay_case.runtime_input
        family = family_by_id[runtime.scenario_family_id]
        _validate_quarantined_final_case(replay_case, family)
        entries.extend(
            (
                _manifest_entry(
                    root,
                    runtime_paths[case_id],
                    CalibrationRedesignFinalManifestArtifactKind.RUNTIME_INPUT,
                    runtime,
                ),
                _manifest_entry(
                    root,
                    outcome_paths[case_id],
                    CalibrationRedesignFinalManifestArtifactKind.EXPECTED_OUTCOMES,
                    runtime,
                ),
            )
        )
        family_counts[runtime.scenario_family_id] += 1

    registry_bytes = _read_bytes(registry_path)
    manifest_without_aggregate: dict[str, Any] = {
        "schema_version": "calibration-redesign-final-evaluation-manifest-v1",
        "fixture_set_id": registry.fixture_set_id,
        "fixture_set_version": registry.fixture_set_version,
        "source_type": TraceSourceType.SYNTHETIC.value,
        "authoring_protocol_version": registry.authoring_protocol_version,
        "scenario_family_registry_path": "scenario_family_registry.json",
        "scenario_family_registry_sha256": _sha256(registry_bytes),
        "scenario_family_registry_byte_count": len(registry_bytes),
        "case_count": len(expected_case_ids),
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
            entry.model_dump(mode="json")
            for entry in sorted(entries, key=_entry_sort_key)
        ],
    }
    manifest_payload = {
        **manifest_without_aggregate,
        "aggregate_sha256": _aggregate_sha256(manifest_without_aggregate),
    }
    try:
        CalibrationRedesignFinalEvaluationFixtureManifest.model_validate(
            manifest_payload
        )
    except ValidationError as error:
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"generated final-evaluation manifest schema validation failed: {error}",
        ) from error

    manifest_path = root / _FINAL_MANIFEST_FILENAME
    manifest_path.write_bytes(_pretty_json_bytes(manifest_payload))
    return manifest_path


def load_calibration_redesign_final_evaluation_manifested_fixture_set(
    fixture_root: Path,
) -> CalibrationRedesignFinalManifestedFixtureSet:
    """Load quarantined final cases after strict manifest and registry verification."""

    root = fixture_root.resolve()
    manifest_path = root / _FINAL_MANIFEST_FILENAME
    manifest_payload = _read_json(manifest_path)
    try:
        manifest = CalibrationRedesignFinalEvaluationFixtureManifest.model_validate(
            manifest_payload
        )
    except ValidationError as error:
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"final-evaluation manifest schema validation failed: {error}",
        ) from error

    aggregate_payload = dict(manifest_payload)
    actual_aggregate = aggregate_payload.pop("aggregate_sha256", None)
    if actual_aggregate != _aggregate_sha256(aggregate_payload):
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "final-evaluation manifest aggregate hash does not match its declared inventory",
        )

    registry_path = _resolve_path(root, manifest.scenario_family_registry_path)
    registry_bytes = _read_bytes(registry_path)
    if (
        _sha256(registry_bytes) != manifest.scenario_family_registry_sha256
        or len(registry_bytes) != manifest.scenario_family_registry_byte_count
    ):
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            "scenario-family registry does not match final-evaluation manifest integrity metadata",
        )
    registry = load_calibration_redesign_scenario_family_registry(registry_path)
    if (
        registry.fixture_set_id != manifest.fixture_set_id
        or registry.fixture_set_version != manifest.fixture_set_version
    ):
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "scenario-family registry fixture identity does not match final-evaluation manifest",
        )

    expected_case_ids = _expected_final_case_ids(registry)
    manifest_case_ids = {entry.case_id for entry in manifest.entries}
    if manifest_case_ids != expected_case_ids:
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "final-evaluation manifest must include every predeclared quarantined final case",
        )

    entries_by_case: dict[
        str,
        dict[
            CalibrationRedesignFinalManifestArtifactKind,
            CalibrationRedesignFinalManifestEntry,
        ],
    ] = defaultdict(dict)
    for entry in manifest.entries:
        _verify_entry_bytes(root, entry)
        entries_by_case[entry.case_id][entry.artifact_kind] = entry

    family_by_id = {family.scenario_family_id: family for family in registry.families}
    cases: list[CalibrationRedesignReplayCase] = []
    for case_id in sorted(entries_by_case):
        entries = entries_by_case[case_id]
        runtime_entry = entries[
            CalibrationRedesignFinalManifestArtifactKind.RUNTIME_INPUT
        ]
        outcomes_entry = entries[
            CalibrationRedesignFinalManifestArtifactKind.EXPECTED_OUTCOMES
        ]
        replay_case = load_calibration_redesign_replay_case(
            _resolve_path(root, runtime_entry.relative_path),
            _resolve_path(root, outcomes_entry.relative_path),
            registry,
        )
        runtime = replay_case.runtime_input
        if runtime.scenario_family_id != runtime_entry.scenario_family_id:
            raise CalibrationRedesignFinalManifestLoadError(
                CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"manifest family does not match runtime case for {case_id}",
            )
        _validate_quarantined_final_case(
            replay_case, family_by_id[runtime.scenario_family_id]
        )
        cases.append(replay_case)

    try:
        return CalibrationRedesignFinalManifestedFixtureSet(
            manifest=manifest, cases=tuple(cases)
        )
    except ValidationError as error:
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"loaded final fixture set does not match its manifest: {error}",
        ) from error


def _expected_final_case_ids(registry: ScenarioFamilyRegistry) -> frozenset[str]:
    """Return all and only the predeclared quarantined final-evaluation case IDs."""

    final_families = [
        family for family in registry.families if family.split is _FINAL_SPLIT
    ]
    if not final_families or any(
        not family.is_final_evaluation_quarantined for family in final_families
    ):
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            "final-evaluation registry families must exist and remain quarantined",
        )
    return frozenset(
        case_id for family in final_families for case_id in family.case_ids
    )


def _discover_final_evaluation_case_assets(
    directory: Path,
    expected_case_ids: frozenset[str],
) -> dict[str, Path]:
    """Discover only predeclared final assets without reading calibration evidence."""

    if not directory.is_dir():
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"fixture asset directory is missing: {directory}",
        )

    assets: dict[str, Path] = {}
    for path in sorted(directory.glob("*.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise CalibrationRedesignFinalManifestLoadError(
                CalibrationRedesignFinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"fixture asset must contain a JSON object: {path.name}",
            )
        case_id = payload.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise CalibrationRedesignFinalManifestLoadError(
                CalibrationRedesignFinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
                f"fixture asset lacks a valid case_id: {path.name}",
            )
        if case_id not in expected_case_ids:
            if (
                payload.get("split") == _FINAL_SPLIT.value
                or payload.get("data_role") == _FINAL_DATA_ROLE.value
            ):
                raise CalibrationRedesignFinalManifestLoadError(
                    CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                    f"undeclared final-evaluation fixture asset: {path.name}",
                )
            continue
        if (
            payload.get("split") != _FINAL_SPLIT.value
            or payload.get("data_role") != _FINAL_DATA_ROLE.value
        ):
            raise CalibrationRedesignFinalManifestLoadError(
                CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"predeclared final-evaluation asset has invalid split or data role: {path.name}",
            )
        if case_id in assets:
            raise CalibrationRedesignFinalManifestLoadError(
                CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
                f"duplicate final-evaluation fixture asset case ID in one directory: {case_id}",
            )
        assets[case_id] = path
    return assets


def _require_complete_final_case_inventory(
    asset_label: str,
    paths: dict[str, Path],
    expected_case_ids: frozenset[str],
) -> None:
    """Require complete paired final evidence before a final manifest can be frozen."""

    discovered_case_ids = set(paths)
    if discovered_case_ids != expected_case_ids:
        missing_case_ids = sorted(expected_case_ids - discovered_case_ids)
        unexpected_case_ids = sorted(discovered_case_ids - expected_case_ids)
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"{asset_label} final-evaluation case inventory is incomplete; "
            f"missing={missing_case_ids}, unexpected={unexpected_case_ids}",
        )


def _validate_quarantined_final_case(
    replay_case: CalibrationRedesignReplayCase,
    family: Any,
) -> None:
    """Recheck that one loaded case is eligible only for held-out assessment."""

    runtime = replay_case.runtime_input
    if (
        runtime.split is not _FINAL_SPLIT
        or runtime.data_role is not _FINAL_DATA_ROLE
        or runtime.source_type is not TraceSourceType.SYNTHETIC
        or family.split is not _FINAL_SPLIT
        or family.primary_data_role is not _FINAL_DATA_ROLE
        or family.is_final_evaluation_quarantined is not True
        or runtime.case_id not in family.case_ids
    ):
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"case is not a quarantined final-evaluation asset: {runtime.case_id}",
        )


def _manifest_entry(
    root: Path,
    path: Path,
    artifact_kind: CalibrationRedesignFinalManifestArtifactKind,
    runtime: Any,
) -> CalibrationRedesignFinalManifestEntry:
    """Create one final manifest entry from immutable local bytes and runtime provenance."""

    raw_bytes = _read_bytes(path)
    return CalibrationRedesignFinalManifestEntry(
        artifact_kind=artifact_kind,
        relative_path=path.resolve().relative_to(root).as_posix(),
        case_id=runtime.case_id,
        scenario_family_id=runtime.scenario_family_id,
        split=runtime.split,
        data_role=runtime.data_role,
        source_type=runtime.source_type,
        is_final_evaluation_quarantined=True,
        sha256=_sha256(raw_bytes),
        byte_count=len(raw_bytes),
    )


def _verify_entry_bytes(
    root: Path, entry: CalibrationRedesignFinalManifestEntry
) -> None:
    """Reject any declared final asset whose current bytes differ from the frozen inventory."""

    raw_bytes = _read_bytes(_resolve_path(root, entry.relative_path))
    if _sha256(raw_bytes) != entry.sha256 or len(raw_bytes) != entry.byte_count:
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH,
            f"final-evaluation manifest mismatch for {entry.relative_path}",
        )


def _resolve_path(root: Path, relative_path: str) -> Path:
    """Resolve one manifest path while forbidding reads outside its fixture root."""

    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"manifest path escapes fixture root: {relative_path}",
        ) from error
    return candidate


def _read_json(path: Path) -> Any:
    """Read JSON with a typed error that preserves the local fixture boundary."""

    raw_bytes = _read_bytes(path)
    try:
        return json.loads(raw_bytes)
    except json.JSONDecodeError as error:
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"invalid JSON in {path.name}: {error.msg}",
        ) from error


def _read_bytes(path: Path) -> bytes:
    """Read immutable local bytes without masking absent fixture artifacts."""

    try:
        return path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignFinalManifestLoadError(
            CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH,
            f"unable to read fixture asset: {path}",
        ) from error


def _entry_sort_key(entry: CalibrationRedesignFinalManifestEntry) -> tuple[str, str]:
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
