"""Tests for immutable V4 calibration-manifest verification after fit diagnostics."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v4_manifest import (
    CalibrationRedesignV4ManifestError,
    CalibrationRedesignV4ManifestViolationCode,
    build_calibration_redesign_v4_calibration_manifest,
    load_calibration_redesign_v4_calibration_manifest,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(101, 149))


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_manifest_hash_verifies_exact_complete_calibration_inventory() -> None:
    manifest = load_calibration_redesign_v4_calibration_manifest(_FIXTURE_ROOT)

    assert manifest.case_ids == _CASE_IDS
    assert manifest.case_pair_count == 48
    assert manifest.asset_count == 96
    assert manifest.observation_count == 192
    assert len(manifest.assets) == 96
    assert len(manifest.case_pairs) == 48
    assert manifest.aggregate_byte_count == sum(
        asset.byte_count for asset in manifest.assets
    )
    assert manifest.assets[0].relative_path == "expected_outcomes/cases/CRV4-101.json"
    assert manifest.assets[-1].relative_path == "inputs/cases/CRV4-148.json"


def test_manifest_carry_forward_hashes_bind_fit_stage_to_original_freeze() -> None:
    manifest = load_calibration_redesign_v4_calibration_manifest(_FIXTURE_ROOT)
    registry_payload = json.loads(
        (_FIXTURE_ROOT / "scenario_family_registry.json").read_text(encoding="utf-8")
    )

    assert registry_payload["frozen_calibration_registry_sha256"] == manifest.registry_sha256
    assert registry_payload["frozen_calibration_manifest_sha256"] == hashlib.sha256(
        (_FIXTURE_ROOT / "calibration_manifest.json").read_bytes()
    ).hexdigest()


def test_manifest_detects_one_byte_asset_change(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    runtime_path = root / "inputs" / "cases" / "CRV4-148.json"
    runtime_path.write_bytes(runtime_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignV4ManifestError) as error:
        load_calibration_redesign_v4_calibration_manifest(root)

    expected_code = CalibrationRedesignV4ManifestViolationCode.ASSET_INTEGRITY_MISMATCH
    assert error.value.code is expected_code


def test_manifest_detects_changed_frozen_registry_carry_forward_hash(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    registry_path = root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["frozen_calibration_registry_sha256"] = "0" * 64
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV4ManifestError) as error:
        load_calibration_redesign_v4_calibration_manifest(root)

    expected_code = CalibrationRedesignV4ManifestViolationCode.REGISTRY_PROVENANCE_MISMATCH
    assert error.value.code is expected_code


def test_build_refuses_to_rebuild_existing_manifest(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)

    with pytest.raises(CalibrationRedesignV4ManifestError) as error:
        build_calibration_redesign_v4_calibration_manifest(root)

    expected_code = CalibrationRedesignV4ManifestViolationCode.DESTINATION_ALREADY_EXISTS
    assert error.value.code is expected_code
