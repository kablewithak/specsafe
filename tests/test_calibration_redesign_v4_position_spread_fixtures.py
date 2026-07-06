"""Tests for the V4 calibration position-spread fixture family."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from specsafe.traces.calibration_redesign_v4_cases import (
    load_calibration_redesign_v4_replay_case,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_POSITION_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(113, 125))


def test_position_spread_fixture_inventory_is_exact_and_physically_separated() -> None:
    expected_names = {f"{case_id}.json" for case_id in _POSITION_CASE_IDS}
    input_names = {
        path.name
        for path in (_FIXTURE_ROOT / "inputs" / "cases").iterdir()
        if path.name.startswith("CRV4-1")
    }
    outcome_names = {
        path.name
        for path in (_FIXTURE_ROOT / "expected_outcomes" / "cases").iterdir()
        if path.name.startswith("CRV4-1")
    }

    assert {f"CRV4-{number:03d}.json" for number in range(113, 125)}.issubset(
        input_names
    )
    assert {f"CRV4-{number:03d}.json" for number in range(113, 125)}.issubset(
        outcome_names
    )
    assert expected_names.issubset(input_names)
    assert expected_names.issubset(outcome_names)


def test_position_spread_cases_cover_every_position_and_workload_equally() -> None:
    replay_cases = tuple(
        load_calibration_redesign_v4_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _POSITION_CASE_IDS
    )

    positions = Counter(
        context.block_position_index
        for replay_case in replay_cases
        for context in replay_case.runtime_input.contexts
    )
    workloads = Counter(
        replay_case.runtime_input.contexts[0].workload_type.value
        for replay_case in replay_cases
    )

    assert positions == Counter({1: 12, 2: 12, 3: 12, 4: 12})
    assert workloads == Counter(
        {
            "structured_text": 4,
            "code": 4,
            "open_ended_chat": 4,
        }
    )


def test_position_spread_confidence_drops_across_each_case_without_outcome_leakage() -> (
    None
):
    for case_id in _POSITION_CASE_IDS:
        runtime_path = _FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json"
        payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        confidences = [
            context["conditional_survival_confidence"]
            for context in payload["contexts"]
        ]

        assert payload["scenario_family_id"] == "CRV4-CAL-POSITION-SPREAD"
        assert confidences == sorted(confidences, reverse=True)

        rendered = json.dumps(payload, sort_keys=True)
        assert "candidate_token_id" not in rendered
        assert "observed_acceptance" not in rendered
        assert "prefix_survival_label" not in rendered
