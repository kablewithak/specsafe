"""Regression tests for the V2 proposal-only registry and fixture-asset boundary."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.contracts.models import TraceDataRole, TraceSplit
from specsafe.traces.calibration_redesign_v2 import (
    CalibrationRedesignV2ProposalLoadError,
    CalibrationRedesignV2ProposalViolationCode,
    assert_calibration_redesign_v2_proposal_only_fixture_root,
    load_calibration_redesign_v2_scenario_family_registry_proposal,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_FIXTURE_ROOT = (
    PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"
)
PROPOSAL_PATH = V2_FIXTURE_ROOT / "scenario_family_registry_proposal.json"


def _proposal_payload() -> dict[str, object]:
    return json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))


def _write_proposal(root: Path, payload: dict[str, object]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    proposal_path = root / "scenario_family_registry_proposal.json"
    proposal_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return proposal_path


def _proposal_root_copy(tmp_path: Path) -> Path:
    root = tmp_path / "synthetic_calibration_redesign_v2"
    shutil.copytree(V2_FIXTURE_ROOT, root)
    return root


def test_v2_registry_proposal_loads_with_declared_floors_and_quarantine() -> None:
    proposal = load_calibration_redesign_v2_scenario_family_registry_proposal(
        PROPOSAL_PATH
    )
    families_by_split = {
        split: tuple(family for family in proposal.families if family.split is split)
        for split in TraceSplit
    }

    assert proposal.fixture_set_id == "synthetic-calibration-redesign-v2"
    assert proposal.v1_data_bearing_evidence_used is False
    assert proposal.v2_runtime_or_outcome_assets_authored is False
    assert len(families_by_split[TraceSplit.CALIBRATION]) == 3
    assert len(families_by_split[TraceSplit.FINAL_EVALUATION]) == 3
    assert all(
        family.primary_data_role is TraceDataRole.CALIBRATION
        for family in families_by_split[TraceSplit.CALIBRATION]
    )
    assert all(
        family.is_final_evaluation_quarantined is True
        for family in families_by_split[TraceSplit.FINAL_EVALUATION]
    )
    assert (
        sum(
            len(family.reserved_case_ids)
            for family in families_by_split[TraceSplit.CALIBRATION]
        )
        == 12
    )
    assert (
        sum(
            len(family.reserved_case_ids)
            for family in families_by_split[TraceSplit.FINAL_EVALUATION]
        )
        == 9
    )


def test_v2_proposal_root_allows_only_planning_assets() -> None:
    assert_calibration_redesign_v2_proposal_only_fixture_root(V2_FIXTURE_ROOT)


def test_v2_proposal_root_rejects_runtime_or_outcome_asset_paths(
    tmp_path: Path,
) -> None:
    root = _proposal_root_copy(tmp_path)
    forbidden_runtime_asset = root / "inputs" / "cases" / "CRV2-101.json"
    forbidden_runtime_asset.parent.mkdir(parents=True)
    forbidden_runtime_asset.write_text("{}\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV2ProposalLoadError) as error_info:
        assert_calibration_redesign_v2_proposal_only_fixture_root(root)

    assert (
        error_info.value.code
        is CalibrationRedesignV2ProposalViolationCode.PROPOSAL_ONLY_BOUNDARY_VIOLATION
    )


def test_v2_proposal_loader_rejects_v1_case_reference(tmp_path: Path) -> None:
    payload = _proposal_payload()
    families = payload["families"]
    assert isinstance(families, list)
    first_family = families[0]
    assert isinstance(first_family, dict)
    reserved_case_ids = first_family["reserved_case_ids"]
    assert isinstance(reserved_case_ids, list)
    reserved_case_ids[0] = "CRV1-001"
    proposal_path = _write_proposal(tmp_path, payload)

    with pytest.raises(CalibrationRedesignV2ProposalLoadError) as error_info:
        load_calibration_redesign_v2_scenario_family_registry_proposal(proposal_path)

    assert (
        error_info.value.code
        is CalibrationRedesignV2ProposalViolationCode.V1_EVIDENCE_REFERENCE
    )


def test_v2_proposal_loader_rejects_reused_calibration_final_fingerprint(
    tmp_path: Path,
) -> None:
    payload = _proposal_payload()
    families = payload["families"]
    assert isinstance(families, list)
    calibration_family = families[1]
    final_family = families[4]
    assert isinstance(calibration_family, dict)
    assert isinstance(final_family, dict)
    final_family["source_template_fingerprint"] = calibration_family[
        "source_template_fingerprint"
    ]
    proposal_path = _write_proposal(tmp_path, payload)

    with pytest.raises(CalibrationRedesignV2ProposalLoadError) as error_info:
        load_calibration_redesign_v2_scenario_family_registry_proposal(proposal_path)

    assert (
        error_info.value.code
        is CalibrationRedesignV2ProposalViolationCode.PROPOSAL_SCHEMA_ERROR
    )


def test_v2_proposal_loader_rejects_unquarantined_final_family(tmp_path: Path) -> None:
    payload = _proposal_payload()
    families = payload["families"]
    assert isinstance(families, list)
    final_family = families[4]
    assert isinstance(final_family, dict)
    final_family["is_final_evaluation_quarantined"] = False
    proposal_path = _write_proposal(tmp_path, payload)

    with pytest.raises(CalibrationRedesignV2ProposalLoadError) as error_info:
        load_calibration_redesign_v2_scenario_family_registry_proposal(proposal_path)

    assert (
        error_info.value.code
        is CalibrationRedesignV2ProposalViolationCode.PROPOSAL_SCHEMA_ERROR
    )


def test_v2_proposal_loader_rejects_insufficient_observation_budget(
    tmp_path: Path,
) -> None:
    payload = _proposal_payload()
    observation_budget = payload["observation_budget"]
    assert isinstance(observation_budget, dict)
    observation_budget["minimum_calibration_observation_count"] = 49
    proposal_path = _write_proposal(tmp_path, payload)

    with pytest.raises(CalibrationRedesignV2ProposalLoadError) as error_info:
        load_calibration_redesign_v2_scenario_family_registry_proposal(proposal_path)

    assert (
        error_info.value.code
        is CalibrationRedesignV2ProposalViolationCode.PROPOSAL_SCHEMA_ERROR
    )
