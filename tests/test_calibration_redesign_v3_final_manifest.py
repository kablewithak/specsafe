from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v3_final_manifest import (
    CalibrationRedesignV3FinalManifestLoadError,
    CalibrationRedesignV3FinalManifestViolationCode,
    build_calibration_redesign_v3_final_evaluation_manifest,
    load_calibration_redesign_v3_final_evaluation_manifested_fixture_set,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"


def _copy_project_root(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT, project_root)
    return (
        project_root,
        project_root / "data" / "fixtures" / "synthetic_calibration_redesign_v3",
    )


def test_v3_final_manifest_verifies_complete_frozen_held_out_corpus() -> None:
    fixture_set = load_calibration_redesign_v3_final_evaluation_manifested_fixture_set(FIXTURE_ROOT)

    assert fixture_set.manifest.case_count == 24
    assert fixture_set.manifest.observation_count == 96
    assert fixture_set.manifest.candidate_positions_per_case == 4
    assert len(fixture_set.manifest.entries) == 48
    assert len(fixture_set.cases) == 24
    assert {
        item.scenario_family_id: item.case_count
        for item in fixture_set.manifest.scenario_family_counts
    } == {
        "CRV3-FINAL-LIGHT-CAPACITY": 6,
        "CRV3-FINAL-MODERATE-CAPACITY": 6,
        "CRV3-FINAL-SATURATED-CAPACITY": 6,
        "CRV3-FINAL-JAGGED-CAPACITY": 6,
    }


def test_v3_final_manifest_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    _, fixture_root = _copy_project_root(tmp_path)
    manifest_path = fixture_root / "final_evaluation_manifest.json"
    before = manifest_path.read_bytes()

    build_calibration_redesign_v3_final_evaluation_manifest(fixture_root)

    assert manifest_path.read_bytes() == before


def test_v3_final_manifest_rejects_tampered_runtime_case_bytes(tmp_path: Path) -> None:
    _, fixture_root = _copy_project_root(tmp_path)
    runtime_path = fixture_root / "final_evaluation" / "inputs" / "cases" / "CRV3-201.json"
    runtime_path.write_bytes(runtime_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignV3FinalManifestLoadError) as error_info:
        load_calibration_redesign_v3_final_evaluation_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_v3_final_manifest_rejects_changed_final_evidence_index_bytes(tmp_path: Path) -> None:
    _, fixture_root = _copy_project_root(tmp_path)
    index_path = fixture_root / "final_evidence_index.json"
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["next_authorized_artifact"] = "tampered"
    index_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3FinalManifestLoadError) as error_info:
        load_calibration_redesign_v3_final_evaluation_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_v3_final_manifest_rejects_tampered_aggregate_hash(tmp_path: Path) -> None:
    _, fixture_root = _copy_project_root(tmp_path)
    manifest_path = fixture_root / "final_evaluation_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["aggregate_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3FinalManifestLoadError) as error_info:
        load_calibration_redesign_v3_final_evaluation_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )
