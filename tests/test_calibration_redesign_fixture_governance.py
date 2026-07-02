"""Regression tests for fresh calibration scenario-family governance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.traces import (
    CalibrationRedesignFixtureLoadError,
    CalibrationRedesignFixtureViolationCode,
    ScenarioFamilyRegistry,
    load_calibration_redesign_scenario_family_registry,
)

REGISTRY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign"
    / "scenario_family_registry.json"
)


def _registry_payload() -> dict[str, object]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_loads_with_required_family_and_case_counts() -> None:
    registry = load_calibration_redesign_scenario_family_registry(REGISTRY_PATH)

    assert registry.fixture_set_id == "synthetic-calibration-redesign-v1"
    assert registry.excluded_historical_case_ids == ("STF-004",)
    assert len(registry.families) == 6
    assert sum(len(family.case_ids) for family in registry.families) == 12


def test_registry_rejects_duplicate_case_id_across_splits() -> None:
    payload = _registry_payload()
    families = payload["families"]
    assert isinstance(families, list)
    families[4]["case_ids"][0] = "CRV1-001"

    with pytest.raises(ValidationError, match="case IDs must not repeat"):
        ScenarioFamilyRegistry.model_validate(payload)


def test_registry_rejects_template_reuse_between_calibration_and_final_evaluation() -> None:
    payload = _registry_payload()
    families = payload["families"]
    assert isinstance(families, list)
    families[4]["source_template_fingerprint"] = families[0]["source_template_fingerprint"]

    with pytest.raises(ValidationError, match="source_template_fingerprint must not repeat"):
        ScenarioFamilyRegistry.model_validate(payload)


def test_registry_rejects_historical_heldout_case_reuse() -> None:
    payload = _registry_payload()
    families = payload["families"]
    assert isinstance(families, list)
    families[0]["case_ids"][0] = "STF-004"

    with pytest.raises(ValidationError, match="historical excluded case IDs"):
        ScenarioFamilyRegistry.model_validate(payload)


def test_registry_rejects_cross_split_parent_lineage() -> None:
    payload = _registry_payload()
    families = payload["families"]
    assert isinstance(families, list)
    families[4]["parent_scenario_family_id"] = "CRV1-CAL-BROAD-RANGE"

    with pytest.raises(
        ValidationError, match="parent scenario family must remain in the same split"
    ):
        ScenarioFamilyRegistry.model_validate(payload)


def test_loader_returns_typed_error_for_historical_heldout_reuse(tmp_path: Path) -> None:
    payload = _registry_payload()
    families = payload["families"]
    assert isinstance(families, list)
    families[0]["case_ids"][0] = "STF-004"
    invalid_registry_path = tmp_path / "invalid-registry.json"
    invalid_registry_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CalibrationRedesignFixtureLoadError) as error:
        load_calibration_redesign_scenario_family_registry(invalid_registry_path)

    assert error.value.code is CalibrationRedesignFixtureViolationCode.HISTORICAL_HELDOUT_REUSE
