from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v3_manifest import (
    CalibrationRedesignV3CalibrationManifestLoadError,
    CalibrationRedesignV3CalibrationManifestViolationCode,
    build_calibration_redesign_v3_calibration_manifest,
    load_calibration_redesign_v3_calibration_manifested_fixture_set,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"


def _copy_fixture_root(tmp_path: Path) -> Path:
    destination = tmp_path / "synthetic_calibration_redesign_v3"
    shutil.copytree(FIXTURE_ROOT, destination)
    return destination


def test_v3_calibration_manifest_verifies_complete_frozen_corpus() -> None:
    fixture_set = load_calibration_redesign_v3_calibration_manifested_fixture_set(FIXTURE_ROOT)

    assert fixture_set.manifest.case_count == 36
    assert fixture_set.manifest.observation_count == 144
    assert fixture_set.manifest.calibration_quantile_group_count == 8
    assert len(fixture_set.manifest.entries) == 72
    assert len(fixture_set.cases) == 36
    assert {
        item.scenario_family_id: item.case_count
        for item in fixture_set.manifest.scenario_family_counts
    } == {
        "CRV3-CAL-CURVE-COVERAGE": 12,
        "CRV3-CAL-POSITION-SPREAD": 12,
        "CRV3-CAL-WORKLOAD-MIX": 12,
    }


def test_v3_calibration_manifest_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    fixture_root = _copy_fixture_root(tmp_path)
    manifest_path = fixture_root / "calibration_manifest.json"
    before = manifest_path.read_bytes()

    build_calibration_redesign_v3_calibration_manifest(fixture_root)

    assert manifest_path.read_bytes() == before


def test_v3_calibration_manifest_rejects_tampered_runtime_case_bytes(tmp_path: Path) -> None:
    fixture_root = _copy_fixture_root(tmp_path)
    runtime_path = fixture_root / "inputs" / "cases" / "CRV3-101.json"
    payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    payload["generation_note"] = "tampered after manifest freeze"
    runtime_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3CalibrationManifestLoadError) as error_info:
        load_calibration_redesign_v3_calibration_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_v3_calibration_manifest_rejects_tampered_aggregate_hash(tmp_path: Path) -> None:
    fixture_root = _copy_fixture_root(tmp_path)
    manifest_path = fixture_root / "calibration_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["aggregate_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3CalibrationManifestLoadError) as error_info:
        load_calibration_redesign_v3_calibration_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3CalibrationManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_v3_calibration_manifest_rejects_early_final_evaluation_asset(tmp_path: Path) -> None:
    fixture_root = _copy_fixture_root(tmp_path)
    source = fixture_root / "expected_outcomes" / "cases" / "CRV3-125.json"
    (fixture_root / "expected_outcomes" / "cases" / "CRV3-201.json").write_bytes(
        source.read_bytes()
    )

    with pytest.raises(CalibrationRedesignV3CalibrationManifestLoadError) as error_info:
        load_calibration_redesign_v3_calibration_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3CalibrationManifestViolationCode.CALIBRATION_BOUNDARY_VIOLATION
    )
