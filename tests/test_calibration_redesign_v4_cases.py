"""Tests for V4 completed calibration case-pair contracts and loader behavior."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v4_cases import (
    CalibrationRedesignV4CaseContractError,
    CalibrationRedesignV4CaseViolationCode,
    load_calibration_redesign_v4_replay_case,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_redesign_v4"
)
_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(101, 149))
_AUTHORISED_FAMILIES = {
    "CRV4-CAL-CURVE-COVERAGE",
    "CRV4-CAL-POSITION-SPREAD",
    "CRV4-CAL-WORKLOAD-MIX",
    "CRV4-CAL-CAPACITY-CONTRAST",
}


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_redesign_v4"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_all_authorised_v4_calibration_case_pairs() -> None:
    replay_cases = tuple(
        load_calibration_redesign_v4_replay_case(_FIXTURE_ROOT, case_id) for case_id in _CASE_IDS
    )

    assert tuple(case.runtime_input.case_id for case in replay_cases) == _CASE_IDS
    assert all(len(case.runtime_input.contexts) == 4 for case in replay_cases)
    assert all(len(case.expected_outcomes.outcomes) == 4 for case in replay_cases)
    assert {case.runtime_input.scenario_family_id for case in replay_cases} == _AUTHORISED_FAMILIES


def test_runtime_assets_contain_decision_time_inputs_but_no_outcome_fields() -> None:
    runtime_path = _FIXTURE_ROOT / "inputs" / "cases" / "CRV4-144.json"
    runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))

    serialized_runtime = json.dumps(runtime_payload, sort_keys=True)
    assert "observed_acceptance" not in serialized_runtime
    assert "prefix_survival_label" not in serialized_runtime
    assert "candidate_token_id" not in serialized_runtime
    assert runtime_payload["contexts"][0]["visible_prefix_token_ids"] == []
    assert runtime_payload["contexts"][3]["visible_prefix_token_ids"]


def test_loader_rejects_misaligned_runtime_and_outcome_pair(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    outcome_path = root / "expected_outcomes" / "cases" / "CRV4-137.json"
    payload = json.loads(outcome_path.read_text(encoding="utf-8"))
    payload["fixture_id"] = "misaligned-fixture-id"
    outcome_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationRedesignV4CaseContractError) as error:
        load_calibration_redesign_v4_replay_case(root, "CRV4-137")

    assert error.value.code is CalibrationRedesignV4CaseViolationCode.CASE_ALIGNMENT_ERROR


def test_loader_rejects_missing_case_asset_after_boundary_validation(
    tmp_path: Path,
) -> None:
    root = _copy_fixture_root(tmp_path)
    (root / "expected_outcomes" / "cases" / "CRV4-148.json").unlink()

    with pytest.raises(CalibrationRedesignV4CaseContractError) as error:
        load_calibration_redesign_v4_replay_case(root, "CRV4-101")

    assert error.value.code is CalibrationRedesignV4CaseViolationCode.CASE_ASSET_LAYOUT_ERROR
