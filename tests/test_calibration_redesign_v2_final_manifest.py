"""V2 final-evaluation manifest integrity tests.

These tests freeze and verify held-out evidence only. They do not load the bounded-Platt
artifact, transform final confidences, calculate held-out metrics, or make a promotion decision.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.contracts.models import TraceDataRole, TraceSplit
from specsafe.traces.calibration_redesign_v2_final_manifest import (
    CalibrationRedesignV2FinalManifestLoadError,
    CalibrationRedesignV2FinalManifestViolationCode,
    build_calibration_redesign_v2_final_evaluation_manifest,
    load_calibration_redesign_v2_final_evaluation_manifested_fixture_set,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"
EXPECTED_CASE_IDS = {f"CRV2-{case_number}" for case_number in range(201, 210)}
EXPECTED_FAMILY_IDS = {
    "CRV2-FINAL-DISTRIBUTION-SHIFT",
    "CRV2-FINAL-LOCAL-DISAGREEMENT",
    "CRV2-FINAL-ORDER-PERTURBATION",
}


def _fixture_root_copy(tmp_path: Path) -> Path:
    root = tmp_path / "synthetic_calibration_redesign_v2"
    shutil.copytree(V2_FIXTURE_ROOT, root)
    return root


def test_final_manifest_verifies_complete_committed_held_out_corpus(tmp_path: Path) -> None:
    """Freeze exactly the nine reserved final cases without assessing their outcomes."""

    fixture_root = _fixture_root_copy(tmp_path)
    manifest_path = build_calibration_redesign_v2_final_evaluation_manifest(fixture_root)
    fixture_set = load_calibration_redesign_v2_final_evaluation_manifested_fixture_set(fixture_root)

    assert manifest_path.name == "final_evaluation_manifest.json"
    assert fixture_set.manifest.case_count == 9
    assert fixture_set.manifest.observation_count == 36
    assert fixture_set.manifest.minimum_required_observation_count == 36
    assert len(fixture_set.cases) == 9
    assert {case.runtime_input.case_id for case in fixture_set.cases} == EXPECTED_CASE_IDS
    assert {
        case.runtime_input.scenario_family_id for case in fixture_set.cases
    } == EXPECTED_FAMILY_IDS
    assert {case.runtime_input.split for case in fixture_set.cases} == {TraceSplit.FINAL_EVALUATION}
    assert {case.runtime_input.data_role for case in fixture_set.cases} == {
        TraceDataRole.HELD_OUT_EVALUATION
    }


def test_final_manifest_loader_rejects_tampered_final_case_bytes(tmp_path: Path) -> None:
    """Detect any byte-level change to one final runtime asset after freezing."""

    fixture_root = _fixture_root_copy(tmp_path)
    build_calibration_redesign_v2_final_evaluation_manifest(fixture_root)
    tampered_path = fixture_root / "inputs" / "cases" / "CRV2-207.json"
    tampered_path.write_bytes(tampered_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignV2FinalManifestLoadError) as error_info:
        load_calibration_redesign_v2_final_evaluation_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_final_manifest_loader_rejects_tampered_aggregate_hash(tmp_path: Path) -> None:
    """Reject a manifest whose declared aggregate no longer matches its own inventory."""

    fixture_root = _fixture_root_copy(tmp_path)
    manifest_path = build_calibration_redesign_v2_final_evaluation_manifest(fixture_root)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["aggregate_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV2FinalManifestLoadError) as error_info:
        load_calibration_redesign_v2_final_evaluation_manifested_fixture_set(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_final_manifest_builder_rejects_missing_final_case_pair(tmp_path: Path) -> None:
    """Require every reserved final case to retain both runtime and outcome assets."""

    fixture_root = _fixture_root_copy(tmp_path)
    (fixture_root / "expected_outcomes" / "cases" / "CRV2-209.json").unlink()

    with pytest.raises(CalibrationRedesignV2FinalManifestLoadError) as error_info:
        build_calibration_redesign_v2_final_evaluation_manifest(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2FinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH
    )


def test_final_manifest_builder_does_not_read_calibration_case_bytes(tmp_path: Path) -> None:
    """A malformed calibration asset must not affect held-out manifest construction."""

    fixture_root = _fixture_root_copy(tmp_path)
    calibration_path = fixture_root / "inputs" / "cases" / "CRV2-101.json"
    calibration_path.write_text("not JSON\n", encoding="utf-8")

    manifest_path = build_calibration_redesign_v2_final_evaluation_manifest(fixture_root)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["case_count"] == 9
    assert all(entry["case_id"].startswith("CRV2-2") for entry in payload["entries"])
