"""Contract and loader tests for V5 calibration case pairs through V5-3c."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_successor_v5_cases import (
    CalibrationSuccessorV5CaseContractError,
    CalibrationSuccessorV5CaseViolationCode,
    load_calibration_successor_v5_curve_coverage_replay_case,
    load_calibration_successor_v5_position_spread_replay_case,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"
_CURVE_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(101, 113))
_POSITION_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(113, 125))


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_loads_all_authorised_v5_curve_and_position_case_pairs() -> None:
    curve_cases = tuple(
        load_calibration_successor_v5_curve_coverage_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _CURVE_CASE_IDS
    )
    position_cases = tuple(
        load_calibration_successor_v5_position_spread_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _POSITION_CASE_IDS
    )

    replay_cases = (*curve_cases, *position_cases)
    assert tuple(case.runtime_input.case_id for case in curve_cases) == _CURVE_CASE_IDS
    assert tuple(case.runtime_input.case_id for case in position_cases) == _POSITION_CASE_IDS
    assert all(len(case.runtime_input.contexts) == 4 for case in replay_cases)
    assert all(len(case.expected_outcomes.outcomes) == 4 for case in replay_cases)
    assert {case.runtime_input.scenario_family_id for case in curve_cases} == {
        "CSV5-CAL-CURVE-COVERAGE"
    }
    assert {case.runtime_input.scenario_family_id for case in position_cases} == {
        "CSV5-CAL-POSITION-SPREAD"
    }


def test_runtime_assets_exclude_evaluation_only_outcome_fields() -> None:
    runtime_payload = json.loads(
        (_FIXTURE_ROOT / "inputs" / "cases" / "CSV5-119.json").read_text(
            encoding="utf-8"
        )
    )
    serialized_runtime = json.dumps(runtime_payload, sort_keys=True)

    assert "observed_acceptance" not in serialized_runtime
    assert "prefix_survival_label" not in serialized_runtime
    assert "candidate_token_id" not in serialized_runtime
    assert runtime_payload["contexts"][0]["visible_prefix_token_ids"] == []
    assert runtime_payload["contexts"][3]["visible_prefix_token_ids"]


def test_position_loader_rejects_a_misaligned_runtime_and_outcome_pair(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    outcome_path = root / "expected_outcomes" / "cases" / "CSV5-119.json"
    payload = json.loads(outcome_path.read_text(encoding="utf-8"))
    payload["fixture_id"] = "misaligned-v5-fixture"
    outcome_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationSuccessorV5CaseContractError) as error:
        load_calibration_successor_v5_position_spread_replay_case(root, "CSV5-119")

    assert error.value.code is CalibrationSuccessorV5CaseViolationCode.CASE_ALIGNMENT_ERROR


def test_loaders_reject_case_ids_outside_their_active_family_boundaries() -> None:
    with pytest.raises(CalibrationSuccessorV5CaseContractError) as curve_error:
        load_calibration_successor_v5_curve_coverage_replay_case(_FIXTURE_ROOT, "CSV5-113")
    with pytest.raises(CalibrationSuccessorV5CaseContractError) as position_error:
        load_calibration_successor_v5_position_spread_replay_case(_FIXTURE_ROOT, "CSV5-125")

    assert curve_error.value.code is CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR
    assert (
        position_error.value.code
        is CalibrationSuccessorV5CaseViolationCode.CASE_ASSET_LAYOUT_ERROR
    )
