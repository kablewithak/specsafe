"""Tests for the V4 curve-coverage authoring boundary."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4RegistryLoadError,
    CalibrationRedesignV4RegistryViolationCode,
    CalibrationRedesignV4ScenarioFamilyRegistry,
    assert_calibration_redesign_v4_calibration_curve_coverage_fixture_root,
    load_calibration_redesign_v4_scenario_family_registry,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_REGISTRY_PATH = _FIXTURE_ROOT / "scenario_family_registry.json"


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_v4_curve_coverage_registry_only_through_active_boundary() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(
        _REGISTRY_PATH,
        allow_calibration_curve_coverage_assets=True,
    )

    assert registry.registry_status == "calibration_curve_coverage_authored"
    assert registry.v4_runtime_or_outcome_assets_authored is True
    assert registry.v4_manifests_authored is False
    assert (
        registry.next_authorized_artifact == "v4-calibration-position-spread-fixtures"
    )
    curve_family = next(
        family
        for family in registry.families
        if family.scenario_family_id == "CRV4-CAL-CURVE-COVERAGE"
    )
    assert curve_family.authoring_status == "calibration_curve_coverage_authored"


def test_current_root_rejects_schema_only_loader_path() -> None:
    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        load_calibration_redesign_v4_scenario_family_registry(_REGISTRY_PATH)

    assert (
        error.value.code
        is CalibrationRedesignV4RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION
    )


def test_curve_coverage_boundary_requires_exact_case_pair_inventory(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "inputs" / "cases" / "CRV4-112.json").unlink()

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_calibration_curve_coverage_fixture_root(root)

    assert (
        error.value.code
        is CalibrationRedesignV4RegistryViolationCode.CALIBRATION_CURVE_COVERAGE_BOUNDARY_VIOLATION
    )


def test_curve_coverage_boundary_rejects_final_or_adversarial_paths(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "final_evaluation").mkdir()

    with pytest.raises(CalibrationRedesignV4RegistryLoadError) as error:
        assert_calibration_redesign_v4_calibration_curve_coverage_fixture_root(root)

    assert (
        error.value.code
        is CalibrationRedesignV4RegistryViolationCode.CALIBRATION_CURVE_COVERAGE_BOUNDARY_VIOLATION
    )


def test_registry_retains_exact_split_counts_and_final_quarantine() -> None:
    registry = load_calibration_redesign_v4_scenario_family_registry(
        _REGISTRY_PATH,
        allow_calibration_curve_coverage_assets=True,
    )

    split_counts: dict[str, int] = {}
    for family in registry.families:
        split_counts[family.split.value] = split_counts.get(
            family.split.value, 0
        ) + len(family.reserved_case_ids)

    assert split_counts == {
        "calibration": 48,
        "final_evaluation": 36,
        "adversarial_regression": 12,
    }
    final_families = [
        family
        for family in registry.families
        if family.split.value == "final_evaluation"
    ]
    assert all(family.is_final_evaluation_quarantined for family in final_families)
    assert all(family.workload_allocation is not None for family in final_families)


def test_registry_rejects_unauthorised_second_calibration_family() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["families"][1]["authoring_status"] = "calibration_curve_coverage_authored"

    with pytest.raises(ValidationError, match="authoring status"):
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)


def test_registry_rejects_false_claim_that_manifests_exist() -> None:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["v4_manifests_authored"] = True

    with pytest.raises(ValidationError):
        CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
