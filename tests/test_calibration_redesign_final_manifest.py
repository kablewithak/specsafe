"""Regression tests for the quarantined final-evaluation manifest boundary."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces import (
    CalibrationRedesignFinalManifestLoadError,
    CalibrationRedesignFinalManifestViolationCode,
    LogitTemperatureScalingFitError,
    LogitTemperatureScalingViolationCode,
    build_calibration_redesign_final_evaluation_manifest,
    fit_logit_temperature_scaling,
    load_calibration_redesign_final_evaluation_manifested_fixture_set,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign"
)
FINAL_CASE_IDS = frozenset({"CRV1-009", "CRV1-010", "CRV1-011", "CRV1-012"})
FINAL_FAMILY_IDS = frozenset(
    {"CRV1-FINAL-MIXED-RELIABILITY", "CRV1-FINAL-ABRUPT-SUFFIX"}
)


def _copied_fixture_root(tmp_path: Path) -> Path:
    """Copy governed assets so final-manifest tests never mutate repository fixture bytes."""

    copied_root = tmp_path / "synthetic_calibration_redesign"
    shutil.copytree(FIXTURE_ROOT, copied_root)
    return copied_root


def test_final_manifest_builder_and_loader_verify_all_quarantined_cases(
    tmp_path: Path,
) -> None:
    fixture_root = _copied_fixture_root(tmp_path)

    manifest_path = build_calibration_redesign_final_evaluation_manifest(fixture_root)
    fixture_set = load_calibration_redesign_final_evaluation_manifested_fixture_set(
        fixture_root
    )

    assert manifest_path.name == "final_evaluation_manifest.json"
    assert fixture_set.manifest.case_count == 4
    assert {case.runtime_input.case_id for case in fixture_set.cases} == FINAL_CASE_IDS
    assert {
        case.runtime_input.scenario_family_id for case in fixture_set.cases
    } == FINAL_FAMILY_IDS
    assert all(
        entry.is_final_evaluation_quarantined for entry in fixture_set.manifest.entries
    )


def test_final_manifest_loader_rejects_tampered_case_bytes(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    build_calibration_redesign_final_evaluation_manifest(fixture_root)
    tampered_path = (
        fixture_root / "inputs" / "cases" / "CRV1-011-final-abrupt-suffix-code.json"
    )
    tampered_path.write_bytes(tampered_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignFinalManifestLoadError) as error:
        load_calibration_redesign_final_evaluation_manifested_fixture_set(fixture_root)

    assert (
        error.value.code
        is CalibrationRedesignFinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_final_manifest_loader_rejects_tampered_aggregate_hash(tmp_path: Path) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    manifest_path = build_calibration_redesign_final_evaluation_manifest(fixture_root)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["aggregate_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignFinalManifestLoadError) as error:
        load_calibration_redesign_final_evaluation_manifested_fixture_set(fixture_root)

    assert (
        error.value.code
        is CalibrationRedesignFinalManifestViolationCode.MANIFEST_INTEGRITY_MISMATCH
    )


def test_final_manifest_builder_rejects_missing_final_runtime_outcome_pair(
    tmp_path: Path,
) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    (
        fixture_root
        / "expected_outcomes"
        / "CRV1-012-final-abrupt-suffix-open-ended-chat.json"
    ).unlink()

    with pytest.raises(CalibrationRedesignFinalManifestLoadError) as error:
        build_calibration_redesign_final_evaluation_manifest(fixture_root)

    assert (
        error.value.code
        is CalibrationRedesignFinalManifestViolationCode.MANIFEST_PROVENANCE_MISMATCH
    )


def test_temperature_fitter_rejects_final_manifested_fixture_set(
    tmp_path: Path,
) -> None:
    fixture_root = _copied_fixture_root(tmp_path)
    build_calibration_redesign_final_evaluation_manifest(fixture_root)
    final_fixture_set = (
        load_calibration_redesign_final_evaluation_manifested_fixture_set(fixture_root)
    )

    with pytest.raises(LogitTemperatureScalingFitError) as error:
        fit_logit_temperature_scaling(final_fixture_set)  # type: ignore[arg-type]

    assert (
        error.value.code is LogitTemperatureScalingViolationCode.UNTRUSTED_FIXTURE_SET
    )
