"""Regression tests for immutable fresh calibration fixture manifest behavior."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces import (
    CalibrationRedesignManifestLoadError,
    CalibrationRedesignManifestViolationCode,
    build_calibration_redesign_manifest,
    load_calibration_redesign_manifested_fixture_set,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign"
)


def _copied_fixture_root(tmp_path: Path) -> Path:
    """Copy governed assets so manifest tests never mutate repository fixture bytes."""

    copied_root = tmp_path / "synthetic_calibration_redesign"
    shutil.copytree(FIXTURE_ROOT, copied_root)
    return copied_root


def test_manifest_builder_and_loader_verify_all_six_calibration_cases(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)

    manifest_path = build_calibration_redesign_manifest(fixture_root)
    fixture_set = load_calibration_redesign_manifested_fixture_set(fixture_root)

    assert manifest_path.name == "manifest.json"
    assert fixture_set.manifest.case_count == 6
    assert len(fixture_set.cases) == 6
    assert {case.runtime_input.scenario_family_id for case in fixture_set.cases} == {
        "CRV1-CAL-BROAD-RANGE",
        "CRV1-CAL-POSITIONAL-DECAY",
    }


def test_manifest_loader_rejects_tampered_case_bytes(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    build_calibration_redesign_manifest(fixture_root)
    tampered_path = (
        fixture_root
        / "inputs"
        / "cases"
        / "CRV1-001-calibration-broad-range-low.json"
    )
    tampered_path.write_bytes(tampered_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignManifestLoadError) as error:
        load_calibration_redesign_manifested_fixture_set(fixture_root)

    assert error.value.code is CalibrationRedesignManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH


def test_manifest_loader_rejects_tampered_aggregate_hash(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    manifest_path = build_calibration_redesign_manifest(fixture_root)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["aggregate_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignManifestLoadError) as error:
        load_calibration_redesign_manifested_fixture_set(fixture_root)

    assert error.value.code is CalibrationRedesignManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH


def test_manifest_builder_rejects_missing_runtime_outcome_pair(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    (
        fixture_root
        / "expected_outcomes"
        / "CRV1-006-calibration-positional-decay-open-ended-chat.json"
    ).unlink()

    with pytest.raises(CalibrationRedesignManifestLoadError) as error:
        build_calibration_redesign_manifest(fixture_root)

    assert error.value.code is CalibrationRedesignManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH


def test_manifest_builder_excludes_quarantined_final_evaluation_cases(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)

    manifest_path = build_calibration_redesign_manifest(fixture_root)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["case_count"] == 6
    assert {entry["case_id"] for entry in payload["entries"]} == {
        "CRV1-001",
        "CRV1-002",
        "CRV1-003",
        "CRV1-004",
        "CRV1-005",
        "CRV1-006",
    }
    assert {entry["split"] for entry in payload["entries"]} == {"calibration"}
    assert {entry["data_role"] for entry in payload["entries"]} == {"calibration"}
    assert {"CRV1-009", "CRV1-010"}.isdisjoint(
        {entry["case_id"] for entry in payload["entries"]}
    )
