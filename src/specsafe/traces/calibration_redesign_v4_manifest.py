"""Immutable V4 calibration-manifest generation and verification.

The manifest hashes exactly the 48 calibration-only runtime/outcome case pairs. It is a
provenance and tamper-detection boundary. It is not a calibration artifact, fitter,
final-evaluation manifest, scheduler, baseline, or replay scorer.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from specsafe.contracts.models import StrictContract
from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4RegistryLoadError,
    CalibrationRedesignV4ScenarioFamilyRegistry,
    assert_calibration_redesign_v4_calibration_capacity_contrast_fixture_root,
    load_calibration_redesign_v4_scenario_family_registry,
)

_MANIFEST_FILENAME = "calibration_manifest.json"
_MANIFEST_SCHEMA_VERSION = "calibration-redesign-v4-manifest-v1"
_MANIFEST_ID = "v4-calibration-manifest-freeze"
_FIXTURE_SET_ID = "synthetic-calibration-redesign-v4"
_FIXTURE_SET_VERSION = "1.0.0"
_METHOD_CONSTITUTION_VERSION = "v4-method-and-evidence-constitution-v1"
_CALIBRATION_METHOD_ID = "regularized-isotonic-calibration-v4"
_EXPECTED_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(101, 149))
_EXPECTED_CASE_COUNT = 48
_EXPECTED_ASSET_COUNT = 96
_EXPECTED_OBSERVATION_COUNT = 192


class CalibrationRedesignV4ManifestViolationCode(StrEnum):
    """Machine-readable reasons a calibration manifest is not trustworthy."""

    DESTINATION_ALREADY_EXISTS = "calibration_redesign_v4_manifest_destination_exists"
    DESTINATION_WRITE_ERROR = "calibration_redesign_v4_manifest_destination_write_error"
    MANIFEST_READ_ERROR = "calibration_redesign_v4_manifest_read_error"
    MANIFEST_SCHEMA_ERROR = "calibration_redesign_v4_manifest_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = (
        "calibration_redesign_v4_manifest_registry_provenance_mismatch"
    )
    INVENTORY_MISMATCH = "calibration_redesign_v4_manifest_inventory_mismatch"
    ASSET_INTEGRITY_MISMATCH = (
        "calibration_redesign_v4_manifest_asset_integrity_mismatch"
    )
    AGGREGATE_MISMATCH = "calibration_redesign_v4_manifest_aggregate_mismatch"
    PRE_FREEZE_ROOT_INVALID = "calibration_redesign_v4_manifest_pre_freeze_root_invalid"


class CalibrationRedesignV4ManifestError(ValueError):
    """Raised when a manifest cannot be created or verified safely."""

    def __init__(
        self,
        code: CalibrationRedesignV4ManifestViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationRedesignV4ManifestAsset(StrictContract):
    """One immutable file record within the calibration-only evidence corpus."""

    relative_path: str = Field(
        pattern=(r"^(inputs|expected_outcomes)/cases/CRV4-[0-9]{3}\.json$")
    )
    case_id: str = Field(pattern=r"^CRV4-[0-9]{3}$")
    asset_kind: Literal["runtime_input", "expected_outcome"]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_path_and_kind(self) -> CalibrationRedesignV4ManifestAsset:
        expected_parent = (
            "inputs/cases"
            if self.asset_kind == "runtime_input"
            else "expected_outcomes/cases"
        )
        expected_path = f"{expected_parent}/{self.case_id}.json"
        if self.relative_path != expected_path:
            raise ValueError(
                "V4 calibration manifest asset path must match its declared case and kind"
            )
        return self


class CalibrationRedesignV4ManifestCasePair(StrictContract):
    """The two separately stored evidence halves for one calibration replay case."""

    case_id: str = Field(pattern=r"^CRV4-[0-9]{3}$")
    runtime_input_relative_path: str = Field(
        pattern=r"^inputs/cases/CRV4-[0-9]{3}\.json$"
    )
    expected_outcome_relative_path: str = Field(
        pattern=r"^expected_outcomes/cases/CRV4-[0-9]{3}\.json$"
    )
    runtime_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_outcome_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_case_pair_paths(self) -> CalibrationRedesignV4ManifestCasePair:
        if self.runtime_input_relative_path != f"inputs/cases/{self.case_id}.json":
            raise ValueError("V4 runtime-input pair path does not match its case ID")
        if self.expected_outcome_relative_path != (
            f"expected_outcomes/cases/{self.case_id}.json"
        ):
            raise ValueError("V4 expected-outcome pair path does not match its case ID")
        return self


class CalibrationRedesignV4CalibrationManifest(StrictContract):
    """Frozen, deterministic provenance for the complete V4 calibration corpus."""

    schema_version: Literal["calibration-redesign-v4-manifest-v1"] = (
        _MANIFEST_SCHEMA_VERSION
    )
    manifest_id: Literal["v4-calibration-manifest-freeze"] = _MANIFEST_ID
    manifest_scope: Literal["calibration_only"] = "calibration_only"
    fixture_set_id: Literal["synthetic-calibration-redesign-v4"] = _FIXTURE_SET_ID
    fixture_set_version: Literal["1.0.0"] = _FIXTURE_SET_VERSION
    method_constitution_version: Literal["v4-method-and-evidence-constitution-v1"] = (
        _METHOD_CONSTITUTION_VERSION
    )
    calibration_method_id: Literal["regularized-isotonic-calibration-v4"] = (
        _CALIBRATION_METHOD_ID
    )
    registry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_ids: tuple[str, ...] = Field(min_length=_EXPECTED_CASE_COUNT)
    case_pair_count: Literal[48] = _EXPECTED_CASE_COUNT
    asset_count: Literal[96] = _EXPECTED_ASSET_COUNT
    observation_count: Literal[192] = _EXPECTED_OBSERVATION_COUNT
    aggregate_byte_count: int = Field(ge=1)
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    assets: tuple[CalibrationRedesignV4ManifestAsset, ...] = Field(
        min_length=_EXPECTED_ASSET_COUNT,
        max_length=_EXPECTED_ASSET_COUNT,
    )
    case_pairs: tuple[CalibrationRedesignV4ManifestCasePair, ...] = Field(
        min_length=_EXPECTED_CASE_COUNT,
        max_length=_EXPECTED_CASE_COUNT,
    )

    @model_validator(mode="after")
    def validate_manifest_shape(self) -> CalibrationRedesignV4CalibrationManifest:
        if self.case_ids != _EXPECTED_CASE_IDS:
            raise ValueError(
                "V4 calibration manifest case IDs must be CRV4-101 through CRV4-148"
            )
        if len(set(self.case_ids)) != _EXPECTED_CASE_COUNT:
            raise ValueError("V4 calibration manifest case IDs must be unique")
        if len(self.assets) != self.asset_count:
            raise ValueError("V4 calibration manifest asset_count must match assets")
        if len(self.case_pairs) != self.case_pair_count:
            raise ValueError(
                "V4 calibration manifest case_pair_count must match case_pairs"
            )

        expected_paths = tuple(
            sorted(
                (
                    *(f"inputs/cases/{case_id}.json" for case_id in _EXPECTED_CASE_IDS),
                    *(
                        f"expected_outcomes/cases/{case_id}.json"
                        for case_id in _EXPECTED_CASE_IDS
                    ),
                )
            )
        )
        actual_paths = tuple(asset.relative_path for asset in self.assets)
        if actual_paths != expected_paths:
            raise ValueError(
                "V4 calibration manifest assets must be complete and sorted by relative path"
            )
        expected_pair_ids = _EXPECTED_CASE_IDS
        actual_pair_ids = tuple(pair.case_id for pair in self.case_pairs)
        if actual_pair_ids != expected_pair_ids:
            raise ValueError(
                "V4 calibration manifest case pairs must be complete and sorted by case ID"
            )
        if self.aggregate_byte_count != sum(asset.byte_count for asset in self.assets):
            raise ValueError(
                "V4 calibration manifest aggregate_byte_count must match asset records"
            )
        return self


def build_calibration_redesign_v4_calibration_manifest(
    root: Path,
) -> CalibrationRedesignV4CalibrationManifest:
    """Build a deterministic manifest only from the complete pre-freeze asset root."""

    resolved_root = root.resolve()
    destination = resolved_root / _MANIFEST_FILENAME
    if destination.exists():
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.DESTINATION_ALREADY_EXISTS,
            "V4 calibration manifest already exists and must not be rebuilt in place",
        )
    try:
        assert_calibration_redesign_v4_calibration_capacity_contrast_fixture_root(
            resolved_root
        )
        registry = load_calibration_redesign_v4_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_calibration_capacity_contrast_assets=True,
        )
    except CalibrationRedesignV4RegistryLoadError as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V4 calibration manifest requires a complete pre-freeze root: {error}",
        ) from error

    return _build_manifest_from_root(resolved_root, registry)


def write_calibration_redesign_v4_calibration_manifest(
    root: Path,
) -> CalibrationRedesignV4CalibrationManifest:
    """Write one immutable calibration manifest with exclusive create semantics."""

    resolved_root = root.resolve()
    manifest = build_calibration_redesign_v4_calibration_manifest(resolved_root)
    destination = resolved_root / _MANIFEST_FILENAME
    payload = _manifest_file_bytes(manifest)
    try:
        with destination.open("xb") as file_handle:
            file_handle.write(payload)
    except FileExistsError as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.DESTINATION_ALREADY_EXISTS,
            "V4 calibration manifest already exists and must not be overwritten",
        ) from error
    except OSError as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.DESTINATION_WRITE_ERROR,
            f"unable to write V4 calibration manifest: {error}",
        ) from error
    return manifest


def load_calibration_redesign_v4_calibration_manifest(
    root: Path,
) -> CalibrationRedesignV4CalibrationManifest:
    """Load and hash-verify the immutable calibration manifest and every asset it names."""

    resolved_root = root.resolve()
    try:
        registry = load_calibration_redesign_v4_scenario_family_registry(
            resolved_root / "scenario_family_registry.json",
            allow_final_evaluation_fixture_assets=True,
        )
    except CalibrationRedesignV4RegistryLoadError as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.PRE_FREEZE_ROOT_INVALID,
            f"V4 calibration manifest root is not authorised: {error}",
        ) from error

    manifest_path = resolved_root / _MANIFEST_FILENAME
    try:
        raw_bytes = manifest_path.read_bytes()
        payload = json.loads(raw_bytes.decode("utf-8"))
    except OSError as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.MANIFEST_READ_ERROR,
            f"unable to read V4 calibration manifest: {error}",
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V4 calibration manifest is not valid UTF-8 JSON: {error}",
        ) from error
    try:
        manifest = CalibrationRedesignV4CalibrationManifest.model_validate(payload)
    except ValidationError as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.MANIFEST_SCHEMA_ERROR,
            f"V4 calibration manifest validation failed: {error}",
        ) from error

    _verify_manifest_against_root(resolved_root, manifest, registry)
    return manifest


def _build_manifest_from_root(
    root: Path,
    registry: CalibrationRedesignV4ScenarioFamilyRegistry,
) -> CalibrationRedesignV4CalibrationManifest:
    registry_sha256 = _sha256(root / "scenario_family_registry.json")
    assets = _collect_asset_records(root)
    assets_by_path = {asset.relative_path: asset for asset in assets}
    case_pairs = tuple(
        CalibrationRedesignV4ManifestCasePair(
            case_id=case_id,
            runtime_input_relative_path=f"inputs/cases/{case_id}.json",
            expected_outcome_relative_path=(f"expected_outcomes/cases/{case_id}.json"),
            runtime_input_sha256=assets_by_path[f"inputs/cases/{case_id}.json"].sha256,
            expected_outcome_sha256=assets_by_path[
                f"expected_outcomes/cases/{case_id}.json"
            ].sha256,
        )
        for case_id in _EXPECTED_CASE_IDS
    )
    aggregate_bytes = sum(asset.byte_count for asset in assets)
    return CalibrationRedesignV4CalibrationManifest(
        registry_sha256=registry_sha256,
        case_ids=_EXPECTED_CASE_IDS,
        aggregate_byte_count=aggregate_bytes,
        aggregate_sha256=_aggregate_sha256(assets),
        assets=assets,
        case_pairs=case_pairs,
    )


def _verify_manifest_against_root(
    root: Path,
    manifest: CalibrationRedesignV4CalibrationManifest,
    registry: CalibrationRedesignV4ScenarioFamilyRegistry,
) -> None:
    if registry.frozen_calibration_registry_sha256 != manifest.registry_sha256:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 active registry does not carry forward the frozen registry SHA-256",
        )
    actual_manifest_sha256 = _sha256(root / _MANIFEST_FILENAME)
    if registry.frozen_calibration_manifest_sha256 != actual_manifest_sha256:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V4 active registry does not carry forward the immutable manifest SHA-256",
        )

    actual_assets = _collect_asset_records(root)
    if manifest.assets != actual_assets:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.ASSET_INTEGRITY_MISMATCH,
            "V4 calibration manifest asset hashes or byte counts do not match the fixture root",
        )
    if manifest.aggregate_byte_count != sum(
        asset.byte_count for asset in actual_assets
    ):
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.INVENTORY_MISMATCH,
            "V4 calibration manifest aggregate byte count does not match the fixture root",
        )
    actual_aggregate_sha256 = _aggregate_sha256(actual_assets)
    if manifest.aggregate_sha256 != actual_aggregate_sha256:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.AGGREGATE_MISMATCH,
            "V4 calibration manifest aggregate SHA-256 does not match the fixture root",
        )

    expected_case_pairs = _build_expected_case_pairs(actual_assets)
    if manifest.case_pairs != expected_case_pairs:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.INVENTORY_MISMATCH,
            "V4 calibration manifest case-pair inventory does not match the fixture root",
        )


def _collect_asset_records(
    root: Path,
) -> tuple[CalibrationRedesignV4ManifestAsset, ...]:
    asset_records = []
    for case_id in _EXPECTED_CASE_IDS:
        asset_records.append(
            _asset_record(
                root,
                relative_path=f"inputs/cases/{case_id}.json",
                case_id=case_id,
                asset_kind="runtime_input",
            )
        )
        asset_records.append(
            _asset_record(
                root,
                relative_path=f"expected_outcomes/cases/{case_id}.json",
                case_id=case_id,
                asset_kind="expected_outcome",
            )
        )
    return tuple(sorted(asset_records, key=lambda asset: asset.relative_path))


def _asset_record(
    root: Path,
    *,
    relative_path: str,
    case_id: str,
    asset_kind: Literal["runtime_input", "expected_outcome"],
) -> CalibrationRedesignV4ManifestAsset:
    path = root / relative_path
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.INVENTORY_MISMATCH,
            f"unable to read V4 calibration asset {relative_path}: {error}",
        ) from error
    return CalibrationRedesignV4ManifestAsset(
        relative_path=relative_path,
        case_id=case_id,
        asset_kind=asset_kind,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        byte_count=len(raw_bytes),
    )


def _build_expected_case_pairs(
    assets: tuple[CalibrationRedesignV4ManifestAsset, ...],
) -> tuple[CalibrationRedesignV4ManifestCasePair, ...]:
    assets_by_path = {asset.relative_path: asset for asset in assets}
    return tuple(
        CalibrationRedesignV4ManifestCasePair(
            case_id=case_id,
            runtime_input_relative_path=f"inputs/cases/{case_id}.json",
            expected_outcome_relative_path=(f"expected_outcomes/cases/{case_id}.json"),
            runtime_input_sha256=assets_by_path[f"inputs/cases/{case_id}.json"].sha256,
            expected_outcome_sha256=assets_by_path[
                f"expected_outcomes/cases/{case_id}.json"
            ].sha256,
        )
        for case_id in _EXPECTED_CASE_IDS
    )


def _aggregate_sha256(
    assets: tuple[CalibrationRedesignV4ManifestAsset, ...],
) -> str:
    payload = [asset.model_dump(mode="json") for asset in assets]
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _sha256(path: Path) -> str:
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise CalibrationRedesignV4ManifestError(
            CalibrationRedesignV4ManifestViolationCode.MANIFEST_READ_ERROR,
            f"unable to read V4 manifest provenance input {path.name}: {error}",
        ) from error
    return hashlib.sha256(raw_bytes).hexdigest()


def _manifest_file_bytes(manifest: CalibrationRedesignV4CalibrationManifest) -> bytes:
    return (
        json.dumps(
            manifest.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
