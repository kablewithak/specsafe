"""Regression tests for V4 frozen final-evaluation fixture access."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v4_final_cases import (
    CalibrationRedesignV4FinalCaseContractError,
    CalibrationRedesignV4FinalCaseViolationCode,
    load_calibration_redesign_v4_final_replay_case,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_FINAL_ROOT = _FIXTURE_ROOT / "final_evaluation"
_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(201, 237))
_EXPECTED_FAMILY_BY_CASE_ID = {
    **{f"CRV4-{number:03d}": "CRV4-FINAL-LIGHT-CAPACITY" for number in range(201, 210)},
    **{
        f"CRV4-{number:03d}": "CRV4-FINAL-MODERATE-CAPACITY"
        for number in range(210, 219)
    },
    **{
        f"CRV4-{number:03d}": "CRV4-FINAL-SATURATED-CAPACITY"
        for number in range(219, 228)
    },
    **{
        f"CRV4-{number:03d}": "CRV4-FINAL-JAGGED-CAPACITY" for number in range(228, 237)
    },
}


def test_final_inventory_is_complete_and_separate_from_calibration_assets() -> None:
    expected_names = {f"{case_id}.json" for case_id in _CASE_IDS}
    input_names = {path.name for path in (_FINAL_ROOT / "inputs" / "cases").iterdir()}
    outcome_names = {
        path.name for path in (_FINAL_ROOT / "expected_outcomes" / "cases").iterdir()
    }

    assert input_names == expected_names
    assert outcome_names == expected_names
    assert (_FIXTURE_ROOT / "final_evaluation_manifest.json").is_file()
    assert (_FIXTURE_ROOT / "final_evidence_index.json").is_file()
    assert not (_FIXTURE_ROOT / "heldout_assessment.json").exists()
    assert not (_FIXTURE_ROOT / "adversarial_regression").exists()


def test_final_cases_cover_each_capacity_family_workload_and_position() -> None:
    replay_cases = tuple(
        load_calibration_redesign_v4_final_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _CASE_IDS
    )

    family_counts = Counter(
        replay_case.runtime_input.scenario_family_id for replay_case in replay_cases
    )
    workload_counts_by_family: dict[str, Counter[str]] = {}
    position_counts = Counter(
        context.block_position_index
        for replay_case in replay_cases
        for context in replay_case.runtime_input.contexts
    )
    profile_case_counts = Counter(
        replay_case.runtime_input.contexts[0].capacity_snapshot.profile_id
        for replay_case in replay_cases
    )

    for replay_case in replay_cases:
        family_id = replay_case.runtime_input.scenario_family_id
        workload_counts_by_family.setdefault(family_id, Counter())[
            replay_case.runtime_input.contexts[0].workload_type.value
        ] += 1

    assert family_counts == Counter(
        {
            "CRV4-FINAL-LIGHT-CAPACITY": 9,
            "CRV4-FINAL-MODERATE-CAPACITY": 9,
            "CRV4-FINAL-SATURATED-CAPACITY": 9,
            "CRV4-FINAL-JAGGED-CAPACITY": 9,
        }
    )
    assert all(
        workload_counts
        == Counter({"structured_text": 3, "code": 3, "open_ended_chat": 3})
        for workload_counts in workload_counts_by_family.values()
    )
    assert position_counts == Counter({1: 36, 2: 36, 3: 36, 4: 36})
    assert profile_case_counts == Counter(
        {
            "v4-final-capacity-light": 9,
            "v4-final-capacity-moderate": 9,
            "v4-final-capacity-saturated": 9,
            "v4-final-capacity-jagged": 9,
        }
    )


def test_final_runtime_assets_are_label_free_and_outcomes_remain_separate() -> None:
    observed_acceptance = []
    for case_id in _CASE_IDS:
        runtime_payload = json.loads(
            (_FINAL_ROOT / "inputs" / "cases" / f"{case_id}.json").read_text(
                encoding="utf-8"
            )
        )
        outcome_payload = json.loads(
            (_FINAL_ROOT / "expected_outcomes" / "cases" / f"{case_id}.json").read_text(
                encoding="utf-8"
            )
        )
        rendered_runtime = json.dumps(runtime_payload, sort_keys=True)

        assert runtime_payload["case_id"] == case_id
        assert (
            runtime_payload["scenario_family_id"]
            == _EXPECTED_FAMILY_BY_CASE_ID[case_id]
        )
        assert runtime_payload["split"] == "final_evaluation"
        assert runtime_payload["data_role"] == "held_out_evaluation"
        assert "candidate_token_id" not in rendered_runtime
        assert "observed_acceptance" not in rendered_runtime
        assert "prefix_survival_label" not in rendered_runtime
        assert runtime_payload["trace_id"] == outcome_payload["trace_id"]
        observed_acceptance.extend(
            item["observed_acceptance"] for item in outcome_payload["outcomes"]
        )

    assert any(observed_acceptance)
    assert not all(observed_acceptance)


def test_final_loader_rejects_calibration_or_unreserved_case_ids() -> None:
    with pytest.raises(CalibrationRedesignV4FinalCaseContractError) as error:
        load_calibration_redesign_v4_final_replay_case(_FIXTURE_ROOT, "CRV4-148")

    expected_code = CalibrationRedesignV4FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR
    assert error.value.code is expected_code
