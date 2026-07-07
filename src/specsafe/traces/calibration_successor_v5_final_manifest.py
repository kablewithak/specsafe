"""Immutable V5 final-evaluation manifest and label-free evidence-index controls.

This module freezes CSV5-201 through CSV5-236 only after all four held-out families exist.
It records provenance and integrity. It does not fit, refit, assess, select thresholds,
execute a scheduler, replay a policy, or authorize runtime control.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import StrictContract, TraceSourceType, WorkloadType
from specsafe.traces.calibration_successor_v5 import (
    CalibrationSuccessorV5RegistryLoadError,
    CalibrationSuccessorV5ScenarioFamilyRegistry,
    assert_calibration_successor_v5_final_mixed_reliability_contrast_fixture_root,
    load_calibration_successor_v5_scenario_family_registry,
)
from specsafe.traces.calibration_successor_v5_final_cases import (
    CalibrationSuccessorV5FinalExpectedOutcomes,
    CalibrationSuccessorV5FinalReplayCase,
    CalibrationSuccessorV5FinalRuntimeInput,
)

_FINAL_ROOT = "final_evaluation"
_MANIFEST_FILENAME = "final_evaluation_manifest.json"
_INDEX_FILENAME = "final_evidence_index.json"
_MANIFEST_SCHEMA = "calibration-successor-v5-final-evaluation-manifest-v1"
_INDEX_SCHEMA = "calibration-successor-v5-final-evidence-index-v1"
_MANIFEST_ID = "v5-final-evaluation-manifest-freeze"
_INDEX_ID = "v5-final-evidence-index-freeze"
_FIXTURE_SET_ID = "synthetic-calibration-successor-v5"
_FIXTURE_SET_VERSION = "1.0.0"
_METHOD_VERSION = "v5-bounded-monotone-beta-calibration-eligibility-charter-v1"
_METHOD_ID = "bounded-monotone-beta-calibration-v5"
_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(201, 237))
_CASE_COUNT = 36
_ASSET_COUNT = 72
_OBSERVATION_COUNT = 144

_FINAL_AUTHORED_EXCLUSION = (
    "Only CSV5-201..CSV5-236 final-evaluation runtime-input and "
    "expected-outcome case pairs are authored."
)
_FINAL_MANIFEST_FROZEN_EXCLUSION = (
    "V5 final-evaluation manifest and final-evidence index are frozen provenance boundaries."
)
_FINAL_MANIFEST_NON_ASSESSMENT_EXCLUSION = (
    "V5 final-evaluation manifest freeze does not author an assessment, baseline, or policy result."
)
_FINAL_ASSESSMENT_BLOCKED_EXCLUSION = (
    "No V5 held-out assessment, scheduler, baseline comparison, capacity "
    "profile, utility scorer, or runtime control is authorized."
)
_PRE_MANIFEST_BLOCKED_EXCLUSION = (
    "No V5 final-evaluation manifest, held-out assessment, scheduler, baseline "
    "comparison, capacity profile, utility scorer, or runtime control is authorized."
)

_FAMILY_IDS = (
    "CSV5-FINAL-CURVE-COVERAGE",
    "CSV5-FINAL-POSITION-SPREAD",
    "CSV5-FINAL-WORKLOAD-VARIATION",
    "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST",
)


class CalibrationSuccessorV5FinalManifestViolationCode(StrEnum):
    DESTINATION_ALREADY_EXISTS = "calibration_successor_v5_final_manifest_destination_exists"
    DESTINATION_WRITE_ERROR = "calibration_successor_v5_final_manifest_destination_write_error"
    PRE_FREEZE_ROOT_INVALID = "calibration_successor_v5_final_manifest_pre_freeze_root_invalid"
    MANIFEST_READ_ERROR = "calibration_successor_v5_final_manifest_read_error"
    MANIFEST_SCHEMA_ERROR = "calibration_successor_v5_final_manifest_schema_error"
    INDEX_SCHEMA_ERROR = "calibration_successor_v5_final_index_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = (
        "calibration_successor_v5_final_manifest_registry_provenance_mismatch"
    )
    INVENTORY_MISMATCH = "calibration_successor_v5_final_manifest_inventory_mismatch"
    ASSET_INTEGRITY_MISMATCH = "calibration_successor_v5_final_manifest_asset_integrity_mismatch"
    AGGREGATE_MISMATCH = "calibration_successor_v5_final_manifest_aggregate_mismatch"
    INDEX_INTEGRITY_MISMATCH = "calibration_successor_v5_final_manifest_index_integrity_mismatch"


class CalibrationSuccessorV5FinalManifestError(ValueError):
    def __init__(
        self, code: CalibrationSuccessorV5FinalManifestViolationCode, message: str
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationSuccessorV5FinalManifestAsset(StrictContract):
    relative_path: str = Field(
        pattern=r"^final_evaluation/(inputs|expected_outcomes)/cases/CSV5-2[0-9]{2}\.json$"
    )
    case_id: str = Field(pattern=r"^CSV5-2[0-9]{2}$")
    asset_kind: Literal["runtime_input", "expected_outcome"]
    scenario_family_id: Literal[
        "CSV5-FINAL-CURVE-COVERAGE",
        "CSV5-FINAL-POSITION-SPREAD",
        "CSV5-FINAL-WORKLOAD-VARIATION",
        "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST",
    ]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_path(self) -> CalibrationSuccessorV5FinalManifestAsset:
        parent = (
            "final_evaluation/inputs/cases"
            if self.asset_kind == "runtime_input"
            else "final_evaluation/expected_outcomes/cases"
        )
        if self.relative_path != f"{parent}/{self.case_id}.json":
            raise ValueError("V5 final manifest asset path must match case ID and kind")
        return self


class CalibrationSuccessorV5FinalManifestCasePair(StrictContract):
    case_id: str = Field(pattern=r"^CSV5-2[0-9]{2}$")
    scenario_family_id: Literal[
        "CSV5-FINAL-CURVE-COVERAGE",
        "CSV5-FINAL-POSITION-SPREAD",
        "CSV5-FINAL-WORKLOAD-VARIATION",
        "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST",
    ]
    runtime_input_relative_path: str = Field(
        pattern=r"^final_evaluation/inputs/cases/CSV5-2[0-9]{2}\.json$"
    )
    expected_outcome_relative_path: str = Field(
        pattern=r"^final_evaluation/expected_outcomes/cases/CSV5-2[0-9]{2}\.json$"
    )
    runtime_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_outcome_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class CalibrationSuccessorV5FinalEvidenceIndexEntry(StrictContract):
    case_id: str = Field(pattern=r"^CSV5-2[0-9]{2}$")
    trace_id: str = Field(min_length=1, max_length=128)
    scenario_family_id: Literal[
        "CSV5-FINAL-CURVE-COVERAGE",
        "CSV5-FINAL-POSITION-SPREAD",
        "CSV5-FINAL-WORKLOAD-VARIATION",
        "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST",
    ]
    workload_type: WorkloadType
    runtime_input_relative_path: str = Field(
        pattern=r"^final_evaluation/inputs/cases/CSV5-2[0-9]{2}\.json$"
    )
    expected_outcome_relative_path: str = Field(
        pattern=r"^final_evaluation/expected_outcomes/cases/CSV5-2[0-9]{2}\.json$"
    )


class CalibrationSuccessorV5FinalEvidenceIndex(StrictContract):
    schema_version: Literal["calibration-successor-v5-final-evidence-index-v1"] = _INDEX_SCHEMA
    index_id: Literal["v5-final-evidence-index-freeze"] = _INDEX_ID
    index_scope: Literal["final_evaluation_only"] = "final_evaluation_only"
    fixture_set_id: Literal["synthetic-calibration-successor-v5"] = _FIXTURE_SET_ID
    fixture_set_version: Literal["1.0.0"] = _FIXTURE_SET_VERSION
    source_type: Literal[TraceSourceType.SYNTHETIC] = TraceSourceType.SYNTHETIC
    frozen_final_evaluation_pre_freeze_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_ids: tuple[str, ...] = Field(min_length=36, max_length=36)
    trace_ids: tuple[str, ...] = Field(min_length=36, max_length=36)
    case_count: Literal[36] = 36
    observation_count: Literal[144] = 144
    candidate_positions_per_case: Literal[4] = 4
    entries: tuple[CalibrationSuccessorV5FinalEvidenceIndexEntry, ...] = Field(
        min_length=36, max_length=36
    )
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_shape(self) -> CalibrationSuccessorV5FinalEvidenceIndex:
        if self.case_ids != _CASE_IDS:
            raise ValueError("V5 final index case IDs must be CSV5-201 through CSV5-236")
        if tuple(entry.case_id for entry in self.entries) != _CASE_IDS:
            raise ValueError("V5 final index entries must be sorted by case ID")
        if self.trace_ids != tuple(entry.trace_id for entry in self.entries):
            raise ValueError("V5 final index trace IDs must match sorted entries")
        if len(set(self.trace_ids)) != _CASE_COUNT:
            raise ValueError("V5 final index trace IDs must be unique")
        if Counter(entry.scenario_family_id for entry in self.entries) != Counter(
            {family: 9 for family in _FAMILY_IDS}
        ):
            raise ValueError("V5 final index requires nine cases per held-out family")
        if Counter(entry.workload_type for entry in self.entries) != Counter(
            {
                WorkloadType.STRUCTURED_TEXT: 12,
                WorkloadType.CODE: 12,
                WorkloadType.OPEN_ENDED_CHAT: 12,
            }
        ):
            raise ValueError("V5 final index requires 12 cases per workload")
        return self


class CalibrationSuccessorV5FinalEvaluationManifest(StrictContract):
    schema_version: Literal["calibration-successor-v5-final-evaluation-manifest-v1"] = (
        _MANIFEST_SCHEMA
    )
    manifest_id: Literal["v5-final-evaluation-manifest-freeze"] = _MANIFEST_ID
    manifest_scope: Literal["final_evaluation_only"] = "final_evaluation_only"
    fixture_set_id: Literal["synthetic-calibration-successor-v5"] = _FIXTURE_SET_ID
    fixture_set_version: Literal["1.0.0"] = _FIXTURE_SET_VERSION
    method_constitution_version: Literal[
        "v5-bounded-monotone-beta-calibration-eligibility-charter-v1"
    ] = _METHOD_VERSION
    calibration_method_id: Literal["bounded-monotone-beta-calibration-v5"] = _METHOD_ID
    frozen_final_evaluation_pre_freeze_registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evidence_index_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    final_evidence_index_byte_count: int = Field(ge=1)
    case_ids: tuple[str, ...] = Field(min_length=36, max_length=36)
    case_pair_count: Literal[36] = 36
    asset_count: Literal[72] = 72
    observation_count: Literal[144] = 144
    aggregate_byte_count: int = Field(ge=1)
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    assets: tuple[CalibrationSuccessorV5FinalManifestAsset, ...] = Field(
        min_length=72, max_length=72
    )
    case_pairs: tuple[CalibrationSuccessorV5FinalManifestCasePair, ...] = Field(
        min_length=36, max_length=36
    )

    @model_validator(mode="after")
    def validate_shape(self) -> CalibrationSuccessorV5FinalEvaluationManifest:
        if self.case_ids != _CASE_IDS:
            raise ValueError("V5 final manifest case IDs must be CSV5-201 through CSV5-236")
        if tuple(pair.case_id for pair in self.case_pairs) != _CASE_IDS:
            raise ValueError("V5 final manifest case pairs must be sorted by case ID")
        if self.aggregate_byte_count != sum(asset.byte_count for asset in self.assets):
            raise ValueError("V5 final manifest aggregate byte count must match asset records")
        return self


class CalibrationSuccessorV5FinalManifestedFixtureSet(StrictContract):
    manifest: CalibrationSuccessorV5FinalEvaluationManifest
    index: CalibrationSuccessorV5FinalEvidenceIndex
    cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...] = Field(min_length=36, max_length=36)


def freeze_calibration_successor_v5_final_evaluation_manifest(
    root: Path,
) -> CalibrationSuccessorV5FinalManifestedFixtureSet:
    resolved = root.resolve()
    if (resolved / _MANIFEST_FILENAME).exists() or (resolved / _INDEX_FILENAME).exists():
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.DESTINATION_ALREADY_EXISTS,
            "V5 final manifest and evidence index are write-once destinations",
        )
    try:
        assert_calibration_successor_v5_final_mixed_reliability_contrast_fixture_root(resolved)
        registry = load_calibration_successor_v5_scenario_family_registry(
            resolved / "scenario_family_registry.json",
            allow_final_mixed_reliability_contrast_assets=True,
        )
    except CalibrationSuccessorV5RegistryLoadError as error:
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V5 final manifest requires a complete pre-freeze root: {error}",
        ) from error
    registry_bytes = (resolved / "scenario_family_registry.json").read_bytes()
    cases = tuple(_load_case_without_registry(resolved, case_id) for case_id in _CASE_IDS)
    index = _build_index(cases, hashlib.sha256(registry_bytes).hexdigest())
    index_bytes = _canonical(index.model_dump(mode="json"))
    manifest = _build_manifest(
        resolved, cases, hashlib.sha256(registry_bytes).hexdigest(), index_bytes
    )
    manifest_bytes = _canonical(manifest.model_dump(mode="json"))
    registry_payload = registry.model_dump(mode="json")
    exclusions = [
        item
        for item in registry_payload["explicit_exclusions"]
        if item != _PRE_MANIFEST_BLOCKED_EXCLUSION
    ]
    exclusions.extend(
        [
            _FINAL_MANIFEST_FROZEN_EXCLUSION,
            _FINAL_MANIFEST_NON_ASSESSMENT_EXCLUSION,
            _FINAL_ASSESSMENT_BLOCKED_EXCLUSION,
        ]
    )
    registry_payload.update(
        {
            "registry_status": "final_evaluation_manifest_frozen",
            "v5_final_evaluation_manifest_authored": True,
            "frozen_final_evaluation_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "frozen_final_evaluation_pre_freeze_registry_sha256": hashlib.sha256(
                registry_bytes
            ).hexdigest(),
            "final_evidence_index_sha256": hashlib.sha256(index_bytes).hexdigest(),
            "explicit_exclusions": exclusions,
            "next_authorized_artifact": "v5-final-heldout-calibration-assessment",
        }
    )
    try:
        CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(registry_payload)
    except ValidationError as error:
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V5 final frozen registry validation failed: {error}",
        ) from error
    try:
        (resolved / _INDEX_FILENAME).write_bytes(index_bytes)
        (resolved / _MANIFEST_FILENAME).write_bytes(manifest_bytes)
        (resolved / "scenario_family_registry.json").write_bytes(_canonical(registry_payload))
    except OSError as error:
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.DESTINATION_WRITE_ERROR,
            f"unable to persist V5 final manifest freeze: {error}",
        ) from error
    return load_calibration_successor_v5_final_manifested_fixture_set(resolved)


def load_calibration_successor_v5_final_manifested_fixture_set(
    root: Path,
) -> CalibrationSuccessorV5FinalManifestedFixtureSet:
    resolved = root.resolve()
    try:
        registry = load_calibration_successor_v5_scenario_family_registry(
            resolved / "scenario_family_registry.json",
            allow_final_evaluation_manifest_assets=True,
        )
        manifest = CalibrationSuccessorV5FinalEvaluationManifest.model_validate(
            json.loads((resolved / _MANIFEST_FILENAME).read_text(encoding="utf-8"))
        )
        index = CalibrationSuccessorV5FinalEvidenceIndex.model_validate(
            json.loads((resolved / _INDEX_FILENAME).read_text(encoding="utf-8"))
        )
    except (
        OSError,
        json.JSONDecodeError,
        ValidationError,
        CalibrationSuccessorV5RegistryLoadError,
    ) as error:
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"unable to load V5 final manifest boundary: {error}",
        ) from error
    if registry.frozen_final_evaluation_manifest_sha256 != _sha256(resolved / _MANIFEST_FILENAME):
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V5 registry final manifest SHA-256 mismatch",
        )
    if registry.final_evidence_index_sha256 != _sha256(resolved / _INDEX_FILENAME):
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V5 registry final evidence-index SHA-256 mismatch",
        )
    if manifest.final_evidence_index_sha256 != _sha256(resolved / _INDEX_FILENAME):
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.INDEX_INTEGRITY_MISMATCH,
            "V5 final manifest does not identify the frozen index",
        )
    actual_assets = _collect_assets(resolved, _load_cases(resolved))
    if manifest.assets != actual_assets:
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.ASSET_INTEGRITY_MISMATCH,
            "V5 final manifest assets do not match final evidence bytes",
        )
    if manifest.aggregate_sha256 != _aggregate(actual_assets):
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.AGGREGATE_MISMATCH,
            "V5 final manifest aggregate SHA-256 mismatch",
        )
    cases = _load_cases(resolved)
    return CalibrationSuccessorV5FinalManifestedFixtureSet(
        manifest=manifest, index=index, cases=cases
    )


def _load_cases(root: Path) -> tuple[CalibrationSuccessorV5FinalReplayCase, ...]:
    return tuple(_load_case_without_registry(root, case_id) for case_id in _CASE_IDS)


def _load_case_without_registry(root: Path, case_id: str) -> CalibrationSuccessorV5FinalReplayCase:
    try:
        runtime = CalibrationSuccessorV5FinalRuntimeInput.model_validate(
            json.loads(
                (root / _FINAL_ROOT / "inputs" / "cases" / f"{case_id}.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        outcome = CalibrationSuccessorV5FinalExpectedOutcomes.model_validate(
            json.loads(
                (root / _FINAL_ROOT / "expected_outcomes" / "cases" / f"{case_id}.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        return CalibrationSuccessorV5FinalReplayCase(
            runtime_input=runtime, expected_outcomes=outcome
        )
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise CalibrationSuccessorV5FinalManifestError(
            CalibrationSuccessorV5FinalManifestViolationCode.INVENTORY_MISMATCH,
            f"V5 final case {case_id} is invalid: {error}",
        ) from error


def _build_index(
    cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...], prefreeze_sha: str
) -> CalibrationSuccessorV5FinalEvidenceIndex:
    entries = tuple(
        CalibrationSuccessorV5FinalEvidenceIndexEntry(
            case_id=case.runtime_input.case_id,
            trace_id=case.runtime_input.trace_id,
            scenario_family_id=case.runtime_input.scenario_family_id,
            workload_type=case.runtime_input.contexts[0].workload_type,
            runtime_input_relative_path=f"final_evaluation/inputs/cases/{case.runtime_input.case_id}.json",
            expected_outcome_relative_path=f"final_evaluation/expected_outcomes/cases/{case.runtime_input.case_id}.json",
        )
        for case in cases
    )
    payload = [entry.model_dump(mode="json") for entry in entries]
    return CalibrationSuccessorV5FinalEvidenceIndex(
        frozen_final_evaluation_pre_freeze_registry_sha256=prefreeze_sha,
        case_ids=_CASE_IDS,
        trace_ids=tuple(entry.trace_id for entry in entries),
        entries=entries,
        aggregate_sha256=hashlib.sha256(_canonical(payload)).hexdigest(),
    )


def _build_manifest(
    root: Path,
    cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...],
    prefreeze_sha: str,
    index_bytes: bytes,
) -> CalibrationSuccessorV5FinalEvaluationManifest:
    assets = _collect_assets(root, cases)
    by_path = {asset.relative_path: asset for asset in assets}
    families = {case.runtime_input.case_id: case.runtime_input.scenario_family_id for case in cases}
    pairs = tuple(
        CalibrationSuccessorV5FinalManifestCasePair(
            case_id=case_id,
            scenario_family_id=families[case_id],
            runtime_input_relative_path=f"final_evaluation/inputs/cases/{case_id}.json",
            expected_outcome_relative_path=f"final_evaluation/expected_outcomes/cases/{case_id}.json",
            runtime_input_sha256=by_path[f"final_evaluation/inputs/cases/{case_id}.json"].sha256,
            expected_outcome_sha256=by_path[
                f"final_evaluation/expected_outcomes/cases/{case_id}.json"
            ].sha256,
        )
        for case_id in _CASE_IDS
    )
    return CalibrationSuccessorV5FinalEvaluationManifest(
        frozen_final_evaluation_pre_freeze_registry_sha256=prefreeze_sha,
        final_evidence_index_sha256=hashlib.sha256(index_bytes).hexdigest(),
        final_evidence_index_byte_count=len(index_bytes),
        case_ids=_CASE_IDS,
        aggregate_byte_count=sum(asset.byte_count for asset in assets),
        aggregate_sha256=_aggregate(assets),
        assets=assets,
        case_pairs=pairs,
    )


def _collect_assets(
    root: Path, cases: tuple[CalibrationSuccessorV5FinalReplayCase, ...]
) -> tuple[CalibrationSuccessorV5FinalManifestAsset, ...]:
    family_by_case = {
        case.runtime_input.case_id: case.runtime_input.scenario_family_id for case in cases
    }
    assets = []
    for case_id in _CASE_IDS:
        for kind, relative in (
            ("runtime_input", f"final_evaluation/inputs/cases/{case_id}.json"),
            ("expected_outcome", f"final_evaluation/expected_outcomes/cases/{case_id}.json"),
        ):
            raw = (root / relative).read_bytes()
            assets.append(
                CalibrationSuccessorV5FinalManifestAsset(
                    relative_path=relative,
                    case_id=case_id,
                    asset_kind=kind,
                    scenario_family_id=family_by_case[case_id],
                    sha256=hashlib.sha256(raw).hexdigest(),
                    byte_count=len(raw),
                )
            )
    return tuple(sorted(assets, key=lambda asset: asset.relative_path))


def _aggregate(assets: tuple[CalibrationSuccessorV5FinalManifestAsset, ...]) -> str:
    return hashlib.sha256(
        _canonical([asset.model_dump(mode="json") for asset in assets])
    ).hexdigest()


def _canonical(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
