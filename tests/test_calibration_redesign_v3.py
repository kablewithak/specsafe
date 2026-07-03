from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v3 import (
    CalibrationRedesignV3RegistryLoadError,
    CalibrationRedesignV3RegistryViolationCode,
    assert_calibration_redesign_v3_schema_only_fixture_root,
    load_calibration_redesign_v3_scenario_family_registry,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
)


def _copy_schema_only_root(tmp_path: Path) -> Path:
    destination = tmp_path / "synthetic_calibration_redesign_v3"
    destination.mkdir()
    for filename in (
        "scenario_family_registry.json",
        "PROPOSAL_MANIFEST.md",
        "authoring_ledger.md",
    ):
        (destination / filename).write_bytes((FIXTURE_ROOT / filename).read_bytes())
    return destination


def test_v3_registry_loads_at_schema_only_boundary() -> None:
    registry = load_calibration_redesign_v3_scenario_family_registry(
        FIXTURE_ROOT / "scenario_family_registry.json"
    )

    assert registry.fixture_set_id == "synthetic-calibration-redesign-v3"
    assert registry.v1_or_v2_data_bearing_evidence_used is False
    assert registry.v3_runtime_or_outcome_assets_authored is False
    assert registry.v3_manifests_authored is False
    assert registry.observation_budget.calibration_observation_count == 144
    assert registry.observation_budget.final_evaluation_observation_count == 96
    assert registry.observation_budget.adversarial_regression_observation_count == 32


def test_v3_registry_reserves_exact_split_and_capacity_family_shape() -> None:
    registry = load_calibration_redesign_v3_scenario_family_registry(
        FIXTURE_ROOT / "scenario_family_registry.json"
    )

    case_count_by_split = {
        split.value: sum(
            len(family.reserved_case_ids)
            for family in registry.families
            if family.split.value == split.value
        )
        for split in {family.split for family in registry.families}
    }
    final_families = [
        family for family in registry.families if family.is_final_evaluation_quarantined
    ]

    assert case_count_by_split == {
        "calibration": 36,
        "final_evaluation": 24,
        "adversarial_regression": 8,
    }
    assert {family.scenario_family_id for family in final_families} == {
        "CRV3-FINAL-LIGHT-CAPACITY",
        "CRV3-FINAL-MODERATE-CAPACITY",
        "CRV3-FINAL-SATURATED-CAPACITY",
        "CRV3-FINAL-JAGGED-CAPACITY",
    }
    assert all(len(family.reserved_case_ids) == 6 for family in final_families)
    assert all(family.workload_allocation is not None for family in final_families)


def test_v3_schema_only_root_rejects_case_directories(tmp_path: Path) -> None:
    fixture_root = _copy_schema_only_root(tmp_path)
    (fixture_root / "inputs").mkdir()

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        assert_calibration_redesign_v3_schema_only_fixture_root(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION
    )


def test_v3_schema_only_root_rejects_unapproved_manifest(tmp_path: Path) -> None:
    fixture_root = _copy_schema_only_root(tmp_path)
    (fixture_root / "calibration_manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        assert_calibration_redesign_v3_schema_only_fixture_root(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION
    )


def test_v3_registry_rejects_closed_v2_reference(tmp_path: Path) -> None:
    fixture_root = _copy_schema_only_root(tmp_path)
    registry_path = fixture_root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["explicit_exclusions"].append("CRV2-201 must not be read")
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        load_calibration_redesign_v3_scenario_family_registry(registry_path)

    assert (
        error_info.value.code
        is CalibrationRedesignV3RegistryViolationCode.V1_OR_V2_EVIDENCE_REFERENCE
    )


def test_v3_registry_rejects_changed_reserved_case_budget(tmp_path: Path) -> None:
    fixture_root = _copy_schema_only_root(tmp_path)
    registry_path = fixture_root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["families"][0]["reserved_case_ids"] = payload["families"][0]["reserved_case_ids"][:-1]
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV3RegistryLoadError) as error_info:
        load_calibration_redesign_v3_scenario_family_registry(registry_path)

    assert error_info.value.code is CalibrationRedesignV3RegistryViolationCode.REGISTRY_SCHEMA_ERROR
