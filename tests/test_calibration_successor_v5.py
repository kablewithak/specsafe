"""Tests for the V5 frozen calibration-manifest evidence boundary."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.traces.calibration_successor_v5 import (
    CalibrationSuccessorV5RegistryLoadError,
    CalibrationSuccessorV5ScenarioFamilyRegistry,
    assert_calibration_successor_v5_calibration_fit_diagnostics_fixture_root,
    load_calibration_successor_v5_scenario_family_registry,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"
_REGISTRY_PATH = _FIXTURE_ROOT / "scenario_family_registry.json"


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_the_v5_registry_only_through_fit_diagnostics_boundary() -> None:
    registry = load_calibration_successor_v5_scenario_family_registry(
        _REGISTRY_PATH,
        allow_calibration_fit_diagnostics_assets=True,
    )

    assert registry.registry_status == "calibration_fit_diagnostics_retained"
    assert registry.v5_runtime_or_outcome_assets_authored is True
    assert registry.v5_calibration_manifest_authored is True
    assert registry.frozen_calibration_manifest_sha256 is not None
    assert registry.frozen_calibration_pre_freeze_registry_sha256 is not None
    assert registry.v5_calibration_artifact_authored is True
    assert registry.v5_calibration_fit_diagnostics_authored is True
    assert registry.frozen_calibration_artifact_sha256 is not None
    assert registry.frozen_calibration_fit_diagnostics_sha256 is not None
    assert registry.v5_final_evaluation_runtime_or_outcome_assets_authored is False
    assert registry.next_authorized_artifact == "v5-final-evaluation-fixture-authoring"


def test_active_root_rejects_obsolete_mixed_reliability_loader_path() -> None:
    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        load_calibration_successor_v5_scenario_family_registry(
            _REGISTRY_PATH,
            allow_calibration_mixed_reliability_contrast_assets=True,
        )

    assert error.value.code.value == (
        "calibration_successor_v5_calibration_mixed_reliability_contrast_boundary_violation"
    )


def test_fit_diagnostics_root_requires_exactly_forty_eight_case_pairs(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "inputs" / "cases" / "CSV5-148.json").unlink()

    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        assert_calibration_successor_v5_calibration_fit_diagnostics_fixture_root(root)

    assert error.value.code.value == (
        "calibration_successor_v5_calibration_fit_diagnostics_boundary_violation"
    )


def test_fit_diagnostics_root_rejects_final_evaluation_path(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "final_evaluation").mkdir()

    with pytest.raises(CalibrationSuccessorV5RegistryLoadError) as error:
        assert_calibration_successor_v5_calibration_fit_diagnostics_fixture_root(root)

    assert error.value.code.value == (
        "calibration_successor_v5_calibration_fit_diagnostics_boundary_violation"
    )


def test_registry_rejects_frozen_status_without_manifest_provenance() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["frozen_calibration_manifest_sha256"] = None

    with pytest.raises(ValidationError):
        CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(payload)


def test_registry_retains_final_and_adversarial_reservations_as_quarantined() -> None:
    registry = load_calibration_successor_v5_scenario_family_registry(
        _REGISTRY_PATH,
        allow_calibration_fit_diagnostics_assets=True,
    )
    final_families = [
        family for family in registry.families if family.split.value == "final_evaluation"
    ]
    adversarial_families = [
        family for family in registry.families if family.split.value == "adversarial_regression"
    ]

    assert all(
        family.authoring_status == "reserved_for_v5_case_authoring" for family in final_families
    )
    assert all(family.is_final_evaluation_quarantined for family in final_families)
    assert all(
        family.authoring_status == "reserved_for_v5_case_authoring"
        for family in adversarial_families
    )
    assert all(family.is_adversarial_regression_quarantined for family in adversarial_families)
